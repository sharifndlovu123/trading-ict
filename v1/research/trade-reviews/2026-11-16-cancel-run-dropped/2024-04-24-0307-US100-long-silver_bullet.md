# US100 long — Wed 24 Apr 2024 03:07 NY · −1.00 R (stopped) · day-only −1.00 R · engine −1.05 R

Batch: cancel-run-dropped (late fills the `cancel_run_r=1` option would have dropped) · model silver_bullet · sheet `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2024-04-24-0307-US100-long-silver_bullet.md`

## What they tried to do
Silver bullet London: a leg up from 17585.01 (03:03) left a 1.71-point 1m FVG. Limit 17589.66, stop 17580.44 (0.25 under the last-4-hour low), TP1 the 02:20 5m swing high 17605.41 (1.71 R), in front of the 1h equal highs 17608.19. A long against a daily bear read.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london / london sweet spot; last hour 0.082 ADR = normal (0.93×); no news |
| 2 | Bias / narrative | fail | The read is bear (daily bear since 14 Apr, counter-weekly); the long is against it |
| 3 | Dealing range | pass | 0.454 of the 4h range 16969.61–18335.47 = discount for a long |
| 4 | POI / array | partial | Named POI 1h FVG 17580.17–17584.22 is 5 points below the entry; the 4h bullish FVG 17516.59–17583.30 lies under the stop |
| 5 | Liquidity before | fail | Only buyside had been taken (Asia high 21:19, 4h swing high 17593.70 at 22:07); no sellside swept |
| 6 | Trigger | partial | 1m gap 1.71 points; futures flow last 5 min +0.123 (with the trade) |
| 7 | Stop | fail | 9 points = 0.031 ADR, 0.25 under the last-4-hour low 17580.69: sits on the liquidity, above a 4h bullish FVG |
| 8 | Targets | pass | TP1 5m swing high 17605.41 at 1.71 R, front-running the 1h equal highs 17608.19 |
| 9 | Management | n/a | Stopped before TP1; nothing to manage |
| 10 | Attribution | fail | Against the read, no sweep, noise-size stop on a local low: weak process + loss |

## The late fill
Decided 03:04, filled 03:07 (3 min). One candle reached 17600.31 (03:05): **10.65 points = 1.15 R = 0.035 ADR**, 67% of the way to TP1. No pool taken. Two candles later a 9-point candle filled the limit and closed under it. At the fill the 03:03 low and the 4-hour low were intact. Nothing had changed in three minutes.

Wait 3 min · run 1.15 R = 10.65 points = 0.035 ADR · 67% of the entry→TP1 distance · class: **ordinary retrace**

## Why it lost
The gap did not hold for one candle: MAE 1.73 R, stopped 03:17, and price went to the place the array actually was, the 4h bullish FVG, bottoming at 17528.37 at 05:51 (0.17 ADR beyond the stop). TP1 and the equal highs traded at 08:31–08:32. Same shape as 2023-08-30: the entry was on a 1m gap above the HTF array, the stop between the two.

## Would a better cancel rule have caught it?
No. 0.035 ADR, 3 minutes, no pool, no shift. The 1 R rule fired on one 1m candle. Nothing about the wait distinguishes this loser from the 3-minute winner of 2023-09-14.

## What the market did (hindsight — lessons to test, not blame)
- Stopped 03:17; Asia low 17548.12 at 05:35; low 17528.37 at 05:51; TP1 08:31; then −40 R by Thursday.
- Stopped, then TP1 traded.

## Verdict
**lesson loss.** A 9-point stop above the 4h FVG that price was going to.

## For the engine
- Lead that repeats here and on 2023-08-30: an HTF array in the trade's direction lying just beyond the stop (within 0.2 ADR). Count stopped-then-target with vs without it. One trade is a lead, not evidence.
