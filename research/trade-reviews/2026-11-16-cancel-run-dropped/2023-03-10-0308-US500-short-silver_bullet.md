# US500 short — Fri 10 Mar 2023 03:08 NY · silver_bullet · engine +2.15 R (tp1) · own management +1.11 R · day-only +1.11 R

Batch: cancel-run-dropped (a late fill the `cancel_run_r=1` option would have cancelled). Sheet: `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2023-03-10-0308-US500-short-silver_bullet.md`.

**Trade in one line:** silver bullet short limit 3896.90 under the 4h bearish FVG 3898.86–3907.65, stop 3901.39 (0.25 above the last-4h high 3901.14), TP1 3886.90 (5m swing low), TP2 3882.39, on NFP morning.

## Checklist
| # | Step | Grade | Evidence (steps 1–8: known at the entry) |
|---|---|---|---|
| 1 | Time and activity | partial | sb_london; last 60 min 0.244 ADR = busy (2.28×); NFP at 08:30 the same day |
| 2 | Bias / narrative | partial | weekly, 4H, 1H bear; daily bull; read side bull (counter-weekly) does not match |
| 3 | Dealing range | fail | 0.309 of the daily range = discount for a short |
| 4 | POI / array | partial | the POI (4h bearish FVG from 3898.86) starts 2 points above the limit, so the entry is under the array, not in it; the entry is inside the 1w bullish volume imbalance 3891.37–3897.39; trigger gap 0.98 points |
| 5 | Liquidity before | partial | only sellside taken before (Asia low 21:15, 1d swing low 3885.03 at 01:40) — with the trade, not against it |
| 6 | Trigger | partial | 1-point FVG; the fill is a V-return three minutes after the low |
| 7 | Stop | partial | 0.004 ADR beyond the last-4h high 3901.14 — on the pool; risk 0.077 ADR |
| 8 | Targets | pass | TP1 3886.90 in front of the 1h swing low 3882.39, 1.2 points inside the top of the 1d bullish FVG 3862.80–3888.10; R:R 2.22 |
| 9 | Management | pass | half at TP1 03:17, runner out at entry 03:28: +1.11 R |
| 10 | Attribution | partial | mixed process; win by two thin touches |

## The late fill
- Decided 03:00, filled 03:08: **8 min** wait. Risk 4.5 points = 0.077 ADR.
- Limit depth at the decision: the decision bar closed **0.44 R** away from the limit. Run after that, beyond the decision close: 1.5 R.
- Run before the fill, measured from the entry (what the option measures): **1.94 R = 8.72 points = 0.149 ADR**, extreme at 03:05 (5 min after the decision; 3 min from the extreme back to the fill). It covered 0.87 of the distance to TP1.
- Pools: TP1 NOT taken: run low 3888.17, 1.3 points short of TP1 3886.90; the last-60-min low 3885.66 untouched. The run did go into the 1d bullish FVG 3862.80–3888.10 top and bounce.
- At the fill: borderline. A real run after the decision (1.50 R past the decision close, 0.149 ADR), a bounce off the top of a daily bullish FVG, and a V-return with two bullish 1m gaps. Structure intact (3901.14 untouched), TP untaken — so not stale by the definitions used here.
- **Class: ordinary retrace**

## Why it won
The return stalled exactly at the limit (3897.4 at 03:08, 3897.7 at 03:10 — the fill by 0.5–0.8 points, MAE 0.18 R) and the range repeated: 3886.7 at 03:17, **TP1 by 0.2 points**. Then back to entry (03:28) and, after NFP, up to 3939.80.

## What the market did (hindsight — lessons to test, not blame)
- Both the fill (0.5–0.8 points) and TP1 (0.2 points) are inside one or two ES ticks plus spread on a CFD feed: on futures this could be no fill, or a fill without TP1.
- Asia high 3906.03 traded at 04:29 (−2 R); the day's high 3939.80 at 08:31; TP1 again at 09:43.

## Would a better cancel rule have caught it?
An ADR rule (0.149, second largest) or "run past the decision close ≥ 1 R" cancels it and gives up +2.15 R (engine). On futures-realistic fills the trade may not exist, so the lost R is uncertain.

## Verdict
**Lucky win** — discount short into a daily bullish FVG on NFP morning, paid by a 0.2-point touch.

## For the engine
- Fill/TP audit with a tolerance of 1 tick + spread on both the limit and TP1 for dropped trades; report R with marginal fills removed and marginal TP1s turned into runner/stop outcomes.

*One trade from a batch of 15: a lead, not evidence.*
