# US30 short — Mon 21 Dec 2020 10:35 NY · engine −1.01 R (stop) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, hold-out run of `recipe3: recipe2 + fresh areas only` (pre-registration `research/preregistered-recipe2-2020-2021.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2020-12-21-1035-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`; candle figures re-derived from 1m bars. One trade is a lead, not evidence.

## What they tried to do
Short on a gap-down Monday. 1H and 4H bear, W/D bull. Area: a fresh 1h bearish FVG 29936.10–30058.05 (0.34 ADR), filled to 99% at 09:52. The 10:00 candle fell 0.33 ADR and left a 112-point gap; limit at its low edge 29848.26, stop 30056.78, TP1 a 5m swing low 29592.03 (1.23 R).

## What happened
Decided 10:29, filled 10:35, best +0.24 R at 10:37, stopped 11:50. London high 13:31, high 30304.5 at 14:36. No return.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz; last hour busy (2.35×); the news calendar has no rows before 2021-01-07, so "none" here means "not in the file" |
| 2 | Bias / narrative | partial | 1H and 4H bear; W/D bull, read bull (ltf_pullback) |
| 3 | Dealing range | pass | 0.867 of the daily range: premium (yet at the bottom of the day's gap-down) |
| 4 | POI / array | pass | 1h FVG 0.344 ADR, formed 05:59, 50% at 09:37, reached to 99% |
| 5 | Liquidity before | fail | London had already taken the previous day low, the previous week low and three daily swing lows (04:44–05:57): the sellside draw was spent; nothing buyside was taken beyond the retrace into the area |
| 6 | Trigger | pass | 10:00 candle body 0.33 ADR (2.3× mean), gap 112 points (0.317 ADR), leg 0.87 ADR |
| 7 | Stop | partial | on the reaction high 30056.78 (the area's top); risk 0.589 ADR |
| 8 | Targets | fail | entry 0.248 ADR below the area at the bottom of the displacement; TP1 0.72 ADR lower, through a 1d bullish FVG 29667.80–29806.28 that starts 42 points under the entry |
| 9 | Management | n/a | stopped before any partial |
| 10 | Attribution | fail | right area and reaction, sold at the low of the move into a daily bullish gap after the sellside was taken |

## What the market did (hindsight — lessons to test, not blame)
- Price never got further than 0.24 R; the day closed the gap-down.
- The retrace into the 112-point gap (its 50% is 29904) was the place a short could have been considered, not its low edge.

## Does this look like Sharif's recipe?
- **The area:** 1h FVG 0.344 ADR, fresh, reached to 99%.
- **Side vs structure:** with 1H and 4H; **against the daily**.
- **15m displacement or a small gap:** Yes: the gap alone is 0.317 ADR.
- **Early or late:** 52 min after the 50%, but the entry is 0.248 ADR below the area (the gate's limit is 0.25) with a 0.589 ADR stop.
- **What he would most likely say:** "bad trade, very late sell"; the daily FVG is right below and the lows were already taken.
- **Verdict:** partly.

## Price we should have looked at
30304.5 at 14:36: 1.288 ADR above the entry, 0.699 ADR beyond the stop. Levels: 1h swing high 30292.80 and the 4H protected lower high 30314.52. Known at the entry; no stop placement saves this trade.

## Realism
- 15m gap closed before the decision: yes (09:45 / 10:00 / 10:15, ends 10:29).
- Fill: 10:35 bar 3.0 ticks through; 10:39 more than 4 through. Fills under the strict rule.
- TP1: not reached.
- Later information: none found.
- **Result:** no problem found.

## Verdict
**lesson loss**

## For the engine
- Entry no further than 0.15 ADR from the area; and when the 15m gap is wider than ~0.15 ADR, the limit at its 50% rather than its far-side edge.
