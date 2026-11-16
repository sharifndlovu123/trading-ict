# US30 short — Tue 05 Jan 2021 10:53 NY · engine −1.01 R (stop) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, hold-out run of `recipe3: recipe2 + fresh areas only` (pre-registration `research/preregistered-recipe2-2020-2021.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2021-01-05-1053-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`; candle figures re-derived from 1m bars. One trade is a lead, not evidence.

## What they tried to do
Short with 1H and 4H bear (both since 4 Jan 10:00), W/D bull. Area: the 1h bearish FVG 30225.23–30454.75 (0.60 ADR, with a 4h FVG 30275.20–30454.75) from the 4 Jan sell-off, first reached to its 50% at 09:37, high 30394.24. Two 15m candles displaced down 0.66 ADR; limit 30263.77, stop 30394.24, TP1 a 5m swing low 30098.52 (1.27 R).

## What happened
Decided 10:44, filled 10:53, +0.97 R at 11:15 (30137, inside a 1d bullish volume imbalance), then up all afternoon: stopped 14:00, high 30504.0 at 14:30. Wednesday took the previous week and previous day highs.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz, 10:50 macro; last hour busy (2.32×); no scheduled release near |
| 2 | Bias / narrative | partial | 1H and 4H bear; W/D bull, read bull (ltf_pullback) |
| 3 | Dealing range | pass | 0.888 of the daily range: premium |
| 4 | POI / array | pass | 1h FVG 0.60 ADR with a 4h FVG inside it; formed 4 Jan, edge touched 4 Jan 15:48, 50% first at 09:37, reached to 74%; entry inside the area |
| 5 | Liquidity before | fail | no liquidity taken in the 6 h before |
| 6 | Trigger | pass | 10:15 candle 0.187 ADR (2.0× mean) and 10:30 candle 0.29 ADR; gap 0.064 ADR; leg 0.66 ADR |
| 7 | Stop | partial | on the reaction high 30394.24 = session high, inside the area (its top is 60 points higher) |
| 8 | Targets | partial | TP1 1.27 R with a 1d bullish volume imbalance 30133.70–30188.23 in the path |
| 9 | Management | partial | +0.97 R seen, nothing taken, full stop |
| 10 | Attribution | partial | the recipe to the letter; the side is against the daily |

## What the market did (hindsight — lessons to test, not blame)
- The move stopped inside the 1d bullish volume imbalance, 39 points before TP1.
- The afternoon closed through the whole area (1m close above 30454.75 at 14:05).

## Does this look like Sharif's recipe?
- **The area:** 1h FVG 0.599 ADR (wide), with a 4h FVG; first reach of its 50%; to 74%.
- **Side vs structure:** with 1H and 4H; **against the daily**.
- **15m displacement or a small gap:** Yes: two candles, 0.66 ADR.
- **Early or late:** Timely: 67 min after the 50%, entry inside the area.
- **What he would most likely say:** "nice this was just a loss"; partials at the daily imbalance would have paid.
- **Verdict:** fully.

## Price we should have looked at
30504.0 at 14:30: 0.627 ADR above the entry, 0.286 ADR beyond the stop, 49 points above the area's top 30454.75. No mapped level at the turn; the next pool was the previous week high 30633.00. On the profit side: 30137 at 11:15, inside the 1d bullish volume imbalance 30133.70–30188.23 (known).

## Realism
- 15m gap closed before the decision: yes (10:00 / 10:15 / 10:30, ends 10:44).
- Fill: 10:53 bar 17.2 ticks through.
- TP1: missed by 39 points (MFE 0.97 R vs 1.27 R).
- Later information: none found.
- **Result:** no problem found.

## Verdict
**acceptable loss**

## For the engine
- For trades against the daily structure, TP1 = the first opposing daily array if it comes before the pool (here +0.6 R at the imbalance's top; it changes win rate more than R, so judge on R).
