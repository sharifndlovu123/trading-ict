# US30 short — Fri 21 Jan 2022 03:05 NY · silver_bullet · engine -1.09 R (stop) · own management -1.00 R · day-only -1.00 R

Batch: cancel-run-dropped (a late fill the `cancel_run_r=1` option would have cancelled). Sheet: `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2022-01-21-0305-US30-short-silver_bullet.md`.

**Trade in one line:** short limit 34779.29 at the leg start (bottom of the 1h bearish FVG 34766.80–35135.30), stop 34800.01 (0.25 above the session high 34799.76), TP1 34660.28 (5m swing low), TP2 Asia low 34444.71.

## Checklist
| # | Step | Grade | Evidence (steps 1–8: known at the entry) |
|---|---|---|---|
| 1 | Time and activity | pass | london_kz / sb_london; last 60 min 0.326 ADR = busy (2.29×); no news |
| 2 | Bias / narrative | partial | W and D bull, 4H and 1H bear: a lower-TF pullback short; read side bull does not match, but the target is near (0.28 ADR) |
| 3 | Dealing range | fail | 0.051 of the daily range = deep discount for a short; price is past the OTE, the daily protected low 34662.72 is 0.2 ADR below |
| 4 | POI / array | partial | lower edge of the 1h bearish FVG, with the 4h bearish FVG 34718.23–35238.22 and the 1d IFVG 34805.79–35207.30 stacked on it |
| 5 | Liquidity before | pass | buyside Asia high 34695.24 taken at 00:45 |
| 6 | Trigger | partial | 8.9-point FVG; blind limit at the leg start 48 points above price at the decision |
| 7 | Stop | fail | stop 0.001 ADR beyond the session high 34799.76 — on the pool; the 1d IFVG low 34805.79 sits 6 points above it |
| 8 | Targets | partial | TP1 34660.28 is exactly the 5m swing low (no front-run) and 2.4 points under the daily protected low 34662.72; R:R 5.74 |
| 9 | Management | n/a | TP1 never filled, stop never moved; day-only identical |
| 10 | Attribution | fail | mixed process; lost on a 0.3-point miss |

## The late fill
- Decided 03:00, filled 03:05: **5 min** wait. Risk 20.72 points = 0.048 ADR.
- Limit depth at the decision: the decision bar closed **2.33 R** away from the limit. Run after that, beyond the decision close: 0.39 R.
- Run before the fill, measured from the entry (what the option measures): **2.72 R = 56.29 points = 0.131 ADR**, extreme at 03:02 (2 min after the decision; 3 min from the extreme back to the fill). It covered 0.47 of the distance to TP1.
- Pools: TP1 pool NOT taken (run low 34723.0, TP1 34660.28). No nearer named pool taken; the run only re-tested the 02:39 low 34730.2.
- At the fill: fully valid. The limit was simply 2.33 R behind the decision close, so "ran 1 R unfilled" was true on the decision bar. The fill came 5 minutes later on one 30-point up bar (03:05: 34751→34781) that stopped 1.8 points past the limit.
- **Class: ordinary retrace**

## Why it lost
The fill was the high of the move: price fell to 34660.6 at 03:22 — **MFE 5.73 R, TP1 at 5.74 R, missed by 0.3 points** — bounced off the daily protected low, and came back to take the session high and the stop at 05:22 (turn 34895.0 at 11:23). TP1 traded at 06:24 and the Asia low at 10:22 (+16 R). A TP on the level instead of in front of it turned a winner into a full loss.

## What the market did (hindsight — lessons to test, not blame)
- Stopped, then TP1 an hour later; price went on 27 R our way.
- The wide-stop counterfactual on the row is +3.77 R.
- The turn at 34895 was inside the 1d IFVG 34805.79–35207.30 — the array above the stop.

## Would a better cancel rule have caught it?
No, and it should not: this was the best-timed fill of the batch (0 adverse until 5.7 R). 0.131 ADR run looks "big", but 2.33 R of it existed at the decision. An ADR threshold of 0.1 would have cancelled it; a run measured from the decision close (0.39 R, 0.019 ADR) would not.

## Verdict
**Lesson loss** — good location, lost to TP1 placed on the pool (0.3 points short) and a stop on the session high. Change: front-run TP1 by a tick or two.

## For the engine
- TP1 audit: count trades whose MFE ended within 1 futures tick + spread short of TP1 and were later stopped; price them with TP1 front-run by 1–2 ticks (in-sample first).

*One trade from a batch of 15: a lead, not evidence.*
