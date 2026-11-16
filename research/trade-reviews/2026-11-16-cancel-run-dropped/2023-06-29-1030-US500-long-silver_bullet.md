# US500 long — Thu 29 Jun 2023 10:30 NY · −1.00 R (stopped) · day-only −1.00 R · engine −1.06 R

Batch: cancel-run-dropped (late fills the `cancel_run_r=1` option would have dropped) · model silver_bullet · sheet `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2023-06-29-1030-US500-long-silver_bullet.md`

## What they tried to do
Silver bullet AM, everything aligned bull: a leg up from the session low 4369.55 left a 2.46-point 1m FVG at 10:14. Limit 4381.53, stop 4375.64 behind the 1m low, TP1 the 10:05 5m swing high 4388.84 (1.24 R), runner to the previous week high 4417.13.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_am; last hour 0.446 ADR = normal (1.08×); GDP was two hours earlier |
| 2 | Bias / narrative | pass | Aligned: weekly and daily bull; side matches the read |
| 3 | Dealing range | fail | 0.783 of the 4h range 4328.06–4396.38 = premium for a long |
| 4 | POI / array | fail | Entry 5 points above the named 1h FVG 4369.65–4376.67, at the top edge of the 1w bullish IFVG (4380.73); 1d bearish IFVG 4391.50–4406.37 overhead |
| 5 | Liquidity before | fail | Only buyside had been taken (Asia high, previous day high 06:16, 4h high 08:30); no sellside pool swept |
| 6 | Trigger | partial | 1m gap of 2.46 points, resting limit |
| 7 | Stop | fail | Behind the 1m low 4375.89 only; SHORT of the session low 4369.55 by 0.141 ADR |
| 8 | Targets | partial | TP1 4388.84 at 1.24 R; by the fill price had already traded 4388.38, 0.46 points from it |
| 9 | Management | n/a | Stopped before TP1; nothing to manage |
| 10 | Attribution | fail | Premium long with no sweep, filled after the target was all but tagged: weak process + loss |

## The late fill
Decided 10:15, filled 10:30 (15 min). Price climbed to 4388.38 at 10:22: **6.85 points = 1.16 R = 0.159 ADR**, which is **94% of the way to TP1** (4388.84, missed by 0.46 points). The scalp this order was placed for had been paid without us. Then a lower high (4385.21 at 10:27) and a lower low (4381.68 at 10:28) on the 1m before the fill bar closed at 4379.46. At the fill the short-term move was done and turning; the launch low 4375.89 was still intact.

Wait 15 min · run 1.16 R = 6.85 points = 0.159 ADR · 94% of the entry→TP1 distance · class: **stale: move already done**

## Why it lost
The fill was the first leg of the pullback after the target was reached, not the pullback before it. Price went on to 4374.51 (10:48), 1.1 points past the stop, turned there inside the 1w bullish IFVG, and traded TP1 at 11:15. Right idea (it ran 13 R by Friday), entry one retrace too early for a 5.9-point stop.

## Would a better cancel rule have caught it?
Yes: a fraction-of-target test. "Cancel when the unfilled run has covered ≥ 80% of the distance to TP1" catches it (94%). An ADR run ≥ 0.15 also catches it (0.159). A time limit of 15 min would be borderline. The 1 R rule caught it only because TP1 was 1.24 R away.

## What the market did (hindsight — lessons to test, not blame)
- Stopped 10:46, low 4374.51 at 10:48, TP1 traded 11:15, 1h swing high 4396.38 at 12:28.
- The previous week high 4417.13 (the runner target) traded Friday 08:30.

## Verdict
**lesson loss.** The order should have died at 10:22 when the target was reached without it.

## For the engine
- Test cancel_run as a fraction of the TP1 distance (≥ 0.8) next to the ADR version; both in-sample first. One trade is a lead, not evidence.
