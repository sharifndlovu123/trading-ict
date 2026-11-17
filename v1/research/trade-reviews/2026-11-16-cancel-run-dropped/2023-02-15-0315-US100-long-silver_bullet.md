# US100 long — Wed 15 Feb 2023 03:15 NY · silver_bullet · engine +2.53 R (tp1) · own management +4.65 R · day-only +4.65 R

Batch: cancel-run-dropped (a late fill the `cancel_run_r=1` option would have cancelled). Sheet: `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2023-02-15-0315-US100-long-silver_bullet.md`.

**Trade in one line:** silver bullet long limit 12494.38, stop 12485.28 (0.3 under three equal 1m lows 12485.6–12485.8), TP1 12517.90 (5m swing high), TP2 Asia high 12555.42.

## Checklist
| # | Step | Grade | Evidence (steps 1–8: known at the entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london; last 60 min 0.108 ADR = normal (1.08×); retail sales 08:30, five hours away |
| 2 | Bias / narrative | partial | daily and 1H bull; weekly and 4H bear; read counter-weekly bull matches |
| 3 | Dealing range | fail | 0.82 of the daily range = premium for a long |
| 4 | POI / array | partial | the POI (1h FVG 12467.60–12486.11) is below the entry; the entry is inside the 1w bearish volume imbalance 12483.90–12599.58 |
| 5 | Liquidity before | pass | sellside Asia low 12509.68 taken (21:15); London lows 12485.6 / 12485.7 / 12485.8 at 03:01–03:05 |
| 6 | Trigger | partial | 5-point FVG; 1 R = 9.1 points |
| 7 | Stop | fail | 0.3 under three equal lows and SHORT of the 1h swing low 12483.82 by 0.005 ADR; risk 0.030 ADR |
| 8 | Targets | pass | TP1 5m swing high 12517.90 in front of the 1h swing high 12524.20; R:R 2.58; runner to the Asia high |
| 9 | Management | pass | half at TP1 03:31, half at the Asia high 07:11: +4.65 R, same day |
| 10 | Attribution | partial | weak stop, premium; win |

## The late fill
- Decided 03:06, filled 03:15: **9 min** wait. Risk 9.1 points = 0.03 ADR.
- Limit depth at the decision: the decision bar closed **0.47 R** away from the limit. Run after that, beyond the decision close: 0.98 R.
- Run before the fill, measured from the entry (what the option measures): **1.45 R = 13.22 points = 0.044 ADR**, extreme at 03:13 (7 min after the decision; 2 min from the extreme back to the fill). It covered 0.56 of the distance to TP1.
- Pools: nothing taken: run high 12507.6, TP1 12517.9 (0.56 of the way).
- At the fill: valid: 9 minutes, equal lows intact, target resting. This is one of the few with a real run after the decision (0.98 R past the decision close).
- **Class: ordinary retrace**

## Why it won
The fill bar (03:15) went 8 points through the limit to 12486.4 and the next to 12486.3 — 0.88 R against, **1.0 point above the stop** and 0.5 above the equal lows — and London then lifted it: TP1 03:31, 1h swing high, Asia high 07:11.

## What the market did (hindsight — lessons to test, not blame)
- The equal lows and the 1h swing low 12483.82 were taken at 10:08–10:12 (12478.22, 0.024 ADR beyond the stop) before the day's rally to the PDH. On a different minute this is the "stopped, then target" trade.

## Would a better cancel rule have caught it?
None should, and none of the candidates does (0.044 ADR, 9 min, no pool). Note what it shows: the difference between this +2.5 R and the losers 01-04 / 11-07 is one point of stop.

## Verdict
**Lucky win** — stop under equal lows survived by a point.

## For the engine
- Near-miss audit: on dropped and kept trades, count winners whose MAE came within 0.15 R of the stop and losers stopped by less than 0.15 R past it; if both are frequent the result is stop noise.

*One trade from a batch of 15: a lead, not evidence.*
