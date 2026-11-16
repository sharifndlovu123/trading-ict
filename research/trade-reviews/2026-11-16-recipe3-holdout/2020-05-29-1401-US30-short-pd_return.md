# US30 short — Fri 29 May 2020 14:01 NY · engine −1.02 R (stop) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, variant "recipe3: recipe2 + fresh areas only", hold-out 2020–2021. Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2020-05-29-1401-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`.

## What they tried to do
1h bear, 4h and daily bull. A 7-point 1h bearish FVG 25235.76–25243.04 formed at 11:59 and was traded through at 12:58 (high 25251.29). The 13:30 15m candle displaced down (2.1× the mean body) and left a gap 25159.27–25178.71. Limit 25159.27, stop 25251.29, TP1 25023.28 (1h swing low, 1.48 R).

## What happened
Decided 13:59, filled 14:01, stopped 14:09. High 25331.76 at 14:27, back to the entry at 14:50, low 25069.24 at 14:53 (0.98 R, short of TP1), then a rally to 25508.79 at 16:10. Friday, month-end.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_pm_kz, Friday month-end, decided one minute before the 14:00 cut-off; activity normal (1.02×). The news calendar has no rows before 2021-01-07, so "news: none near" on this sheet means "no calendar", not "no news". |
| 2 | Bias / narrative | fail | against the daily and the 4h (both bull); the engine read says bull |
| 3 | Dealing range | partial | 0.595 of the 4h range: premium, barely |
| 4 | POI / array | fail | the area is a sliver: 7.3 points, 0.013 ADR, two hours old, traded through its far edge on the touch |
| 5 | Liquidity before | fail | only sellside was taken before (London low 09:09, Asia low 10:08, 1h low 10:49): a sell after the lows were run |
| 6 | Trigger | pass | 13:30 candle body 0.085 ADR, 2.1× the mean; gap 19 points (0.034 ADR) |
| 7 | Stop | partial | on the 1h swing high 25251.29, no buffer |
| 8 | Targets | pass | TP1 1.48 R at the 1h swing low, no pool before it |
| 9 | Management | n/a | stopped in 8 minutes |
| 10 | Attribution | fail | a sell from no real area, against the daily, after the sellside was taken |

## What they missed / should have seen (known at the entry)
- The area was 7 points wide and already traded through: there was no higher-timeframe area here.
- Price was inside the 1d bullish FVG 25175.26–25356.00: a daily support area, in a daily bull.

## What the market did (hindsight — lessons to test, not blame)
- After the stop price reached 25331.76 (through the last-4h high 25307.73), dropped to 0.98 R without TP1, then closed the day at the highs.

## Does this look like Sharif's recipe?
- **The area:** 0.013 ADR wide (7 points), 1 h old. Not an area.
- **Side vs structure:** With the 1h; against the 4h and the daily.
- **15m displacement or a small gap?** Yes (2.1× the mean body).
- **Early or late?** Late: 0.14 ADR below the area, PM session, one minute before the cut-off.
- **What he would most likely say:** "wrong bias … the no. 1 focus is where we currently are": inside a daily bullish FVG with the lows already taken.
- **Verdict:** not.

## Price we should have looked at
Same swing: 25331.76 at 14:27, 0.306 ADR above the entry and 0.143 ADR beyond the stop, inside the 1d bullish FVG 25175.26–25356.00 after taking the last-4h high 25307.73. Both levels were known, but the bounce from there failed too: the day closed 3.7 R against.

## Realism
- 15m gap closed before the decision: yes (13:45–13:59).
- Fill: 11 ticks through at 14:01. Fine.
- TP1: not reached.
- Later information: none found.
- **Result:** no problem found.

## Verdict
**lesson loss**

## For the engine
- Two leads: the PM window (0 of 4 in this batch) and a minimum area width that removes slivers (0.013 ADR here).
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
