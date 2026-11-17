# Microstructure components — what each is, what it needs, what we can compute (2026-11-16)

One row per measure found in `references/orderflow.md` and the library in `references/microstructure/`.
Citations are `book §section, pp.PDF pages` (keys as in the `microstructure-library` skill). Formulas are paraphrased
from the sources; code and tests: `research/scripts/micro_features.py`, `tests/test_micro_features.py`.
Results of testing each computable one on our trades: `research/microstructure/2026-11-16-study.md`.

**Our data, three levels**
- **Bars** — Dukascopy CFD 1m bid + ask bars (OHLC; "volume" is the quote feed's own size number, not traded contracts). Indices from 2019-10, gold from 2021-10. All 7 datasets.
- **Trades with side** — CME NQ 2024 (every trade with its aggressor side; 1m buy/sell/delta). US100 trades in 2024-H1 only (246 trades).
- **Order book / quotes** — none. One day of NQ top-of-book (2024-03-05) exists as a side check. Not enough to test anything.

## A. Computable from bars (all 7 datasets)

| Component | Plain words | Formula | Source | Data it needs | Feature in the study | How it could matter for an ICT trade |
|---|---|---|---|---|---|---|
| Quoted spread | The cost of crossing from bid to ask right now | S = ask − bid (mean over the last 60 min) | harris ch.14, pp.310-334; bouchaud ch.16, pp.317-337 | Bid and ask quotes | `spread_rel` (÷ normal for the clock time), `spread_r` (÷ the trade's risk) | Skip when the spread is wide against the stop (cost in R); a spread wider than normal = stress |
| Roll spread | The spread implied by price "bounce": prices that flip up-down-up reveal a bid/ask being hit | 2·√max(0, −cov(Δp_t, Δp_{t−1})) | lopez §19.3.2, pp.309-310; hasbrouck ch.3, pp.34-41 | Prices only | `roll_sig` (÷ the 1m σ) | Stop placement: a stop inside the bounce is noise |
| Return autocorrelation | Is the last hour trending (> 0) or bouncing (< 0) minute to minute | corr(Δp_t, Δp_{t−1}) | bouchaud §2.1.2, pp.43-44 | Prices only | `autocorr1` | Entry timing: continuation vs fade |
| Corwin–Schultz spread | Spread from highs and lows: a high is usually at the ask, a low at the bid; volatility grows with time, the spread doesn't | β = Σ_{j=0,1} ln(H_{t−j}/L_{t−j})², γ = ln(H_{t−1,t}/L_{t−1,t})², α = (√(2β) − √β)/(3 − 2√2) − √(γ/(3 − 2√2)), S = 2(e^α − 1)/(1 + e^α), α < 0 → 0 | lopez §19.3.4, pp.311-312 | High/low bars | `cs_bp` | Same use as the spread: cost and stop noise |
| High-low (Parkinson) volatility | Volatility read from each bar's range rather than its close | σ² = mean(ln(H/L)²) / (4 ln 2) | lopez §19.3.3, pp.310-311 | High/low bars | `pk_rel` (÷ normal for the clock time) | Skip quiet markets; size the stop to volatility |
| Realized volatility | How far price has actually been moving | √Σ(Δp)² over the window; variogram V(τ) = E[(p_{t+τ} − p_t)²] | bouchaud §2.1, pp.42-46; harris ch.20, pp.423-431 | Prices | `rv_rel` (÷ normal for the clock time), `risk_sigma` (the stop ÷ the last hour's σ) | Skip quiet markets; stop in units of noise |
| Intraday seasonality | Volatility, volume and spread follow a daily pattern, so "high" must be judged against the normal for that clock time | value ÷ median of the same clock window over the previous 20 weekdays | bouchaud §4.2, pp.78-80; lehalle §2.2, pp.170-174; cartea ch.4, pp.78-115 | Bars | `tod_season` (the normal 60-min range for the clock time, in ADR); every `_rel` feature uses it | Time-of-day gate; the base for every other measure |
| Variance ratio (signature plot) | Do 5-minute moves add up to more (trend) or less (mean reversion) than 1-minute moves predict | VR(q) = Var(Δ_q p) / (q · Var(Δ_1 p)) | bouchaud §2.1.3, pp.44-46; lehalle §A.13, pp.343-344 | Prices | `vr5` (q = 5, last 120 min) | Regime: sweep-and-reverse (mean-reverting) vs run (trending) |
| Amihud illiquidity | Price move per unit of volume. Low = much volume, little movement | mean(\|Δln p_t\| / volume_t) | lopez §19.4.2, pp.315-316; orderflow.md §2 | Returns + volume | `amihud_rel`; on NQ with real volume `nq_amihud_rel` | Absorption at a zone (low Amihud into the entry); thin market = skip |
| Trade intensity / volume clock | How fast volume is arriving; the volume clock ticks once per fixed amount traded | volume in the window ÷ normal; volume bars = sample every V units | lopez §2.3.1, pp.53-55; p10-easley pp.6-10; bouchaud ch.9, pp.182-205 | Volume | `intensity_rel`; on NQ `nq_intensity_rel` | "Be in the market when it is moving": skip slow tape |
| Tick rule / signed volume proxy | Guess the aggressor from the price change: up = buy, down = sell | b_t = sign(Δp_t), unchanged → b_{t−1}; imbalance = Σ b·v / Σ v | lopez §19.3.1, p.309; orderflow.md §2 (78.6 % accuracy trade by trade) | Prices + volume | `tick_imb` (aligned with the trade, last 60 min) | A delta stand-in: flow with or against the trade |
| Kyle's λ (bar version) | Price move per unit of signed flow | Δp_t = λ·(b_t v_t) + ε; feature = t-value of λ | lopez §19.4.1, pp.313-315; bouchaud ch.15, pp.309-316 | Signed volume + returns | `kyle_t` | Thin, impact-heavy market = skip or expect slippage. **On bars the sign comes from the same price change it explains, so the fit is circular** (t between 2 and 15 on every trade) |
| Stop-run / liquidity burst | Stops are market orders that fire when price is already moving, so a run through a level shows as a burst of volume ("stops add momentum") | max 1m volume of the last 5 min ÷ median of the 60 min before | harris §4.5, pp.92-93; harris ch.11, pp.258-271 (order anticipators) | Volume | `vol_burst` | The sweep before an entry: does a volume burst mark the turn? |

## B. Needs trades with an aggressor side (NQ 2024 only → US100 trades in 2024-H1)

| Component | Plain words | Formula | Source | Feature in the study | How it could matter |
|---|---|---|---|---|---|
| Signed volume / delta / trade imbalance | Net aggressive buying over a window | I = (V_buy − V_sell)/(V_buy + V_sell); ΔV = Σ ε_n v_n | bouchaud §11.4, pp.241-242; p03-cont §4, pp.16-20 | `imb30`, `imb60`, `imb120` (aligned with the trade, over the approach) | The open idea: flow over the whole approach into the zone |
| Cumulative delta divergence | Price makes a new extreme but cumulative delta does not: the aggressors behind the move are running out | new price low in the last 15 min vs the previous 105; compare the cumulative-delta low the same way | retail name; mechanism in bouchaud §11.4 and ch.13 (impact of flow fades), pp.241-242, 268-288 | `cvd_div` (+1 diverges, −1 flow confirms, 0 no new extreme) | Entry timing at a swept level |
| Absorption | Aggressors hit one side hard and price does not move: someone is taking the other side with limit orders | flow against the trade (I < 0 over 30 min) and price not against it | harris ch.13-14 (dealers and value traders supply liquidity), pp.291-334; bouchaud §11.3, pp.231-240 | `absorbed`; `nq_amihud_rel` | "The zone holds" confirmation. (Absorption at stop-outs already failed: H3) |
| VPIN | Share of volume that is one-sided, measured on a volume clock; proposed as "toxicity" | VPIN = Σ_τ \|V^B_τ − V^S_τ\| / (n·V), n = 50 buckets of V = daily volume / 50 | p10-easley pp.6-10; lopez §19.5.2, pp.319-320; critique p11-andersen pp.16-28 | `vpin` | Skip or widen when flow is one-sided. **Contested**: Andersen–Bondarenko show it mostly tracks volume and volatility |
| Kyle's λ (true signs) | Price move per contract of net aggressive flow | Δp_t = λ·delta_t + ε per minute; t-value | lopez §19.4.1, pp.313-315; bouchaud ch.15, pp.309-316 | `kyle_t_true` | Impact regime: thin book = moves travel further |
| Order-sign persistence | Buy and sell pressure persists because large orders are split up | lag-1 autocorrelation of 1m delta; C(ℓ) ~ ℓ^−γ | bouchaud ch.10, pp.206-223; lopez §19.6.5, p.322; p08-bouchaud | `delta_ac` | A persistent one-way tape = don't fade it |
| Order-size distribution | Share of volume in large prints | volume in trades ≥ 10 contracts ÷ all volume, last 60 min | lopez §19.6.1, p.320; bouchaud §10.2, pp.208-209 | `large_share` | "Big players are active" as a filter |
| Hasbrouck's λ, PIN | Variants of price impact per √dollar-volume; probability of informed trading from daily buy/sell counts | Δln p = λ·Σ b√(pV); PIN = αμ/(αμ + 2ε) | lopez §19.4.3, §19.5.1, pp.316-319; hasbrouck ch.6, pp.67-71 | not built: same information as Kyle's λ and VPIN, and PIN is one number per day | — |

## C. Needs quotes or an order book — not available free

| Component | Plain words | Formula | Source | Why not |
|---|---|---|---|---|
| Effective and realized spread, adverse selection | What a trade really paid vs the mid, and how much of it the liquidity provider kept after the price moved | ES = 2D(p − m_t), RS = 2D(p − m_{t+Δ}); adverse selection = ES − RS | bouchaud ch.16, pp.317-337; harris ch.14, pp.310-334; orderflow.md §2 | Needs every trade matched to the quote at that instant (TBBO). We have one day |
| Order-flow imbalance (OFI) | Net change of size at the best bid and ask, including limit orders and cancels, not only trades | e_n from changes in (P^B, q^B, P^A, q^A); ΔP = β·OFI, β ∝ 1/depth | p03-cont §2, pp.3-7; p13-kolm §2, pp.5-11 | Needs every top-of-book update (L1 events) |
| Book / queue imbalance | Which side of the book is heavier | I = (Q_bid − Q_ask)/(Q_bid + Q_ask) | bouchaud ch.7, pp.136-152; cartea ch.12, pp.312-331 | Needs book sizes |
| Microprice / weighted mid | A fair price between bid and ask, tilted by imbalance | P_w = (Q_b P_a + Q_a P_b)/(Q_b + Q_a); P_micro = mid + g(I, S) | p05-stoikov pp.1-10 | Needs book sizes; horizon is seconds |
| Multi-level OFI, depth, hidden liquidity | The same deeper in the book; iceberg / dark liquidity | OFI per level | p04-xu; hasbrouck ch.13, pp.142-153; lehalle §1.4, pp.129-143 | Needs L2 / L3 |
| Square-root impact, propagator | How much a large order moves price and how the impact fades | ΔP ≈ Y·σ·√(Q/V); m_t = Σ G(t−n)·ε_n | bouchaud §12.3, pp.252-258; ch.13, pp.268-288 | About executing size, which we don't do. The propagator could be fitted on NQ 2024 trades, but it describes the tape; it is not a per-trade feature at our horizon |

Dukascopy tick files carry top-of-book sizes from the CFD provider, not an exchange book (orderflow.md §10). OFI or imbalance built from them would describe one broker's quotes; not attempted.
