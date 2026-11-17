# DE40 short — Thu 26 Oct 2023 10:45 NY · engine +1.03 R (tp1) · sheet +1.07 R · day-only +1.07 R
Engine pd_return trade (variant recipe4, unchanged), first run on new indices 2020-2026 (`research/preregistered-recipe-new-indices.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe-new-indices/2023-10-26-1045-DE40-short-pd_return.md`; row in `reports/recipe-new-indices-trades.parquet`. Entry 14745.28 · stop 14796.76 · TP1 = final 14690.40 (5m swing low, 1.07 R) · risk 0.241 ADR · ADR 213.93. Decided 10:14, filled 10:45. Conditions: vol normal, state consolidating, backdrop bear, GDP day (candidate 2).

## Checklist
| # | Step | Grade | Evidence (1-8 known at the entry; 9-10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz + sb_am, last hour normal (1.12x); US GDP at 08:30 (-135 min); filled 45 minutes before the Xetra close; ECB rate decision that morning (general knowledge, not in our calendar: check before using) |
| 2 | Bias / narrative | pass | aligned: weekly, daily, 4H and 1H all bear |
| 3 | Dealing range | fail | 0.18 of the 4h range 14625.77-15304.67: discount, wrong half for a short |
| 4 | POI / array | pass | 1h bearish FVG 14777.10-14813.25 overlapping a 4h bearish FVG 14784.20-14811.65 |
| 5 | Liquidity before | pass | 1h equal highs 14790.18 taken at 08:58 (high 14796.76 at 09:13) |
| 6 | Trigger | partial | after the sweep, down to 14694 by 10:24; the 15m gap is 1.5 points (0.007 ADR); filled 31 minutes after the decision |
| 7 | Stop | partial | on the session high 14796.76 (sits at the pool), inside the 1h FVG (top 14813.25) |
| 8 | Targets | pass | TP1 the 5m swing low 14690.40, 1.07 R, in front of the 1h swing low 14652.90 |
| 9 | Management | pass | TP1 12:15, all off, +1.03 R |
| 10 | Attribution | partial | decent process in the wrong half + win = earned, small |

## Market conditions
Normal volatility, bear backdrop, US GDP day. A two-sided range day: 150 points = 0.70 ADR between 14653 (07:34) and 14797 (09:13), closing in the middle. London sold, the US data hour bought it back to the equal highs, the New York morning sold it again.

## Why it won
The equal highs were taken into the 1h/4h bearish FVG and price fell away; the entry was the second return. It went 0.63 R against (14777.8 at 10:54, the FVG edge) before falling to TP1.

## What the market did (hindsight: lessons to test, not blame)
Turn 14777.8 at 10:54 (0.63 R against, at the 1h FVG's lower edge). TP1 12:15. 1h swing low 16:01 (+1.8 R), 1d swing low Friday.

## Instrument notes
- TP1 (12:15) came 45 minutes after the Xetra close (11:30 New York): the fill of the target is an after-hours futures price.
- The US calendar tags this day "GDP"; for the DAX the event of the day was the ECB (general knowledge, not in our calendar: check before using). A European calendar is missing.
- A 1.5-point 15m gap on a 14,700 index is 1-2 futures ticks.

## Would Sharif take it?
**Maybe.** Everything bear, area reached after a sweep of equal highs, 15m momentum down. But the short is from 0.18 of the 4h range, deep in the discount: the wrong half.

## Verdict
earned win.

## For the engine
- European release calendar (ECB, BoE) for DE40/UK100 before any news split is read on them. One trade is a lead, not evidence: check on all trades, in-sample first.
