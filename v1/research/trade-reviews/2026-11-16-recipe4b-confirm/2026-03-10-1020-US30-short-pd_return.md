# US30 short — Tue 2026-03-10 10:20 NY · engine -1.01 R (stop; with partials -1.01) · sheet -1.00 R · day-only -1.00 R
Engine pd_return trade, confirmation run of `recipe4b` on 2024-07 → 2026-11 (FAILED: 81 trades, 33.3% win, −0.17 R; `research/preregistered-recipe4b-2024H2-2026.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2026-03-10-1020-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`. Entry 47627.22 · stop 47847.54 · TP1 46997.94 (pwl, 2.86 R) · risk 0.289 ADR · ADR 763.56. Decided 09:59, filled 10:20.

## What they tried to do
Short with the daily/4H the morning after a 2-ADR reversal day: 1h bearish FVG 47668.65–47752.68 (0.11 ADR) reached (high 47771.19, through its top), the 09:30 15m candle pushed down, limit at the gap edge 47627.23. Stop 0.10 ADR above the reaction high; target the previous week low 46997.94 (2.86 R).

## What happened
Decided 09:59; price fell 0.88 R first (Asia low taken 09:57), came back and filled 10:20, stopped 10:40. It went on to 48221.20 at 13:28 into the 4h/1d bearish FVGs, then fell 1.88 ADR: target Wednesday 19:30.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz, sb_am; no news (CPI next morning); last hour 0.44 ADR = 0.76× normal |
| 2 | Bias / narrative | partial | daily + 4H bear, weekly bull; 1H bull since 09 Mar 15:00 (yesterday's reversal): 'where we currently are' was up |
| 3 | Dealing range | pass | 0.519 of the 4h range: premium, just |
| 4 | POI / array | partial | 1h bearish FVG 0.11 ADR, traded right through (18 pts past its top) before the trigger; two 4h bearish FVGs 47880–47997 and 47962–48251 untouched above |
| 5 | Liquidity before | fail | only sellside taken (Asia low 09:57, with the trade); 1h swing high 47924.67 untaken |
| 6 | Trigger | partial | body 0.128 ADR, 2.16×; gap 7.5 pts (0.01 ADR) |
| 7 | Stop | fail | stop 47847.54 is 0.101 ADR short of the 1h swing high 47924.67 and under the 4h FVG 47880.50 |
| 8 | Targets | partial | single target the previous week low, 2.86 R / 0.82 ADR away, session low in the way |
| 9 | Management | n/a | stopped 20 minutes after the fill |
| 10 | Attribution | fail | the lesson: sold under the real area |

## What they missed / should have seen (known at the entry)
- The 4h bearish FVGs and two 4h swing highs were 0.3–0.6 ADR above: the higher-timeframe area had not been reached.
- 1H structure bull after a 2-ADR up day; stop short of the 1h swing high.

## What the market did (hindsight — lessons to test, not blame)
- Price went 0.49 ADR past the stop into the 4h bearish FVG 47962–48251 / 1d bearish FVG 48095–48211, then gave 6.5 R.
- Same day it only came back to 47655 (−0.13 R).

## Market conditions
- **Known before the day:** trending down (20-day efficiency 0.425), backdrop mixed, volatility high (1.307× its 1-year median), no scheduled high-impact release.
- **The day:** range before the decision 0.65 ADR; whole day 1.03 ADR; 09:30–16:55 range 1.03 ADR, net +0.07 ADR. Trending down (0.43), mixed, high volatility (1.31×), no news — the cell the regime study liked. The day itself: RTH range 1.03 ADR, net +0.07: up to 13:28, back down by the close. A rotation day before CPI.
- **Day type:** range day.

## Does this look like Sharif's recipe?
- **Area:** 1h FVG 47668.65-47752.68, 0.11 ADR wide; entry +0.054 ADR from its near edge (negative = inside it).
- **15m:** middle candle 09:30 body 0.128 ADR = 2.16× the mean of the 20 before; gap 0.01 ADR (7.5 ticks).
- The 1h area was traded through and the 15m gap is 7 points; the area he would name is the 4h FVG above.
- **What he would most likely say:** 'sold a bit too early, notice the fvg at 4hr' — almost word for word his most repeated note.
- **Verdict:** partly.

## Why it lost
Entered early, under the 4h area price was still drawn to; stop short of the 1h swing high.

## Price we should have looked at
48221.20 at 13:28: 0.778 ADR above the entry, 0.489 ADR beyond the stop; 4h bearish FVG 47962.46–48250.97 and 1d bearish FVG 48095.44–48211.49. Known at the entry.

## Realism
- 15m gap closed before the decision: yes (candles 09:15 / 09:30 / 09:45, the third ends at 09:59); the entry is the gap's near edge; the stop is the reaction extreme 47771.19 ∓ 0.10 ADR (that price is on the 1m bars before the decision).
- Fill bar traded 23.7 ticks through the limit; price ran 0.88 R our way between the decision and the fill.
- TP1 did not trade that day.
- Resting limit: price ran 0.88 R before the fill.
- The row's `thru` is 2.1 ticks, but the fill bar traded 23.7 ticks through the limit on the 1m bars: the column is measured differently — worth a check.

## Verdict
**lesson loss**

## For the engine
- When an untouched same-direction 4h FVG lies within 0.6 ADR beyond the 1h area, prefer it (4h over 1h): count on all recipe trades.
- One trade is a lead, not evidence; nothing is re-tuned on 2024-07 → 2026-11.
