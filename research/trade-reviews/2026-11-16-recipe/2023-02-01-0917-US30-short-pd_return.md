# US30 short — Wed 01 Feb 2023 09:17 NY · −1.00 R (stopped 14:41, FOMC) · day-only −1.00 R · engine −1.03 R

Engine pd_return trade, full-recipe variant, in-sample. Fact sheet: `../sheets/2026-11-16-recipe/2023-02-01-0917-US30-short-pd_return.md`. The sheet does not print the POI's bounds, the time the area was reached, or the 15m gap: the POI is inferred from the arrays and the stop (= the reaction extreme); the 15m gap and its displacement candle were measured for this review from the 1m bars before the entry (known at the entry, but not on the sheet).

## What they tried to do
A short in the NY AM killzone on FOMC day. Area (inferred): the 1h bearish FVG 33976.09–33998.29, reached to its 50% (33987.2) by the 08:15–08:30 high 33988.10. 15m bearish FVG 33915.05–33933.58 closed at 09:15; limit at its bottom edge 33915.05, stop 33988.10, TP1 = previous day low 33511.53 (5.5 R, 100%). Daily / 4H / 1H are all bull; only the weekly is bear.

## What happened
Filled 09:17. Price went back up to 33975.0 at 09:53 (−0.82 R), then fell: 1h swing low 33759.27 (+2.13 R) at 10:50, 1h swing low 33659.80 (+3.49 R) at 14:32, MFE +4.7 R at 14:34. The FOMC press conference took it straight back: stopped 14:41, previous day high 14:46, previous week high 15:07.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz, activity normal (1.01×); FOMC statement 14:00 and press conference 14:30 inside the hold window (known in advance) |
| 2 | Bias / narrative | fail | read counter_weekly, side bull; Daily, 4H and 1H all bull; short ≠ read |
| 3 | Dealing range | pass | 0.716 of the 4h range 33266.24–34171.80 = premium, in the OTE |
| 4 | POI / array | partial | 1h bearish FVG 33976.09–33998.29 reached to its 50% (inferred); the entry is 61 pts (0.13 ADR) below it and 31 pts above the 4h bullish FVG 33818.80–33883.71 |
| 5 | Liquidity before | partial | only sellside taken (Asia low 03:28, 1h swing low 33883.71 at 09:06); no buyside raid; 1h swing high 33988.10 untaken |
| 6 | Trigger | partial | 15m gap 18.5 pts (0.041 ADR), displacement candle body 0.079 ADR; last hour net 0.059 ADR |
| 7 | Stop | fail | stop exactly on the 1h swing high / last-4h high 33988.10 (sits at the liquidity); London high 34030.10 and Asia high 34034.24 are 0.09–0.10 ADR beyond |
| 8 | Targets | fail | TP1 just past the previous day low, 5.52 R, 100%; five pools in front (1h swing lows 33759.27 and 33659.80 among them), none planned as a partial |
| 9 | Management | fail | no partial, held through FOMC: +4.7 R became −1 R |
| 10 | Attribution | fail | the short worked for 5 hours; the plan had nowhere to take it = the lesson |

## Does this look like Sharif's recipe?
- **(a) At a 1h / 4h area, in the right half?** Yes. The 1h bearish FVG was reached to its 50% (inferred from the stop), and the range line says premium 0.716, in the OTE of the 4h range. The entry itself is 0.13 ADR below the area.
- **(b) With the current momentum?** Against the structure: 1H bull since 31 Jan 15:00, 4H bull since 26 Jan, Daily bull. With the morning's flow: three sellside pools taken in the 6 h before (the last at 09:06). Activity normal, net move 0.059 ADR.
- **(c) After a real displacement?** Modest. Range 0.196 ADR in the hour (normal), 15m gap 0.041 ADR, displacement body 0.079 ADR, risk 0.16 ADR. Not chop, not a strong displacement.
- **(d) What Sharif would most likely say:** "Short from premium is nice, but if we took our partials we would have won here" — and he would not hold a 100% position into FOMC.

## Price we should have looked at
- **The turn:** 33975.0 at 09:53 (36 min after the entry, the same swing) = 0.132 ADR above our entry, 0.029 ADR inside our stop. From there 0.89 ADR our way.
- **Level there, known at entry:** yes — the bottom edge of the 1h bearish FVG 33976.09–33998.29 (the area itself, second visit), under the 1h swing high 33988.10.
- **Where to price it:** the area's edge 33976, not the 15m gap 61 pts below it. The stop held by 13 pts.

## What they missed / should have seen (known at the entry)
- FOMC at 14:00 / 14:30 was on the calendar; the only target was 5.5 R away.
- 1h swing lows at 33759.27 and 33659.80 sat between the entry and TP1 and were not targets.
- The side was against Daily, 4H and 1H.

## What the market did (hindsight — lessons to test, not blame)
- +2.13 R and +3.49 R pools were taken before the stop; MFE 4.7 R (0.8 R short of TP1).
- The FOMC move ran −5.94 R against within the window.

## Verdict
**lesson loss.** The entry was fine; the target list was not. A 50% partial at the first 1h swing low (+2.1 R) and flat before 14:00 turns this into a win.

## For the engine
- Add 1h / 4h swing pools to the TP1 candidates of `_targets` (today: the day's 5m/15m swings + Asia / previous day / previous week), keep the 50% partial; test with the existing `fomc_day` gate. In-sample first; pre-register before any default. One trade is a lead, not evidence.
