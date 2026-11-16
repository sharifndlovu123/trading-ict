# US100 long — Mon 02 Oct 2023 10:30 NY · +0.52 R (TP1 50%, rest at entry) · day-only +0.52 R · engine +1.03 R

Batch: cancel-run-dropped (late fills the `cancel_run_r=1` option would have dropped) · model silver_bullet · sheet `research/trade-reviews/sheets/2026-11-16-cancel-run-dropped/2023-10-02-1030-US100-long-silver_bullet.md`

## What they tried to do
Silver bullet AM, decided on the 10:00 ISM manufacturing candle (14756.54 → 14813.09): leg-start gap of 4.03 points, limit 14769.77, a wide stop at 14698.78 (71 points, 0.33 ADR), TP1 the 04:40 5m swing high 14843.57 (1.04 R), runner to the previous day high 14905.89. Long from the discount of the daily range against a daily bear read.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | partial | sb_am, but the decision candle is the 10:00 ISM release; last hour 0.658 ADR (1.42× normal) |
| 2 | Bias / narrative | fail | The read is bear (daily bear since 7 Aug, counter-weekly); the long is against it |
| 3 | Dealing range | pass | 0.247 of the daily range 14428.58–15811.90 = discount for a long |
| 4 | POI / array | partial | Named POI 1h FVG 14633.61–14725.38 is 44 points below the entry; the entry sits inside two 1d bearish IFVGs (14672.67–14766.27, 14745.77–14880.55) and the 1w bullish FVG 14672.67–14784.52 |
| 5 | Liquidity before | partial | Sellside 1h swing low 14780.10 taken at 05:47; the session low 14676.62 made inside the last hour |
| 6 | Trigger | partial | News-candle displacement, gap 4.03 points |
| 7 | Stop | partial | 71 points = 0.329 ADR, wide, yet still SHORT of the session low 14676.62 by 0.103 ADR |
| 8 | Targets | fail | TP1 14843.57 at 1.04 R; by the fill price had already traded 14840.99, 2.6 points from it; London high 14860.60 just beyond |
| 9 | Management | pass | 50% at TP1 11:15, rest out at entry 11:53; flat the same day |
| 10 | Attribution | fail | Against the read, on a news candle, after the target was nearly tagged: weak process + win |

## The late fill
Decided 10:00, filled 10:30 (30 min). The ISM spike ran to 14840.99 by 10:04: **71.22 points = 1.00 R = 0.330 ADR**, which is **96% of the way to TP1** (14843.57, missed by 2.6 points). Then 26 minutes of lower highs (14820.12 at 10:18, 14823.54 at 10:26) and lower lows (14775.51 at 10:14, 14773.36 at 10:22) until the fill: the whole news spike was given back. At the fill the 1m/5m structure pointed down and the scalp had already been delivered; only the wide stop and the pre-news low (14753.81) said the idea was alive.

Wait 30 min · run 1.00 R = 71.22 points = 0.330 ADR · 96% of the entry→TP1 distance · class: **stale: move already done**

## Why it won
The pullback ended at 14756.55 (10:31), 0.19 R under the entry, at the base of the news candle, and price went back up the same range: TP1 at 11:15, London high 14860.60 at 11:20, then down again (runner out at entry 11:53; −4.6 R the next day). It won because the stop was 0.33 ADR wide and the target was 1 R inside the range the news had just drawn: a range trade, not a fresh displacement.

## Would a better cancel rule have caught it?
Yes, every version catches it: ADR run (0.33), ≥ 80% of the TP1 distance (96%), a 30-minute limit, lower highs/lows before the fill. And it won. This is the counter-example to all of them: with a wide stop a full retrace of a spent move can still pay 1 R.

## What the market did (hindsight — lessons to test, not blame)
- Turn 14756.55 at 10:31; TP1 11:15; London high 11:20; previous day low 14660.73 taken Tuesday 10:15.
- The runner never had a chance: the day stayed inside the daily bearish IFVG 14745.77–14880.55.

## Verdict
**lucky win.** Stale by every test and against the read; paid by a wide stop and a 1 R target.

## For the engine
- Split every cancel-rule test by stop size in ADR: stale fills with a wide stop (≥ 0.15 ADR) may behave differently from stale fills with a noise-size stop. One trade is a lead, not evidence.
