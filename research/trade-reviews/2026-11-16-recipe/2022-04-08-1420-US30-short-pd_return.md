# US30 short — Fri 08 Apr 2022 14:20 NY · engine +1.95 R (tp1) · sheet +1.65 R · day-only +1.65 R
Engine pd_return trade, "full recipe" variant (1h/4h FVG to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop beyond the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows). Facts: `research/trade-reviews/sheets/2026-11-16-recipe/2022-04-08-1420-US30-short-pd_return.md`.

## What they tried to do
Weekly and 4H bear. After the morning sweep of the previous week low, price rallied to 34915.79 (4h swing high, under the 1d bearish FVG 34903.10–35053.29, inside the 1w bearish FVG from 34816.76). A 15m bearish gap formed, limit 34834.79, stop 34915.79, TP1 34675.24 (1.97 R), runner to the previous day low 34186.25.

## What happened
Filled 14:20, high 34847.80 a minute later (MAE −0.16 R), TP1 on the 15:59 close; the runner was flat at 16:14 ≈ 34726.80.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_pm_kz + sb_pm; activity normal but slow (0.146 ADR, 0.61× normal) |
| 2 | Bias / narrative | partial | W and 4H bear; D and 1H bull; the read says counter-weekly bull → side matches the read: False |
| 3 | Dealing range | pass | 0.82 of the daily range = premium |
| 4 | POI / array | partial | the engine's 1h FVG is not among the sheet's arrays; the entry is at the low edge of the 1w bearish FVG 34816.76–35637.27, under the 1d bearish FVG |
| 5 | Liquidity before | pass | buyside taken 10:51–10:52 (1h high, London high) after the previous week low sweep at 09:40 |
| 6 | Trigger | partial | 15m gap in a slow hour (net 0.058 ADR) |
| 7 | Stop | partial | stop on the session high / 4h swing high 34915.79, with 1h equal highs 34918.50 three points above |
| 8 | Targets | partial | TP1 34675.24 is not a pool on the sheet's map (a 5m/15m swing); 1.97 R; 4h and 1h bullish FVGs 34643–34797 in the way |
| 9 | Management | pass | 50% at TP1, flat at the close |
| 10 | Attribution | pass | mostly sound process + win = earned |

## What they missed / should have seen (known at the entry)
- 1h equal highs 34918.50 sat 3 points above the stop: untaken buyside right on it.
- The path to TP1 ran through a 4h bullish FVG 34741.80–34797.30 and a 1h bullish FVG 34643.30–34782.76.

## What the market did (hindsight — lessons to test, not blame)
- Turned 0.025 ADR above the entry; reached TP1 on the last minute of the session; no pools taken after.

## Does this look like Sharif's recipe?
- **(a) At a 1h/4h area, in the right half?** In the right half (premium 0.82) and at a weekly/daily bearish area. The sheet cannot confirm the 1h FVG itself (not listed).
- **(b) With the current momentum?** Split. 4H and weekly bear; 1H bull, and the day's move since 09:40 was up into the area.
- **(c) After a real displacement?** Not a strong one: slow hour (0.61× normal), range 0.146 ADR, risk 0.155 ADR.
- **(d) What Sharif would most likely say:** "Short is nice — premium, weekly gap. Mind the equal highs above your stop."

## Price we should have looked at
34847.80 at 14:21 = our entry (0.025 ADR above it, 0.13 ADR inside the stop). Known: the low edge of the 1w bearish FVG 34816.76.

## Verdict
**earned win** — most useful change: stop above the 1h equal highs 34918.50, not under them.

## For the engine
- Sheet/tooling: print the POI's own bounds on the fact sheet; the 1h area could not be checked here. (One trade is a lead, not evidence: in-sample test first, pre-registration before any default.)
