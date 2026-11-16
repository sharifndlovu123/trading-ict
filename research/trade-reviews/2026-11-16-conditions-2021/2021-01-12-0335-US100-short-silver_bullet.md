# US100 short — Tue 12 Jan 2021 03:35 NY · engine -1.03 R (stop) · sheet -1.00 R · day-only -1.00 R
Engine silver_bullet trade, first run on 2021 (`research/preregistered-conditions-2021.md`). Facts: `research/trade-reviews/sheets/2026-11-16-conditions-2021/2021-01-12-0335-US100-short-silver_bullet.md`. Entry 12942.21 · stop 12959.25 · TP1 12920.87 (5m swing low, 1.25 R) · final 12897.11 (Asia low) · risk 17.0 pts = 0.089 ADR · ADR 191.78 · window sb_london · POI "leg ran asia_high" · engine FVG 1.0 pt · decided 03:25, filled 03:35, stopped 04:24.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london inside the London killzone; last hour normal (0.15 ADR, 0.83×); no news near (JOLTS 10:00 is medium) |
| 2 | Bias / narrative | partial | weekly, daily and 4H bull; only the 1H is bear (since 11 Jan 15:00). The read calls it a lower-TF pullback; the target is near (Asia low 0.22 ADR) |
| 3 | Dealing range | pass | 0.705 of the 4h range 12499.82–13127.09: premium, in the OTE |
| 4 | POI / array | fail | no array at the entry: the POI is "leg ran asia_high" and the engine FVG is 1.0 pt (0.005 ADR). The 1h bearish VI + FVG 12971.11–12988.74 sat 0.15 ADR above, untouched |
| 5 | Liquidity before | pass | Asia high 12954.19 and 1h swing high 12955.01 taken at 03:11 |
| 6 | Trigger | partial | the 03:15 15m candle closed −0.10 ADR after the sweep; nothing else. Limit at a 1-pt gap |
| 7 | Stop | fail | 12959.25 is 0.001 ADR beyond the session high 12959.00: on the pool, 0.06 ADR under the 1h bearish FVG |
| 8 | Targets | pass | TP1 5m swing low 12920.87, 1.25 R, no pool in front; final = Asia low |
| 9 | Management | n/a | stopped 04:24 |
| 10 | Attribution | fail | no area, stop on the pool: the lesson |

## Market conditions
CSV (known before the day): **consolidating**, **bull** backdrop, **low** volatility (0.63× its 1-year median), efficiency 0.274, scheduled high-impact news: none. Sheet: weekly/daily/4H bull, 1H bear; activity normal; no news near; CPI the next morning. The day (1m bars): London high 12969.21 at 04:49, low 12778.90 at 12:15, range 0.99 ADR, net −0.07 ADR, RTH closed mid-range. A two-sided **range day**.

## Why it lost / why it won
**Lost: sold before the area, stop on the session high.** The Asia-high run had not reached the 1h bearish FVG 12971.68–12988.74. Price went 10 pts further (12969.21, 04:49), took the session high and the stop, tagged the volume imbalance under that FVG and then fell 0.99 ADR. The engine's wide-stop counterfactual also lost (−1.02 R): the level was beyond that too.

## What the market did (hindsight)
- stopped, then TP1 traded at 08:25; Asia low, PDL and the 1h swing low all went at 08:57; +9.6 R in favour by 12:15
- MFE before the stop 0.73 R

## Price we should have looked at
12969.21 (04:49): **0.141 ADR above the entry, 0.052 ADR beyond the stop**. Known levels there: 1h bearish VI 12971.11–12971.22 and 1h bearish FVG 12971.68–12988.74. Known at the entry.

## Would Sharif take it?
**false** — No. The higher timeframes are bull and the bearish area (1h FVG 12971–12989) was not reached; one 15m candle down is not momentum. He would wait for that FVG, or buy the pullback into the 1d bullish FVG 12852–12928.

## Realism
Decision 03:25, fill 03:35 (bar high 12943.40, 1.2 pts through). Sheet price = close of 03:34. FVG 1.0 pt = 4 NQ ticks.

## Verdict
**lesson loss** — most useful change: sell from the array the run is going to, not from under it.

## For the engine
- SB shorts with an untouched opposing-run array (1h/4h FVG) within 0.2 ADR beyond the stop: split filled trades by "array beyond the stop: yes/no" on 2022–24.
- One trade is a lead, not evidence. 2021 is now used for this model; any rule goes in-sample (2022–24) first, then a new pre-registration.
