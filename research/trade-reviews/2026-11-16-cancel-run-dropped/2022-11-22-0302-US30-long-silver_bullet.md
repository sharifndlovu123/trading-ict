# US30 long — Tue 22 Nov 2022 03:02 NY · silver_bullet · engine +1.31 R (tp1) · own management +0.70 R · day-only +0.70 R

Batch: cancel-run-dropped (a late fill the `cancel_run_r=1` option would have cancelled). Sheet: `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2022-11-22-0302-US30-long-silver_bullet.md`.

**Trade in one line:** silver bullet long limit 33669.21 at the leg start, stop 33645.99 (0.25 under the session low 33646.24), TP1 33701.50 (5m swing high), TP2 Asia high 33768.26.

## Checklist
| # | Step | Grade | Evidence (steps 1–8: known at the entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london; last 60 min 0.088 ADR = normal (0.8×); no news |
| 2 | Bias / narrative | pass | D, 4H, 1H bull; weekly bear (counter-weekly, read side bull matches); small targets near |
| 3 | Dealing range | fail | 0.572 of the 4h range = premium for a long, by a little |
| 4 | POI / array | partial | the POI (1h FVG 33642.00–33654.70) is below the entry, not at it; the entry is inside the 1d bearish FVG 33640.29–33837.21; trigger gap 0.47 points |
| 5 | Liquidity before | pass | sellside taken three times: Asia low 33726.26 (21:28), 1h swing lows 33686.50 (00:38) and 33669.71 (02:01) |
| 6 | Trigger | partial | a 0.47-point FVG — under one futures tick |
| 7 | Stop | fail | 0.0 ADR beyond the session low 33646.24 — on the pool; risk 0.038 ADR |
| 8 | Targets | partial | TP1 33701.50 is 1.7 points past the 5m swing high 33699.8; by the fill that high had already been taken (33700.3 at 03:01); R:R 1.39 |
| 9 | Management | pass | half at TP1 03:20, runner out at entry 03:23: +0.70 R |
| 10 | Attribution | partial | weak stop and trigger; small win |

## The late fill
- Decided 03:00, filled 03:02: **2 min** wait. Risk 23.22 points = 0.038 ADR.
- Limit depth at the decision: the decision bar closed **1.03 R** away from the limit. Run after that, beyond the decision close: 0.31 R.
- Run before the fill, measured from the entry (what the option measures): **1.34 R = 31.09 points = 0.051 ADR**, extreme at 03:01 (1 min after the decision; 1 min from the extreme back to the fill). It covered 0.96 of the distance to TP1.
- Pools: the TP1 pool itself WAS taken: the 5m swing high 33699.8 went by 0.5 points at 03:01 (33700.3). TP1, placed 1.7 points past the pool, was missed by 1.2 points.
- At the fill: structure intact and only 2 minutes old, but the liquidity TP1 was aimed at had just been taken. The fill came on one 26-point down bar (03:02).
- **Class: stale: move already done**

## Why it won
It won because the range repeated: price dipped to 33650.0 (03:09, MAE 0.83 R, 4 points above the session low), went back up and this time reached 33703.5 at 03:20 — TP1 by 2 points. Then straight back: runner out at entry 03:23, session low and the stop level taken at 03:44 (33626.0), and only then the real move (21 R).

## What the market did (hindsight — lessons to test, not blame)
- "Stopped (runner at entry), then target": the real low was 0.033 ADR beyond the stop at the 1d bullish IFVG 33179.30–33625.71.
- Asia high 04:38, PDH 09:18, previous week high 10:50.

## Would a better cancel rule have caught it?
"TP1 pool taken before the fill" would have cancelled it — and cost +1.31 R (engine) / +0.70 R (own). Same signature as the loser 11-08. Run 0.051 ADR, 2 minutes: no other rule fires.

## Verdict
**Lucky win** — the target pool was already gone and the stop held by 4 points; the second push paid TP1 by 2 points.

## For the engine
- Report (do not gate) "TP1 pool taken before the fill" on all resting-limit trades: 1 winner, 1 loser here.

*One trade from a batch of 15: a lead, not evidence.*
