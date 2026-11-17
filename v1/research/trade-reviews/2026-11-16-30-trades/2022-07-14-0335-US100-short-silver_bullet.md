# US100 short — Thu 14 Jul 2022 03:35 NY · +2.19 R (TP1 03:58, TP2 04:00) · day-only +2.19 R

Engine silver-bullet trade, in-sample. Fact sheet: `../sheets/2026-11-16-30-trades/2022-07-14-0335-US100-short-silver_bullet.md`.

## What they tried to do
London silver bullet short at the low edge of the 1h bearish FVG 11669.44–11771.19, with the weekly / daily bear (read side bear). Entry 11674.66, stop 11691.93, TP1 11638.23 (front of the Asia low), TP2 the Asia low 11635.61.

## What happened
Price went to 11690.21 at 03:37 (−0.9 R, 1.7 pts from the stop), then dropped: TP1 03:58, TP2 04:00. It ran on to about 11481 by 10:12 (+11.2 R) and reversed hard after.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london / sweet spot, 03:35; activity normal (0.83×); PPI 4.9 h away |
| 2 | Bias / narrative | pass | read ltf_pullback, side bear = the trade; W / D / 1H bear |
| 3 | Dealing range | fail | 0.335 of the 1d range 11036.23–12941.71 = discount; price inside the 1d bullish FVG 11583.40–11696.71 |
| 4 | POI / array | partial | 1h FVG entered at its low edge; the first clean sell arrays were the 1h bearish FVG 11696.89–11705.66 and the 1d bearish FVG from 11727.38 |
| 5 | Liquidity before | partial | Asia high 11687.62 taken at 21:57, 5.6 h earlier; 1h swing high 11729.72 untaken |
| 6 | Trigger | partial | proxy: −0.9 R of heat right after the fill |
| 7 | Stop | fail | 17 pts (0.052 ADR), 5 pts under the 1h bearish FVG 11696.89 and 0.114 ADR short of the 1h swing high 11729.72 |
| 8 | Targets | partial | TP1 front-runs the Asia low (good), R:R 2.11; TP2 is 2.6 pts further, so there is no real runner; PDL 11448.56 was the daily draw |
| 9 | Management | pass | both partials inside 25 min, day-only |
| 10 | Attribution | partial | right side, stop survived by 1.7 pts |

Step 6 is a proxy.

## Price we should have looked at
- **The turn:** 11690.21 at 03:37, 0.047 ADR above the entry, inside the stop by 1.7 pts. Known levels: the top of the 1d bullish FVG 11696.71 and, 6.7 pts higher, the 1h bearish FVG 11696.89–11705.66.
- **Known at entry:** yes. The better entry was the 1h bearish FVG 11696.89 (0.067 ADR above the entry) with the stop above 11705.66 or the 1h swing high 11729.72. We sold 22 pts early and the stop sat under the array instead of beyond it.
- **Target:** TP2 = Asia low left 8+ R. Price reached about 11481, 32 pts short of PDL 11448.56 (the read's draw); a runner front-running PDL would have been filled only with a front-run of more than 0.1 ADR.

## What they missed / should have seen (known at the entry)
- The stop was 5 pts in front of the array that should defend the short.
- TP1 and TP2 were the same pool.

## What the market did (hindsight — lessons to test, not blame)
- 12 R from the turn in 6.5 h, then −18 R against by the next day: day-only mattered.

## Verdict
**lucky win.** Right side and target; the stop held by 1.7 pts.

## For the engine
- Stop beyond the nearest same-side array within 0.05 ADR (`stop_mode` variant "beyond array") and a TP2 that is a different pool from TP1 (min 1 R apart).
