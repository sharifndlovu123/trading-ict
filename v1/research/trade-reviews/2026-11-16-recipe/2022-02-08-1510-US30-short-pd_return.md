# US30 short — Tue 08 Feb 2022 15:10 NY · engine −1.02 R (stop) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, "full recipe" variant (1h/4h FVG to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop beyond the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows). Facts: `research/trade-reviews/sheets/2026-11-16-recipe/2022-02-08-1510-US30-short-pd_return.md`.

## What they tried to do
Daily bear. Price reached the 4h bearish FVG 35443.27–35470.01 to its 50% (session high 35465.30), a 15m bearish gap formed, limit 35378.77, stop on the session high, TP1 35275.75 (1.19 R, just past the 1h swing low 35280.21), runner to the Asia low 35055.20.

## What happened
Filled 15:10 and stopped 15:15. Price kept rising: 4h swing high 35606.30, previous week high 35687.77, and 35858.57 by Thu 08:07 (CPI). TP1 traded on Thu 14:15, two days later.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_pm_kz + sb_late, activity normal (0.25 ADR, 1.02×); 15:10 is late in the window |
| 2 | Bias / narrative | partial | D bear and side matches the read, but 4H bull since 31 Jan and 1H bull since 11:00 that day |
| 3 | Dealing range | partial | 0.587 of the daily range = premium, but only just above EQ 35049; the OTE starts at 35506 |
| 4 | POI / array | pass | 4h bearish FVG 35443.27–35470.01 reached to its 50% |
| 5 | Liquidity before | pass | buyside taken 11:00–11:40: London high, PDH 35329.29, 4h equal highs, 1h swing high |
| 6 | Trigger | fail | no displacement down on the sheet: normal activity, risk 0.128 ADR, stopped in 5 minutes |
| 7 | Stop | fail | stop on the session high 35465.30 (sits at the liquidity) with 4h high 35606.30 and 1h equal highs 35611.50 above |
| 8 | Targets | partial | TP1 just past the 1h swing low (not in front); 4h bullish FVG 35227.76–35280.21 and 1h bullish FVG 35244.80–35357.72 between entry and TP1 |
| 9 | Management | pass | day-only, full stop |
| 10 | Attribution | fail | against the 1H/4H wave with no displacement + loss = the lesson |

## What they missed / should have seen (known at the entry)
- 1H had turned bull at 11:00 and four buyside pools were taken in 40 minutes: the momentum was up.
- A 1h bullish FVG 35244.80–35357.72 started 21 points under the entry.
- Better sell areas were known and above: 1d IFVG 35527.80–35744.23, the OTE from 35506, the previous week high 35687.77.

## What the market did (hindsight — lessons to test, not blame)
- Stopped, then TP1 traded Thu 14:15 — but only after a 0.71 ADR run against us.
- Buyside taken next: 4h high (Wed 00:05), 1h equal highs, previous week high (Wed 08:07).

## Does this look like Sharif's recipe?
- **(a) At a 1h/4h area, in the right half?** Yes on paper: 4h bearish FVG reached to its 50%, premium (0.587). But it is the shallow end of the premium, below the OTE.
- **(b) With the current momentum?** Against. 1H bull since 11:00, 4H bull since 31 Jan, buyside run 11:00–11:40.
- **(c) After a real displacement?** No. Normal activity, risk 0.128 ADR: a small 15m gap against a rising market.
- **(d) What Sharif would most likely say:** "Wrong side for now and too early: momentum is buying. Wait for the daily area above (35527+)."

## Price we should have looked at
The up-leg ended at 35858.57 on Thu 08:07 (CPI, a later swing), 0.711 ADR above the entry and 0.583 ADR beyond the stop, at the 1d bearish IFVG 35782.27–35874.25 (known at the entry). Nearest known sell area on the way: 1d IFVG 35527.80–35744.23, 0.22–0.54 ADR above the entry.

## Verdict
**lesson loss** — most useful change: no short while 1H and 4H are bull and buyside is being taken; wait for the daily area.

## For the engine
- Same `side_structure` flag as 03 Jan; plus require the hour before the trigger to be at least 'busy' (`min_activity`) for PM entries. (One trade is a lead, not evidence: in-sample test first, pre-registration before any default.)
