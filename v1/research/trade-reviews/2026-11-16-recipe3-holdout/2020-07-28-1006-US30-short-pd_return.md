# US30 short — Tue 28 Jul 2020 10:06 NY · engine −1.03 R (stop) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, variant "recipe3: recipe2 + fresh areas only", hold-out 2020–2021. Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2020-07-28-1006-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`.

## What they tried to do
1h and 4h bear, daily bull. The 1h bearish FVG 26527.03–26555.56 (formed 06:59) was reached to its 50% on the 09:30 open spike (high 26544.78), which then fell 107 points inside the same 15m candle. The candles 09:15/09:30/09:45 left a gap 26478.79–26479.50. Limit 26478.79, stop 26544.78, TP1 the previous day low 26336.20 (2.16 R).

## What happened
Decided 09:59 with price 0.97 R below the limit (the previous week low 26398.00 was taken at 09:52, low 26380.77). Filled 10:06, went 1.15 R in favour, then drifted up for four hours: stopped 13:58, high 26560.74 at 14:12, back at the entry 15:15, low 26359.79 at 15:58. TP1 at 23:44.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz; last hour normal (1.01×). The news calendar has no rows before 2021-01-07, so "news: none near" on this sheet means "no calendar", not "no news". |
| 2 | Bias / narrative | partial | with the 1h and the 4h; against the daily |
| 3 | Dealing range | pass | 0.604 of the daily range: premium |
| 4 | POI / array | partial | 1h FVG 28.5 points (0.061 ADR), formed today, first return |
| 5 | Liquidity before | fail | the sellside target (previous week low 26398.00) was taken at 09:52, before the entry; no buyside taken apart from the open spike itself |
| 6 | Trigger | fail | the gap is 0.71 points, under one tick; the move itself was a real two-sided open spike |
| 7 | Stop | fail | on the spike high 26544.78: inside the area (its far edge is 26555.56) and under the 4h bearish FVG 26544.78–26566.27; taken by 16 points |
| 8 | Targets | partial | TP1 2.16 R, beyond the session low 26380.77, which was not planned as a partial |
| 9 | Management | partial | 1.15 R in favour with nothing taken off and the stop not moved |
| 10 | Attribution | partial | right side (TP1 traded that night); stop and partials were the error |

## What they missed / should have seen (known at the entry)
- The stop sat under two known levels: the area's far edge 26555.56 and the 4h bearish FVG top 26566.27.
- The previous week low had just been swept: the first objective of a short was already met.

## What the market did (hindsight — lessons to test, not blame)
- The sheet's turn line (26604.20, Wed 15:37) is the next day. Same swing: 26560.74 at 14:12, then 1.8 R down by 15:58 and TP1 overnight.

## Does this look like Sharif's recipe?
- **The area:** 0.061 ADR wide, 2.5 h old, reached to its 50% on the open spike. Thin.
- **Side vs structure:** With the 1h and the 4h; against the daily.
- **15m displacement or a small gap?** The 09:30 candle moved 107 points both ways; the gap it left is 0.71 points. Not a clean displacement.
- **Early or late?** Early (29 min after the touch) but 0.10 ADR below the area, after the previous week low was taken.
- **What he would most likely say:** "we just got swept out by a minor liq grab" and "if we took our partials we would have won here".
- **Verdict:** partly.

## Price we should have looked at
Same swing: 26560.74 at 14:12, 0.175 ADR above the entry and 0.034 ADR (16 points) beyond the stop: 5 points past the area's far edge 26555.56, inside the 4h bearish FVG 26544.78–26566.27. Known at the entry. A stop above 26566.27 (risk 0.19 ADR instead of 0.14) survived.

## Realism
- 15m gap closed before the decision: yes (09:45–09:59).
- **The trigger gap is 0.71 points, under one US30 futures tick (1.0).**
- Fill: 5.7 ticks through. Fine.
- TP1: not reached that day.
- Later information: none found.
- **Result:** problem, see the bold line.

## Verdict
**lesson loss**

## For the engine
- Stop beyond the area's far edge (and any same-direction array touching it) instead of the reaction extreme when the extreme is inside the area: this trade and 9 Jul US500.
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
