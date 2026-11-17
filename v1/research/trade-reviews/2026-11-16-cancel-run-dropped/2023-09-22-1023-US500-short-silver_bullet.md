# US500 short — Fri 22 Sep 2023 10:23 NY · −1.00 R (stopped) · day-only −1.00 R · engine −1.08 R

Batch: cancel-run-dropped (late fills the `cancel_run_r=1` option would have dropped) · model silver_bullet · sheet `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2023-09-22-1023-US500-short-silver_bullet.md`

## What they tried to do
Silver bullet AM: a leg down from the 10:06 high 4346.92 left a 0.68-point 1m FVG inside the 4h bearish FVG 4333.20–4350.29. Limit 4342.74, stop 4347.17, TP1 the 09:50 5m swing low 4332.85 (2.23 R), runner to the Asia low. Daily bear against a weekly bull.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_am; last hour 0.326 ADR, 0.73× the normal (labelled normal); no news |
| 2 | Bias / narrative | partial | Counter-weekly leg (W bull, D bear since 16 Aug); side matches the read |
| 3 | Dealing range | fail | 0.131 of the 4h range 4324.17–4466.03 = deep discount for a short |
| 4 | POI / array | fail | Inside the 4h bearish FVG, but straight above the 1w bullish FVG 4322.26–4340.71 and the 1d bullish FVG 4322.26–4334.56: selling into HTF support |
| 5 | Liquidity before | fail | No pool taken in the 6 h before |
| 6 | Trigger | fail | Trigger gap 0.68 points |
| 7 | Stop | fail | Just above the 10:06 high; SHORT of the 1h swing high 4348.06 by 0.021 ADR |
| 8 | Targets | partial | TP1 4332.85 at 2.23 R sits inside the 1d bullish FVG (top 4334.56): an array in the way |
| 9 | Management | n/a | Stopped before TP1; nothing to manage |
| 10 | Attribution | fail | Discount short with no sweep into weekly and daily bullish gaps: weak process + loss |

## The late fill
Decided 10:11, filled 10:23 (12 min). Price fell to 4335.57 at 10:16: **7.17 points = 1.62 R = 0.166 ADR**, 73% of the way to TP1. No pool taken (the 09:50 low 4332.85 held). The run went 5 points into the 1w bullish FVG and stopped 1 point above the 1d bullish FVG (4334.56). From there a higher low (4338.51) and a single 4-point candle at 10:23 that closed on its high at 4344.41, through the 10:20 high. At the fill the 10:06 high was intact, but the bounce came off HTF support with force.

Wait 12 min · run 1.62 R = 7.17 points = 0.166 ADR · 73% of the entry→TP1 distance · class: **ordinary retrace**

## Why it lost
The bounce from the weekly/daily bullish gaps carried through the entry: 1h swing high 4348.06 taken at 10:31 with the stop, then 4357.31 by 11:39 (0.235 ADR beyond the stop). TP1 traded at 13:38 and the Asia low at 14:16. Right side for the day; the short was placed at the low of the morning range.

## Would a better cancel rule have caught it?
Partly. An ADR run ≥ 0.15 catches it (0.166). So does "the unfilled run was rejected at an opposing HTF array" (1w/1d bullish FVG). A pool-taken or 80%-of-target test does not; 12 minutes is not long. Better still is step 4 before the order: no short directly above two bullish HTF gaps.

## What the market did (hindsight — lessons to test, not blame)
- Stopped 10:31, high 4357.31 at 11:39, TP1 traded 13:38, Asia low 4324.17 at 14:16.
- MFE after the fill 0.62 R.

## Verdict
**lesson loss.** Discount short into HTF support with a stop under the nearest 1h high.

## For the engine
- Same count as 2023-08-30: unfilled run rejected at an opposing HTF array, with vs without, on all dropped trades. One trade is a lead, not evidence.
