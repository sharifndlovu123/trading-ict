# US30 long — Wed 19 Apr 2023 10:05 NY · +5.75 R (TP1 50%, TP2 50%) · day-only +5.75 R · engine +5.53 R

Batch: cancel-run-dropped (late fills the `cancel_run_r=1` option would have dropped) · model silver_bullet · sheet `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2023-04-19-1005-US30-long-silver_bullet.md`

## What they tried to do
Silver bullet AM: after the 09:30 high (33946.79) price flushed to 33809.71 at 09:48, turned, and left a 5.71-point 1m FVG at the leg start. Limit at 33830.21, stop under the 09:48 low, TP1 the 09:30 high (5.6 R), in front of the Asia high 33952.27. Counter-weekly leg, daily bull, in the OTE of the 4h range.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_am + macro 09:50; last hour 0.371 ADR = normal (1.22×); no news near |
| 2 | Bias / narrative | partial | Counter-weekly leg (W bear, D bull since 10 Apr); side matches the read |
| 3 | Dealing range | pass | 0.264 of the 4h range 33722.28–34131.01 = discount, in the OTE (33877.60–33808.11) |
| 4 | POI / array | partial | Named POI is the 1h FVG 33790.30–33818.24, but the entry is 12 points above it at a 1m gap; no HTF array at the entry price |
| 5 | Liquidity before | pass | Sellside 1h swing low 33870.70 taken at 04:11; the 09:48 flush to 33809.71 after the 09:30 run on buyside 33931.30 |
| 6 | Trigger | partial | Leg-start 1m FVG of 5.71 points, resting limit |
| 7 | Stop | partial | 0.25 points under the 09:48 low; SHORT of the 1h swing low 33797.59 by 0.032 ADR (sits at the liquidity) |
| 8 | Targets | pass | TP1 = the 09:30 high 33946.79, front-running the Asia high; no pool before it; 5.6 R |
| 9 | Management | pass | 50% at TP1 and 50% at the Asia high, both 14:00; flat the same day |
| 10 | Attribution | pass | Discount + OTE + sweep + side with the daily: good process + win |

## The late fill
Decided 10:00, filled 10:05 (5 min). Price ran to 33856.27 at 10:04: **26.06 points = 1.26 R = 0.071 ADR**, only 22% of the way to TP1. It did not even pass the pre-decision high of 09:56 (33866.25), so no pool was taken. The fill bar (10:05) dropped 25 points to 33825.22. At the fill the 09:48 low was intact (15 points below the fill-bar low) and the turn came two minutes later at 33823.22. The idea was fully valid.

Wait 5 min · run 1.26 R = 26.06 points = 0.071 ADR · 22% of the entry→TP1 distance · class: **ordinary retrace**

## Why it won
MAE 0.34 R, then a four-hour grind to the 09:30 high and the Asia high at 14:00 (+6.27 R MFE). Location did the work: OTE of the 4h range after a sellside flush, with the daily.

## Would a better cancel rule have caught it?
No, and it should not. The run was 0.07 ADR and a fifth of the target distance. An ADR-based run (≥ 0.15), a fraction-of-target test (≥ 80%) or a pool-taken test all keep this trade. The 1 R rule threw away the best trade of the batch.

## What the market did (hindsight — lessons to test, not blame)
- Turn 33823.22 at 10:07 (nothing on the map there), then +6.6 R to 33952 by 14:00.
- Next day the stop-side pools went: 1h swing low 33797.59 and the previous day low at 03:28–03:30. Day-only was right.

## Verdict
**earned win.** Keep. Note the same fill is also a 2022_model row (decided 09:51, cap 2 R, +1.91 R): one trade counted in two models.

## For the engine
- When the dropped set is studied, de-duplicate fills shared by two models (same asset, minute, entry and stop) so one trade does not count twice. One trade is a lead, not evidence.
