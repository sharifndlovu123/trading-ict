# US500 short — Thu 16 Mar 2023 03:41 NY · silver_bullet · engine -1.06 R (stop) · own management -1.00 R · day-only -1.00 R

Batch: cancel-run-dropped (a late fill the `cancel_run_r=1` option would have cancelled). Sheet: `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2023-03-16-0341-US500-short-silver_bullet.md`.

**Trade in one line:** silver bullet short limit 3900.05 in the lower half of the 4h bearish FVG 3891.74–3916.05, stop 3906.13, TP1 = Asia low 3888.36.

## Checklist
| # | Step | Grade | Evidence (steps 1–8: known at the entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london at the decision (the fill at 03:41 is still inside it); last 60 min 0.212 ADR = normal (1.47×); claims 08:30 |
| 2 | Bias / narrative | partial | weekly, 4H, 1H bear; daily bull; read side bull (counter-weekly) does not match |
| 3 | Dealing range | fail | 0.316 of the daily range = discount for a short |
| 4 | POI / array | partial | 4h bearish FVG 3891.74–3916.05 (the 1h POI is 31 points wide); trigger gap 0.56 points |
| 5 | Liquidity before | fail | none in the 6 h before |
| 6 | Trigger | partial | 0.56-point FVG; limit 1.43 R above the decision close |
| 7 | Stop | fail | stop 3906.13 is SHORT of the last-4h high 3910.43 by 0.065 ADR, with the Asia high 3913.88 above that |
| 8 | Targets | partial | TP1 is the Asia low 3888.36 itself (no front-run), just past the last-4h low 3889.37; R:R 1.92 |
| 9 | Management | n/a | stopped before TP1 |
| 10 | Attribution | fail | weak process and a loss |

## The late fill
- Decided 03:00, filled 03:41: **41 min** wait. Risk 6.08 points = 0.092 ADR.
- Limit depth at the decision: the decision bar closed **1.43 R** away from the limit. Run after that, beyond the decision close: 0.33 R.
- Run before the fill, measured from the entry (what the option measures): **1.76 R = 10.68 points = 0.161 ADR**, extreme at 03:15 (15 min after the decision; 26 min from the extreme back to the fill). It covered 0.91 of the distance to TP1.
- Pools: the last-60-min / last-4h low 3893.37 was taken; the run then pressed 3890.1, 3889.4, 3889.4, 3889.9 over 25 minutes and never reached the Asia low 3888.36 (1.0 point short). TP1 = that Asia low, so 0.91 of the way.
- At the fill: stale. Three failures in front of the Asia low, 41 minutes, then a 5m close above the 03:10–03:35 highs (3896.9) at 03:40–03:44 — a lower-TF shift up — on the way to the limit, with six bullish 1m gaps. The 4h high 3910.43 was intact, but the down-leg had been tried and refused.
- **Class: stale: move already done**

## Why it lost
After three refusals at the Asia low, price went for the buyside first: through the limit at 03:41, the stop at 03:54, to 3909.87 at 04:02 — 0.56 under the last-4h high 3910.43 — and only then down to the Asia low (TP1 traded 05:07). The stop was 4 points short of the pool that turned it.

## What the market did (hindsight — lessons to test, not blame)
- Stopped, then TP1 73 minutes later; turn 0.056 ADR beyond the stop.
- Later the day ran the other way: Asia high 10:54, PDH 11:26, 4h equal highs 3939.80.
- The wide-stop counterfactual also lost (−1.04 R).

## Would a better cancel rule have caught it?
Several fire: ADR run 0.161 (largest among the losers), 41 minutes, 0.91 of the way to TP1, an opposing 5m shift before the fill. But each of them also fires on a winner (01-24: all four; 03-21: time and distance; 03-10: ADR). The cleanest description of this one is "repeated failure in front of the TP1 pool, then an opposing shift" — a pattern to count, not yet a rule.

## Verdict
**Lesson loss** — no sweep, discount short, stop short of the 4h high, filled after the leg had failed three times.

## For the engine
- Count on all resting-limit trades: an opposing 5m shift (close beyond the last 5m swing against us) between the run extreme and the fill, when the wait is over 30 minutes; report R with and without (2 such fills here: 01-24 won, 03-16 lost).

*One trade from a batch of 15: a lead, not evidence.*
