# US30 long — Wed 18 Oct 2023 10:08 NY · -1.00 R (stopped 10:36) · day-only -1.00 R

_Sources: the fact sheet in `research/trade-reviews/sheets/2026-11-16-30-trades/` (same filename). Lines marked (1m bars) are a same-day high/low lookup on the Dukascopy bars, entry → 16:55 NY — hindsight, like the sheet's turn line. One trade is a lead, not evidence._

## What they tried to do
Silver bullet long in the 10–11 hour: sellside taken (1h low, Asia low 06:21, 4h swing low 33849.29 at 09:53), entry 33905.75 for the London high 33993.76 — the 4H pullback leg inside a bear weekly/daily. POI 1h FVG 33798.00–33844.76. Stop 33826.96, TP1 33992.74 (R:R 1.1), TP2 PDH 34148.24.

## What happened
Filled 10:08, low 33850.29 at 10:11, high 33965.30 at 10:20 (0.76 R), stopped 10:36. PDL 33808.09 went at 10:42; day low 33591.21.

## Checklist
| # | Step | Grade | Evidence (known at entry for 1–8) |
|---|---|---|---|
| 1 | Time and activity | pass | SB AM hour + 09:50 macro, normal (1.09×), no news |
| 2 | Bias / narrative | partial | Read = lower-TF pullback, side bear; the long rides the 4H/1H pullback to the London high, but price is inside the 1w FVG 33720.45–33943.75 where the read expects bear to resume |
| 3 | Dealing range | partial | 0.495 of the daily range = its EQ (33915.81): no discount |
| 4 | POI / array | partial | POI 1h FVG 33798.00–33844.76; the entry is 61 pts (0.15 ADR) above its top |
| 5 | Liquidity before | pass | Three sellside pools taken, the last (4h swing low 33849.29) 15 min before |
| 6 | Trigger | pass | FVG in the SB hour after the sweep |
| 7 | Stop | fail | 33826.96 = 0.001 ADR under the session low 33827.21, inside the POI and the 4h FVG 33791.80–33838.71, with the PDL 33808.09 0.045 ADR below it |
| 8 | Targets | fail | TP1 front-runs the London high by 1 pt (good) but the 1h bearish FVG 33951.79–34016.71 and 1d bearish IFVG 33964.00–34215.20 sit between entry and TP1; R:R 1.1 |
| 9 | Management | n/a | Stopped |
| 10 | Attribution | fail | Entry too high, target through two bearish arrays |

## What they missed / should have seen (known at the entry)
- Two bearish arrays (1h FVG from 33951.79, 1d IFVG from 33964.00) 0.11–0.14 ADR above the entry, in front of TP1. The sheet's 'pools before TP1: none' counts pools only.
- Entry 0.15 ADR above the POI it was built on.
- Stop on the session low with the PDL 0.045 ADR under it.

## Price we should have looked at
- **Entry level:** the swept 4h swing low 33849.29 / POI top 33844.76. The low was 33850.29 at 10:11 — 0.134 ADR below our entry, inside our stop. Known at entry: yes.
- **Target level:** the 1h bearish FVG edge 33951.79 / 1d bearish IFVG edge 33964.00. High 33965.30 (1m bars) = 1.3 pts into the 1d IFVG, then the turn down. Known at entry: yes.
- **What the two prices do:** from our entry, 33950 is only 0.56 R → no trade. From 33850 with the same stop (risk 23 pts), 33950 is +4.3 R.
- **Stop level:** under the PDL 33808.09 / 4h FVG low 33791.80 (0.11 ADR lower) — it would still have lost; the bear leg resumed.

## What the market did (hindsight — lessons to test, not blame)
- Stopped, PDL six minutes later, then 1.0 ADR lower by 15:48: the read's side won the day.

## Verdict
**lesson loss** — Count opposing arrays, not only pools, between entry and TP1; here that turns the plan into R:R 0.56 → skip, or buy the POI edge.

## For the engine
- `tp1_front_array` (new): cap TP1 in front of the nearest opposing 1h/4h/1d array edge; skip if R:R < 1. In-sample first; pre-registered on 2024-07+ before any default.
- Silver bullet `entry_level`: test 'poi' (limit at the HTF POI edge) vs the current LTF FVG when the FVG is > 0.10 ADR from the POI. In-sample first; pre-registered on 2024-07+ before any default.
