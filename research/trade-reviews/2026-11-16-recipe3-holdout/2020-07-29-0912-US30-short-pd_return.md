# US30 short — Wed 29 Jul 2020 09:12 NY · engine +1.00 R (TP1) · sheet +1.07 R · day-only +1.07 R
Engine pd_return trade, variant "recipe3: recipe2 + fresh areas only", hold-out 2020–2021. Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2020-07-29-0912-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`.

## What they tried to do
1h and 4h bear, daily bull. The 1h bearish FVG 26412.00–26511.73 (formed 28 Jul 16:14, tapped at 18:00) was reached to its 50% (26461.87) at 08:12; high 26480.04 at 08:15. The 15m candles 08:15/08:30/08:45 left a gap 26450.04–26452.56. Limit 26450.04, stop 26480.04 (30 points), TP1 26418.01 (5m swing low, 1.07 R).

## What happened
Decided 08:59. The 09:12 bar's high was 26450.06, two hundredths above the limit, and price never traded higher. TP1 at 09:29, low 26373.27 at 09:40; the day then rallied to 26604.20 at 15:37.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz, pre-market; last hour normal (0.71×). The news calendar has no rows before 2021-01-07, so "news: none near" on this sheet means "no calendar", not "no news". |
| 2 | Bias / narrative | partial | with the 1h and the 4h; against the daily |
| 3 | Dealing range | pass | 0.588 of the daily range: premium |
| 4 | POI / array | pass | 1h FVG 0.216 ADR wide, one shallow tap before, reached to its 50% |
| 5 | Liquidity before | partial | Asia high 26442.50 taken at 03:42 |
| 6 | Trigger | fail | gap 2.5 points (0.006 ADR); body 1.24× the mean: no displacement |
| 7 | Stop | partial | on the session high 26480.04; 0.065 ADR risk, cost 0.063 R |
| 8 | Targets | partial | TP1 1.07 R, 0.07 ADR away: a scalp |
| 9 | Management | pass | all off at TP1 |
| 10 | Attribution | partial | the win depends on a fill at the exact high of one bar |

## What they missed / should have seen (known at the entry)
- Risk 30 points and target 32 points on a 461-point ADR, against the daily.

## What the market did (hindsight — lessons to test, not blame)
- The sheet's turn line (26604.20 at 15:37) is the afternoon high, 0.27 ADR beyond the stop: any runner or later short was stopped.

## Does this look like Sharif's recipe?
- **The area:** 0.216 ADR wide, 16 h old, one shallow tap, reached to its 50%. Good.
- **Side vs structure:** With the 1h and the 4h; against the daily.
- **15m displacement or a small gap?** No: 2.5-point gap, body 1.24× the mean.
- **Early or late?** Early: 47 min after the touch, entry inside the area.
- **What he would most likely say:** "short is nice" for the area; no comment on momentum because there was none yet.
- **Verdict:** partly.

## Price we should have looked at
Same swing: 26450.06 at 09:12, the fill bar's high, 0.000 ADR from the entry and 0.065 ADR inside the stop: the 15m gap's lower edge 26450.04. Known.

## Realism
- 15m gap closed before the decision: yes (08:45–08:59).
- **Fill: a touch.** High 26450.06 against a limit of 26450.04: 0 ticks through, at any time. Under the 4-tick rule this +1.00 R winner is not filled.
- TP1: 6.5 ticks through. Fine.
- Later information: none found.
- **Result:** problem, see the bold line.

## Verdict
**lucky win**

## For the engine
- Third of the three winners removed by the 4-tick rule.
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
