# Order flow & market microstructure: must-knows

Local copy of Sharif's doc **"Order Flow & Market Microstructure: Institutional Reading List"**
(private doc, rev 11, 2026-11-13). Sections 1–9 below keep
that doc's content. **§10 "What this engine can use"** is new: it maps each idea to our data and our layers.
If the doc changes, re-read it and update this file. The full texts (free papers and books) go in
`references/microstructure/` (see its README).

Institutions don't call this "order flow trading". The field is **market microstructure**, and the useful
material sits under that name. Books titled "Order Flow Trading" tend to be retail footprint-chart guides,
many of them self-published. This file covers the institutional version.

Data levels: **L1** = best bid and ask, **L2** = depth at each price, **L3** = every individual order.

---

## 1. Core measures (from the shortest horizon to the longest)

| Measure | What it tells you | Data needed | Known caveat |
| --- | --- | --- | --- |
| Book imbalance (queue imbalance) | Which side of the book is heavier; price tends to drift toward the thinner side | L1 or L2 snapshots | Static state. Easily spoofed; decays within seconds |
| Order Flow Imbalance (OFI) | Net change in supply and demand at the best quotes; explains short-horizon price changes linearly | L1 event updates | Slope is inversely proportional to depth, so it must be normalised per instrument and time of day |
| Multi-level OFI (MLOFI) | OFI across deeper levels | L2 event updates | Fit improves with each added level, but so does noise |
| Microprice | A fair-price estimate better than the mid, adjusted for imbalance and spread | L1 | Replication is mixed: one thesis found it no better than the mid at most horizons |
| Trade sign (tick rule, Lee-Ready) | Whether each trade was buyer- or seller-initiated | Trades, plus quotes for Lee-Ready | Every trade-based measure below inherits its errors |
| Signed volume / delta / CVD | Net aggressive buying | Signed trades | Retail-chart name for the same thing; only as good as the trade signs |
| Kyle's lambda | Price move per unit of signed flow; a proxy for informed trading | Signed trades and returns | Regression estimate; unstable over short windows |
| Effective and realized spread | Cost paid versus the mid, and how much of it the liquidity provider keeps | Trades and quotes | Depends on the benchmark price (mid versus microprice) |
| Roll spread | Spread implied by negative autocorrelation of price changes | Trade prices only | Undefined when the autocovariance is positive |
| Amihud illiquidity | Price move per dollar traded | Daily or bar returns and volume | Coarse; for cross-sectional liquidity, not timing |
| VPIN | Order flow toxicity on a volume clock | Trades, bucketed by volume | **Contested.** Its flash-crash signal is disputed |
| Square-root impact | How much a large order moves price | Your own executions or a model | Holds on average across metaorders, not trade by trade |
| Order-sign long memory | Buy and sell signs persist for long periods because large orders are split | Signed trades | Inflates naive t-statistics; use autocorrelation-robust errors |

## 2. Formulas

**Order Flow Imbalance** (Cont, Kukanov, Stoikov). For each L1 update n, with best bid Pᴮ, bid size qᴮ,
best ask Pᴬ and ask size qᴬ:

```latex
e_n = \mathbb{1}\{P^B_n \ge P^B_{n-1}\}\,q^B_n - \mathbb{1}\{P^B_n \le P^B_{n-1}\}\,q^B_{n-1} - \mathbb{1}\{P^A_n \le P^A_{n-1}\}\,q^A_n + \mathbb{1}\{P^A_n \ge P^A_{n-1}\}\,q^A_{n-1}
```

OFI over an interval is the sum of eₙ. The paper's model:

```latex
\Delta P_k = \beta\,\mathrm{OFI}_k + \varepsilon_k, \qquad \beta \propto \frac{1}{\text{average depth}}
```

**Book imbalance** over N levels (as in the hftbacktest tutorial):

```latex
I = \frac{\sum_{i=1}^{N} Q^{bid}_i - \sum_{i=1}^{N} Q^{ask}_i}{\sum_{i=1}^{N} Q^{bid}_i + \sum_{i=1}^{N} Q^{ask}_i}
```

**Weighted mid** and **Stoikov's microprice**, which adds a learned adjustment g that depends on imbalance I and spread S:

```latex
P_{w} = \frac{Q^{bid} P^{ask} + Q^{ask} P^{bid}}{Q^{bid} + Q^{ask}}, \qquad P_{micro} = P_{mid} + g(I, S)
```

**Kyle's lambda**: regress returns on signed volume over a window:

```latex
r_t = \lambda \sum_{j \in t} s_j v_j + \varepsilon_t, \qquad s_j \in \{+1, -1\}
```

**Effective and realized spread**, for a trade at price p with sign D and mid m:

```latex
\text{ES} = 2D(p - m_t), \qquad \text{RS} = 2D(p - m_{t+\Delta})
```

**Roll spread** and **Amihud illiquidity**:

```latex
\text{Roll} = 2\sqrt{-\operatorname{cov}(\Delta p_t, \Delta p_{t-1})}, \qquad \text{ILLIQ} = \frac{1}{T}\sum_{t=1}^{T} \frac{|r_t|}{\text{dollar volume}_t}
```

**VPIN** over n equal-volume buckets of size V:

```latex
\text{VPIN} = \frac{\sum_{\tau=1}^{n} \lvert V^{B}_{\tau} - V^{S}_{\tau} \rvert}{n V}
```

**Square-root impact** of a metaorder of size Q, with daily volatility σ, daily volume V and a constant Y near 1:

```latex
\Delta P \approx Y \, \sigma \sqrt{\frac{Q}{V}}
```

**Trade signing.** The tick rule marks a trade a buy if its price is above the previous different price.
Lee-Ready marks it a buy if above the mid and a sell if below, and falls back to the tick rule at the mid. On Nasdaq
data with true signs, Lee-Ready classified 86.9% of trades correctly with 1-second timestamps and 93.6% with
millisecond timestamps, against 78.6% for the tick rule. Where the exchange publishes the aggressor side (most
futures and crypto feeds), use it and skip classification.

## 3. Validation pitfalls (run these against any model that uses order flow)

| Check | What goes wrong | Evidence |
| --- | --- | --- |
| Fees and rebates included | Signals with real predictive power still lose money after costs. Results often depend on a maker rebate the strategy may not qualify for | hftbacktest's imbalance market maker assumes Binance's best maker rebate; per-trade returns fall sharply without it |
| Queue position and latency modelled | Assuming a limit order fills when price touches it overstates profit, especially for market making | hftbacktest results shift when its queue model parameter changes |
| Out-of-sample and out-of-regime test | A strategy tuned on one period degrades in the next | hftbacktest's BTC example: Sharpe 10.8 (May 2023) → 3.0 (May–Jul 2025), no out-of-sample split shown |
| Unseen instruments, not only a benchmark | Deep models that score well on FI-2010 drop sharply on LOBSTER data | LOBCAST benchmark of 15 models |
| Realistic expectation of fit | R² near 0.01 is normal for a useful order book feature; a high R² at a forward horizon suggests leakage | Databento's sklearn tutorial |
| Horizon matched to the decay | Order book alpha peaks around two average price changes, then decays | Kolm, Turiel, Westray |
| No look-ahead in labels or timestamps | Labels built by smoothing forward prices add ad hoc parameters; exchange vs receive time and same-timestamp events leak the future | Kolm, Turiel, Westray; general practice |
| Trade-sign accuracy checked | Toxicity measures can look predictive purely because classification errors correlate with volatility | Andersen, Bondarenko on VPIN |
| Autocorrelation-robust statistics | Order signs have long memory, so naive t-statistics overstate significance | Bouchaud, Farmer, Lillo |
| Seasonality and depth normalisation | Impact varies with depth through the day; raw OFI is not comparable across times or instruments | Cont, Kukanov, Stoikov |
| Spoofing and cancellation risk | Static book imbalance can be gamed by orders never meant to fill | General practice; prefer event-based OFI over static snapshots |
| Contested measures flagged | VPIN's creators and critics disagree on whether it works; treat it as a hypothesis | Easley, López de Prado, O'Hara vs Andersen, Bondarenko |

## 4. Open-access reading pack (free full texts, in reading order)

| # | Paper | Topic | Free full text |
| --- | --- | --- | --- |
| 1 | Gould, Porter, Williams, McDonald, Fenn, Howison: Limit Order Books (survey) | How order books work, stylised facts, where models fail | [arXiv 1012.0349](https://arxiv.org/abs/1012.0349) |
| 2 | Hasbrouck: Securities Trading, Principles and Procedures | Trading mechanisms, institutional and regulatory detail | [NYU Stern](https://pages.stern.nyu.edu/~jhasbrou/STPP/STPPindex.html) |
| 3 | Cont, Kukanov, Stoikov: The Price Impact of Order Book Events | OFI defined; linear impact; slope ∝ 1/depth | [arXiv 1011.6402](https://arxiv.org/abs/1011.6402) |
| 4 | Xu, Gould, Howison: Multi-Level Order-Flow Imbalance | OFI over deeper levels | [arXiv 1907.06230](https://arxiv.org/abs/1907.06230) |
| 5 | Stoikov: The Micro-Price | Martingale fair price from imbalance and spread | [SSRN 2970694](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2970694) |
| 6 | Avellaneda, Stoikov: High-Frequency Trading in a Limit Order Book | Reference market-making model | [NYU PDF](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf) |
| 7 | Almgren, Chriss: Optimal Execution of Portfolio Transactions | Impact cost vs risk when working a large order | [PDF (Quantitative Brokers)](https://quantitativebrokers.com/s/Optimal-Execution-of-Portfolio-Transaction-_-AlmgrenChriss-1999.pdf) |
| 8 | Bouchaud, Farmer, Lillo: How Markets Slowly Digest Changes in Supply and Demand | Order-sign long memory, metaorders, square-root impact | [arXiv 0809.0822](https://arxiv.org/abs/0809.0822) |
| 9 | Evans, Lyons: Order Flow and Exchange Rate Dynamics | Order flow explains R² > 50% of daily FX changes | [NBER w7317](https://www.nber.org/papers/w7317) |
| 10 | Easley, López de Prado, O'Hara: Flow Toxicity and Liquidity in a High-Frequency World | VPIN defined | [NYU Stern PDF](https://www.stern.nyu.edu/sites/default/files/assets/documents/con_035928.pdf) |
| 11 | Andersen, Bondarenko: VPIN and the Flash Crash | Main VPIN critique; read with #10 | [Aarhus CREATES PDF](https://repec.econ.au.dk/repec/creates/rp/11/rp11_50.pdf) |
| 12 | Easley, López de Prado, O'Hara, Zhang: Microstructure in the Machine Age | Roll, Kyle's λ, Amihud, VPIN as ML features | [NBER conference PDF](https://conference.nber.org/conf_papers/f117415.pdf) |
| 13 | Kolm, Turiel, Westray: Deep Order Flow Imbalance | Nets on OFI beat nets on raw book states; alpha horizon | [SSRN 3900141](https://ssrn.com/abstract=3900141) |
| 14 | Zhang, Zohren, Roberts: DeepLOB | CNN + LSTM on raw order books | [arXiv 1808.03668](https://arxiv.org/abs/1808.03668) |
| 15 | Prata et al.: LOBCAST benchmark | Why benchmark scores overstate performance | [arXiv 2308.01915](https://arxiv.org/abs/2308.01915) |
| 16 | How Smart is Institutional Trading? (ABFER 2017) | Hedge fund flow has larger, more persistent impact | [ABFER PDF](https://www.abfer.org/media/abfer-events-2017/annual-conference/investment-finance/ac2017p3026_how_smart_is_institutional_trading.pdf) |
| 17 | Carmona: High Frequency Markets, summer school notes | Order book mechanics and models | [Princeton PDF](https://carmona.princeton.edu/sites/g/files/toruqf5466/files/documents/HF_Summer_School_2013.pdf) |

Kyle (1985), Glosten-Milgrom (1985) and Lee-Ready (1991) are foundational but paywalled. Items 1, 2 and 12 cover
their key results. SSRN downloads may need a free account.

## 5. Data sources

Order flow models need event-level data, not bars.

| Source | Level | Cost | Good for |
| --- | --- | --- | --- |
| Binance futures via [collect-binancefutures](https://github.com/nkaz001/collect-binancefutures) | L2 depth + trades, aggressor side | Free; collect going forward | First experiments, hftbacktest tutorials |
| [Databento](https://databento.com/stocks) | L1, L2 (MBP-10), L3 (MBO); US equities and **CME futures** | Paid; $125 free credits for new accounts | Research-grade samples (NQ/ES/YM/GC/SI) |
| [LOBSTER](https://lobsterdata.com) | Nasdaq book rebuilt from TotalView-ITCH | Paid academic | The standard academic dataset |
| FI-2010 | Nasdaq Nordic, 5 stocks, 10 days | Free | Benchmarking only; too small to prove anything |
| Nasdaq sample ITCH ([parsing guide](https://cedardb.com/docs/example_datasets/nasdaq/)) | Full L3 messages, selected days | Free | Practising book reconstruction |

Record the exchange timestamp and the receive timestamp separately. The latency between the two is where most
backtests lie.

## 6. Books (reading order; paid, so for human reading)

**Foundations**
1. **Trading and Exchanges: Market Microstructure for Practitioners**, Larry Harris. How order books, market makers, informed traders and liquidity work.
2. **Trades, Quotes and Prices**, Bouchaud, Bonart, Donier, Gould. Empirical, physics-style: order books, impact, the long memory of order flow.
3. **Empirical Market Microstructure**, Joel Hasbrouck. The econometrics of price discovery, information share and trade-sign models.

**Quant and strategy side**
4. **Algorithmic and High-Frequency Trading**, Cartea, Jaimungal, Penalva. The maths of market making, optimal execution and order-flow strategies.
5. **Market Microstructure in Practice**, Lehalle and Laruelle. The buy-side and execution-desk view.
6. **Advances in Financial Machine Learning**, Marcos López de Prado. Microstructural features, including VPIN-style toxicity.

**Narrative, for context**
7. **Dark Pools** (Scott Patterson) and **Flash Boys** (Michael Lewis). Journalism: how institutional flow, HFT and venue structure interact.

## 7. Practical: reproduce the research in Python

| Resource | What you build | Data needed |
| --- | --- | --- |
| [Databento: HFT signals with sklearn](https://databento.com/blog/hft-sklearn-python) | Top-of-book skew + 10-level imbalance → 500-tick return forecast | Databento MBP-10 |
| [Databento: microprice and book imbalance](https://databento.com/docs/examples/order-book/microprice) | Microprice, N-level imbalance as fair-price estimators | Databento MBP-10 |
| [Databento: examples index](https://databento.com/docs/examples?lang=python) | Book construction from MBO, queue position, a liquidity-taking HFT strategy | Databento MBO |
| [hftbacktest: Market Making with Alpha, Order Book Imbalance](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html) ([GitHub](https://github.com/nkaz001/hftbacktest)) | Imbalance-skewed market maker with queue position and latency modelled | Full tick book + trades (free: Binance via collect-binancefutures) |
| [NautilusTrader: order book depth (Binance)](https://nautilustrader.io/docs/latest/tutorials/backtest_orderbook_binance/) | Fill-or-kill limit orders when one side is much thicker | Binance depth CSVs |
| [NautilusTrader: gold book imbalance](https://nautilustrader.io/docs/latest/tutorials/gold_book_imbalance_ax/) | Top-of-book imbalance backtest on **CME gold futures** | Databento mbp-1 (cheaper than depth) |
| [DeepLOB](https://arxiv.org/abs/1808.03668) + [implementation](https://github.com/Jeonghwan-Cheon/lob-deep-learning) | CNN + LSTM price-move model from the book | FI-2010 |
| [LOBCAST](https://arxiv.org/abs/2308.01915) | Compare 15 deep models | FI-2010 and LOBSTER |

Read the LOBCAST result before trusting any deep model: the best models score well on FI-2010 but drop sharply on
unseen LOBSTER data.

## 8. Courses and lecture notes

| Resource | Level | Access | Covers |
| --- | --- | --- | --- |
| [Hasbrouck NYU notes](https://pages.stern.nyu.edu/~jhasbrou/STPP/STPPindex.html) | Undergraduate | Free PDF | Order books, auctions, dealer markets; institutional and regulatory detail |
| [Carmona, Princeton 2013](https://carmona.princeton.edu/sites/g/files/toruqf5466/files/documents/HF_Summer_School_2013.pdf) | Graduate | Free PDF | Microstructure and book mechanics (lectures 1–5 of 10) |
| [Stevens FE570](https://fsc.stevens.edu/fe570-market-microstructure-and-trading-strategies) | Master's | Syllabus only | Roll, inventory, information-based and book models, optimal execution (study map) |
| [Oxford: Algorithmic and HF Trading](https://courses.maths.ox.ac.uk/course/info.php?id=6483) | Master's | Synopsis only (login) | Book mechanics, impact, optimal liquidation, Avellaneda-Stoikov |
| [Oxford: Market Microstructure](https://courses.maths.ox.ac.uk/course/view.php?id=4827) | Master's | Synopsis only (login) | Mathematical framework for how a book evolves |
| [Quantra: Order Book Basics](https://quantra.quantinsti.com/course/market-microstructure-order-book-basics) | Beginner | Paid; not validated | Reading a live order book |
| [Udemy: A Primer on Quant Trading](https://www.udemy.com/course/a-primer-on-quant-trading/) | Intermediate | Paid; not validated | Book statistics, Avellaneda-Stoikov, impact from trade data |

## 9. Things worth knowing

- **Real alpha here is thin and fast.** OFI signals peak at the shortest horizons and decay quickly. They are statistically real but economically thin, and are captured mostly by whoever has the best costs and queue position. Edge depends on infrastructure and fees more than on cleverness.
- **Institutions use "order flow" in different ways.** Market makers read client flow and adverse selection. Execution desks hide their own footprint. Quants model imbalance and impact. Almost none of them watch footprint charts the way retail traders do.
- **Data is the real barrier.** Research-grade work needs tick-level or L2/L3 data, which is expensive and large.

**Suggested path (from the doc):**
1. Harris for vocabulary, with Hasbrouck's NYU notes alongside.
2. Get tick data: Binance futures (free) or a small Databento MBP-10 sample.
3. Reproduce OFI (Cont, Kukanov, Stoikov) and measure how well it predicts forward returns at several horizons.
4. Run the hftbacktest imbalance tutorial: does the signal survive queue position, latency and fees?
5. Only then try DeepLOB-style models, with the LOBCAST warning in mind.

*Educational background, not trading or investment advice.*

---

## 10. What this engine can use (engine notes, not from the doc)

**Our data.** Dukascopy CFD quotes: 1m bid and ask bars (we have both, 2021-10 → 2026-11). Dukascopy tick files
also carry bid/ask prices and top-of-book sizes (**to check per asset**: the CFD liquidity provider's sizes, not an
exchange book). There are **no exchange trades**, so nothing that needs a trade sign can be built from this feed.

| Measure | With our data? | Note |
| --- | --- | --- |
| Effective / quoted spread | ✅ **built** | `ict_engine/data/spreads.py` (measured ask − bid, expected per half-hour, no look-ahead) |
| Roll spread | ✅ possible | From mid prices; a cross-check on the measured spread |
| Book imbalance (L1), microprice, OFI (L1) | ⚠️ maybe | Only if Dukascopy tick sizes are meaningful for indices and metals. Test on a few days first |
| Signed volume / delta / CVD, Kyle's λ, VPIN, trade-sign memory | ❌ | Need exchange trades with an aggressor side → CME futures (Databento: NQ, ES, YM, GC, SI) |
| L2 / MLOFI, queue position | ❌ | Need depth data (Databento MBP-10 / MBO) |
| Amihud | ❌ (tick volume only) | Coarse anyway; not a timing tool |

**Where it fits the four layers (CLAUDE.md).**
- **Concepts** (detected, not scored): spread, imbalance, OFI and delta as per-bar series, like FVGs and swings.
- **Patterns / tags**: order-flow state at a setup's decision time (e.g. OFI over the sweep candle, delta
  divergence at the swept level). These are tagged on every backtest row like `news`, then compared in the trade
  store with and without, exactly as news was.
- **Gates** (optional, off by default): e.g. "the sweep shows absorption" (heavy aggressive selling into the swept
  low with no follow-through). It becomes a default only if it beats the baseline out-of-sample.
- Never a model on its own: per §9, pure order-flow alpha lives at seconds-scale horizons and belongs to whoever
  has the best costs. Our trades last minutes to hours and pay a CFD spread. The plausible use is **confirming
  ICT's liquidity events** (sweep → reversal), not a standalone HFT signal.

**Rules this adds to our validation checklist.** Several are already ours: costs (measured spreads), out-of-sample
(pre-registration), no look-ahead (event `ts`). New ones:
- **Autocorrelation-robust standard errors** for any flow feature. Our leaderboard's `se` assumes independent trades.
- **Normalise flow by depth and time of day** before comparing across sessions or assets, the same lesson as the
  half-hour spread buckets.
- **Expect tiny fit**: R² ≈ 0.01 is normal; a large effect is a leakage alarm.
- **Treat VPIN as contested.** A hypothesis, never a default.

## 11. What the books say about our findings (2026-11-14, engine notes)
Paraphrased from the local library (`references/microstructure/`, read with the `microstructure-library` skill).
Page numbers are PDF pages.

**1. Stops add momentum. They don't hand the other side a free reversal.**
- *Harris §4.5.2 (pp.92-93):* stop orders are market orders that wake up when price is already moving. They
  ask for liquidity at the worst moment, so they speed the move up: they "add momentum".
- *Harris ch.11 §11.2 (pp.264-267):* people who trade ahead of predictable flow ("sentiment-oriented technical
  traders", "order anticipators") make money only by getting out before value traders push price back. The edge
  is in the **timing of the exit**, not in the sweep itself.
- *Our data:* after a stop-out, price reaches 3R in either direction about half the time
  (`research/direction-diagnosis-2026-11-13.md`). This fits: the sweep is a burst of liquidity demand with no
  reliable sign afterwards.

**2. Impact from a burst of orders fades, but slowly enough that price stays a random walk.**
- *Bouchaud ch.13 (propagator model), eq. 13.7–13.10, pp.270-277:*
  - The mid-price is a sum over past trades:
    m_t = m_{t0} + Σ_{n<t} G(t−n) ε_n + Σ ξ_n, where ε = ±1 is the trade sign and G(ℓ) is the propagator.
  - Trade signs have long memory: C(ℓ) ~ ℓ^(−γ), with γ < 1.
  - If G(ℓ) ~ ℓ^(−β), returns are uncorrelated (efficient) only when **β = β_c = (1−γ)/2**, the "fine
    balance" (§13.2.3, p.257 of the book, PDF p.276).
  - Read: impact is semi-permanent. It neither stays nor snaps back on a fixed clock. Liquidity providers absorb
    the predictable part of the flow.
- *For us:* a sweep-then-reverse pattern can only have an edge if it shows the fine balance being broken (a
  real imbalance, a news shock). The price pattern alone isn't evidence of that. Testing it needs signed trades,
  i.e. CME futures data (§10). Dukascopy quotes can't show it.

**3. With no forecast, no stop/target pair creates an edge.**
- *López de Prado ch.13 (optimal trading rules by synthetic data), §13.4–13.6, pp.196-221:*
  - He models a trade's P&L as an Ornstein–Uhlenbeck process:
    P_t = (1−φ)·E0[P_T] + φ·P_{t−1} + σ·ε_t, with half-life τ: φ = 2^(−1/τ).
  - He then grid-searches profit-take × stop-loss pairs.
  - With a zero forecast (E0 = 0), most pairs give a Sharpe of about zero. Only a fast-reverting process (small
    τ) rewards "small profit-take, wide stop", which is the market maker's business.
  - Stop and target settings change the *shape* of returns. They can't create a mean.
  - He also warns that calibrating them on historical paths is a classic overfitting route.
- *Our data matches:* partials (`partial_frac`/`runner_stop`), stop variants and the cost-relative-to-reward gate
  all left the gross mean at about 0, in every cost bucket. Lever = the **entry signal** (the forecast E0), not
  exits.

**4. Selection and a burned test set.**
- *López de Prado ch.11–12 (pp.178-195):* every variant you try is a trial. Hold-out results viewed more than once
  are no longer out-of-sample.
- *For us:* that's why 2024-07→2026-11-12 is burned and a clean confirmation needs forward data. Use clustered
  standard errors (`store.clustered_se`), and count trials when judging z.

**What this means for the plan**
1. Spend effort on entries that carry a forecast (the PD array return model, time-of-day / macro windows), not on
   stop or target tuning.
2. Any stop-hunt / sweep-reversal claim needs signed order flow, so log it as a futures-data item.
3. Forward-test log from 2026-11-13: frozen rules, no tuning on it.
