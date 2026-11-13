# ICT Framework — rules every model obeys

`models.md` says *what* to trade, `patterns.md` says *what to look for*. This file holds the rules that sit above both: **bias, timeframes, pricing (premium/discount), POIs, time cycles, and where to close.**

The trading style (§0) is chosen first. Then the engine checks, in this order on every candle: **time window open → bias → price in the right half of the dealing range → at a POI → entry-timeframe trigger.** Time first, then price. A model card can't override these; it can only pick from the options listed here.

All times New York local (DST-aware). Source priority: ICT's direct words (Twitter Spaces, livestreams, transcripts; "Michael" = Michael J. Huddleston = ICT) > reference PDFs > third-party. Contradictions are settled on https://ictindex.io.

---

## 0. Trading style — decide first

Scalping, day trading and swing trading are different games: bias, timeframes, holding time and exits all change. **Every trade is tagged with one style, and all analysis (votes, win rate, expectancy, leaderboard) is reported per style.** Results are never mixed across styles.

| | Scalp | Day trade | Swing |
| --- | --- | --- | --- |
| Bias that must agree | Daily + session | Daily (weekly recorded) | Monthly + weekly (daily for timing) |
| POI timeframe | H1 / M15 | H4 / H1 | D1 / W1 |
| Entry timeframe | M1 (finest our data allows) | M5 / M1 | H1 / M15 |
| Typical window | One killzone hour, macro or Silver Bullet hour | London or NY killzone | Days to weeks |
| TP1 (earliest close) | Nearest 60-minute swing / wick CE / half gap | Opposite side of the day: PDH/PDL, session high/low | Opposite weekly liquidity: PWH/PWL, HTF FVG |
| Time exit | End of the killzone the trade was entered in | 16:00 NY (flat by the close) | Friday close, or after 10 trading days |
| Models that fit | Silver Bullet, macros, OTE, PD array return, MMxM (intraday) | 2022 model, PO3 day, Silver Bullet, TGIF, OTE, MMxM | MMxM (D1/W), PD array return, OTE |

- **Time exits** are neither a vote nor a loss. They are counted as trades, their R goes into expectancy, and the share of trades that time out is reported per model.
- Sources: ICT 2017 Mentorship Month 9 (scalps are micro setups on 5-minute charts framed on higher timeframes), Month 8 (day trades on 15m/5m), Month 6 (swing trades from monthly/weekly). Time-exit and TP1 defaults are engine choices, open to change.

## 1. Bias — trade with it

Bias is a **strategy** (a filter, never a trade). Trading with bias is the default; the engine also runs every model *without* the filter so we can prove what bias adds.

| Level | Read on | Decides | How the engine sets it |
| --- | --- | --- | --- |
| Monthly | Monthly / weekly charts | Long-term order flow; slowest to change | Direction of the last displacement on M / W; next untapped draw (old high/low, HTF FVG) |
| Weekly | Weekly / daily | Direction of the **weekly range expansion** — "the stage for all" day-trading models (ICT, Charter Model 11) | Same, on W / D; plus weekly profile (which day likely forms the weekly high/low) |
| Daily | Daily / 4H | Today's draw on liquidity: PDH or PDL, an old high/low, or a FVG | Bearish if price keeps taking previous-day lows under lower highs (and vice versa); premium vs discount of the dealing range |

- **Alignment:** M + W + D agree → *aligned*. ICT: when monthly, weekly and daily are bullish, intraday charts (4H and below) retrace into discount to buy — that retracement is where models fire.
- **Rule:** a model trades only in the **daily bias** direction by default. Monthly/weekly alignment is recorded on every trade (aligned / mixed / against) and reported.
- **Source:** ICT 2016 Mentorship Month 4 (Order Blocks, Reinforcing Liquidity); 2017 Mentorship Month 6 (Ideal Swing Conditions); Charter Price Action Model 11; "Keys To Daily Bias" (2020); 2022 Mentorship Ep. 18.

## 2. Timeframes — each one has a job

ICT: "the higher time frame PD arrays will draw price… the intraday lower time frame PD arrays will provide the timing and/or price levels to enter on."

| Job | Timeframes | Source |
| --- | --- | --- |
| Bias | Monthly, weekly, daily | ICT 2017 Month 6: "start with a monthly and weekly basis and work down" |
| POI (where price is drawn) | D1, H4, H1 (M15 for intraday) | MMxM PDF p. 4; 2022 slide "weekly profile – intraday swing" (HTF PD array D1–H1) |
| Bellwether / scanning | M15 | MMxM PDF p. 4 |
| Entry (timing + exact price) | M15, M5, M3, M2, M1 | MMxM PDF p. 4; ICT 2017 Month 8: day trades on 15m and/or 5m |

- **Pairing used by default:** daily bias → H1/H4 POI → M5/M1 entry. Other pairings are **params** (e.g. H4 POI → M15 entry for slower assets) and are tested, not assumed.
- Every timeframe is resampled from the 1-minute base, so a POI on H1 and an entry on M1 share exact boundaries.

## 3. Pricing — premium or discount

Price is only "cheap" or "expensive" relative to a **dealing range**. Getting the range right decides whether a POI is valid.

- **Dealing range:** the high and low of the newest swing formed after both buy-side and sell-side liquidity were run (ICT Bible p. 27–28). Price moves internal range liquidity → external range liquidity and back.
- **Equilibrium** = 50% of the range. Above = **premium**, below = **discount** (Bible p. 29). ICT: a FVG "at equilibrium or above is premium, at equilibrium or below is discount" — anchor high to low and read where the gap sits (2023 Mentorship, 6 Jun 2023).
- **Quadrants:** 25%, 50%, 75% (and the CE of every gap/wick) are graded levels ICT writes down daily (2025 Lecture Series, 13 Jan 2025). ICT: "the best buys are going to be in the lower half… in the lower quadrant", the best sells in the upper quadrant (2017 Mentorship Month 7).
- **Which range:** two are measured on every candle —
  - **HTF range** on the POI timeframe, using ICT's 20 / 40 / 60-day look-back to pair premium and discount arrays (2017 Mentorship Month 7). Decides whether a POI is a buy or sell POI.
  - **Intraday range** of the current leg (e.g. the swing that made the Judas swing, or the displacement leg). Decides the entry price; OTE 62–79% is deep discount (or premium) of this leg.
- **Rule:** buy only when price is in discount of **both** ranges; sell only in premium of both. Which quadrant price entered in is recorded on every trade, so the leaderboard can show win rate by quadrant.
- **Premium sensitivity check:** a premium FVG that holds shows no candle bodies closing in its upper half; a discount FVG, none in its lower half (2026 Lecture Series, 21 Apr 2026). Bodies through the CE downgrade the gap.
- **Correct pricing still needs correct time:** a discount POI reached outside a killzone or macro is logged, not traded.

## 4. POI — a FVG means nothing on its own

ICT: "just because… there's a separation between one candle and a candle two candles later, that does not mean that's a tradable inefficiency." What he looks for is "a blending and a confluence of PD arrays and time."

A **POI (point of interest)** is a HTF PD array on the correct side of the dealing range (section 3) where we expect to buy or sell:

- **Buy POI:** a discount PD array (below dealing-range 50%) — bullish OB, FVG, breaker, mitigation block, rejection block, old low / SSL. See the PD array matrix, ICT Bible p. 15.
- **Sell POI:** the premium mirror.
- "Achieve high-timeframe PD array, look left" (MMxM PDF p. 5): the POI must be visible on D1–H1 (M15 intraday) before the entry timeframe is consulted.

**Engine rule:** an entry FVG (or OB) on the entry timeframe only counts if

1. price is **inside or reacting from a HTF POI** in the bias direction, **and**
2. it is **inside the model's time window** (time first, then price), **and**
3. it was created by **displacement**.

FVGs that fail any of these are still logged (so we can measure "FVG outside a POI" vs "inside"), but they never open a trade.

## 5. Time cycles — quarterly theory

Quarterly theory comes from Daye (traderdaye), building on ICT's Power of 3 / AMD; it is not ICT's own. The PO3 Fractal Study shows the same idea at month → week → day: a monthly bearish PO3's Judas swing *was* week 1's bullish profile, and its expansion was weeks 2–3.

Every cycle splits into four quarters following **AMDX**: Q1 accumulation, Q2 manipulation, Q3 distribution, Q4 continuation or reversal.

| Cycle | Quarters | True open (start of Q2) |
| --- | --- | --- |
| Year | Calendar quarters Jan–Mar, Apr–Jun, Jul–Sep, Oct–Dec | April open |
| Month | Weeks 1–4 | Week 2 open |
| Week | Mon, Tue, Wed, Thu (Fri apart) | Tuesday open |
| Day | 18:00–00:00, 00:00–06:00, 06:00–12:00, 12:00–18:00 | **00:00** — matches ICT's midnight open |
| 6h session | Four 90-minute quarters (e.g. 06:00–07:30, 07:30–09:00, 09:00–10:30, 10:30–12:00) | 2nd quarter open (e.g. 07:30) |
| 90 min | Four 22.5-minute quarters | 2nd quarter open |

- **Engine use:** every candle is labelled with its quarter at every level. Quarters are a **time bucket** on the leaderboard (e.g. "Silver Bullet entries in Q3 of the NY AM session").
- **Default:** only the 00:00 true day open is used as a *price level*. The other true opens are used only as *time labels* (which quarter a trade happened in), so the leaderboard can show whether quarters matter. Source quality is secondary (LuxAlgo, TradingView scripts).

## 6. Killzones and windows

Index futures killzones (2022 Content slide "index future kill zones"): **London 02:00–05:00, NY AM 08:30–11:00, NY PM 13:30–16:00.** The ICT Bible gives 08:30–12:00 for the AM session; the narrower window is the default and the wider one a param. FX killzones: ICT Bible p. 9. Silver Bullet hours and macros: see `models.md` and `patterns.md`.

From Sharif's Notion notes (`personal/notion/`):
- **London sweet spot 02:00–04:00** inside the 02:00–05:00 killzone; expect a Judas swing (Twitter Spaces).
- **NY lunch 12:00–13:00 = no new trades** (2022 Mentorship). At 13:30 wait for a swing high/low before the PM program starts.
- 15:40 / 15:50 / 16:00 — price accelerates into the close (2022 Mentorship EP 5).
- If London (02:00–05:00) makes a huge range on equities, skip NY AM; from 13:00 expect the NY morning high/low to be taken (2022 Mentorship). Param: `skip_am_after_big_london`.
- CBDR = 14:00–20:00, range < 40 pips (ideally 20–30) — confirmed on ictindex (ruling: `personal/ictindex-rulings.md`); 16:00–20:00 (2024 lecture) as a param.

## 7. Where to close

Every trade states its **earliest close (TP1)** before it opens, plus a final target.

**Earliest close (TP1) — the "low-hanging fruit":**
- Nearest untapped relative equal low/high or single swing low/high on the 60-minute chart (ICT, Twitter Space 29 May 2023).
- The CE (midpoint) of a nearby wick — ICT: if price trades to the CE of a wick, "you must take partials… always, cast in stone" (Price Action Workshop, 15 Jun 2023).
- Half of the opening range gap, or the previous session's low/high when gapping (NQ review, Aug 2026).
- Internal range liquidity inside the current dealing range.

**Final target:** external range liquidity; the model's terminus (e.g. original consolidation in MMxM); or standard-deviation projections of the manipulation leg at −1, −2, −2.5, −4 (2022 slide "fibonacci settings"; example "POI divergence – low risk sell": TP1 at the nearest low, final at −4 STDV + SSL).

**Voting:** the vote is decided at **TP1** — TP1 hit before the stop = 1 vote. Whether the runner reached the final target is recorded and reported as a separate rate, and expectancy is computed for both "all out at TP1" and "partial at TP1 + runner" variants.

## 8. Entry and stop options

Models pick from these; the engine tests each variant.

| Entry type | Where | Stop type | Where |
| --- | --- | --- | --- |
| Entry drill | Proximal edge of the FVG/OB (first touch) | Imbalance end | Beyond the far end of the imbalance |
| Consequent encroachment | 50% of the FVG | Order block | Beyond the OB that launched the move |
| Complete fill | Far edge of the FVG | Swing point | Beyond the swing that was swept |

Source: 2022 Content slide "entry types / stop loss types". Order block quality (same deck, "selective preference"): prefer a **defined candle body** (most range between open and close) over a small body with a large wick.

**From ICT's live executions** (`personal/notion/live-exec.md`): extra stop type **wick CE** — stop at the 50% of the wick that swept liquidity (5 Jan 2024). **After TP1, trail the stop** to just below the HTF FVG that launched the move (8 Dec 2023 NFP) — runner variant. Prefer **unfilled** PD arrays: a low/FVG already delivered efficiently is not a target or entry zone (8 Dec FVG tip).

**Multiple FVGs in one displacement:** enter on the higher one (sells) / lower one (buys) when price returns (2022 Mentorship). **OB entry zone:** body midpoint to the candle's high (bullish down-close candle), stop below the zone (Core Content Month 2).

## 9. PD array validity (when a gap stops counting)

ICT livestream 30 Oct 2023, via `personal/notion/trading-extras.md`:
- **Quadrants:** on 4H / daily / weekly imbalances use 0 / 25 / 50 / 75 / 100%; on LTF only high, low and 50%. A body close beyond 25% or 50% → expect the far side to be reached.
- **Volume imbalance:** retired once bodies close through it both above and below; if only wicked, it stays a live target.
- **IFVG:** valid while no candle *body* closes beyond it; wicks into it are fine.
- **Breaker:** once a candle closes beyond its 50%, expect no return to its far side (2022 Mentorship).
- **NDOG** (index futures): primary = 16:59 last print → 18:00 open; secondary = 16:14 RTH settlement → 18:00 open when the primary has no gap. The opening range gap (16:14 → 09:30) is separate. Compute all three (ruling: `personal/ictindex-rulings.md`). Dukascopy CFDs have no real halt — use the prints at those times.
- **Rebalanced imbalance:** once fully rebalanced, the swing it created becomes an ITH/ITL (2022 Mentorship, "advanced — revisit").

## 10. Trade filters and limits (tags first, then test)

Mostly ICT Twitter Spaces (`personal/notion/twitter-spaces.md`). Each is a **tag** on every trade *and* a filter param, so we can measure it rather than assume it.
- **News:** no trades on FOMC days; before CPI is off-limits, after the release is fine. **NFP week:** NFP Monday is always a trading day (ordinary Mondays: sit on hands); trade Mon–Tue, no new positions after Wednesday's AM session; if Mon–Wed has a holiday, skip Monday and trade Thu/Fri (ruling: `personal/ictindex-rulings.md`). "No trades the days before NFP" is kept only as a variant. Tag every trade with the day's event.
- **August:** generally poor — tag month, report August separately.
- **Daily cap (Silver Bullet):** 3 windows = 3 chances; **one trade per day — a win or a loss ends the day**; a window with no setup passes the chance to the next (ruling: `personal/ictindex-rulings.md`). Separate risk variant (ICT 2022 Ep 41): after a loss risk ½, then ¼, back to full once half the loss is recovered.
- **Risk:reward:** "3:1 is a religion"; ICT's son trades 2:1 (ruling: `personal/ictindex-rulings.md`). Report expectancy at fixed 2R as the benchmark, with 1R and 3R beside it, alongside TP1-based targets. Minimum framework 10 handles / 15 pips of *potential* confirmed; NQ preference 20-handle range for a 15-handle TP1 (variant).
- **Low-resistance vs high-resistance run:** many swing points between price and the target = high resistance; skip unless NFP/FOMC/CPI volatility (Core Content).
- **Avoid piling in at 09:30** (no window length given).
