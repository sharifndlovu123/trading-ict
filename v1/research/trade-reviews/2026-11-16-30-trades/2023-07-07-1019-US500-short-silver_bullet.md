# US500 short — Fri 07 Jul 2023 10:19 NY · -1.00 R (stopped 11:38) · day-only -1.00 R

_Sources: the fact sheet in `research/trade-reviews/sheets/2026-11-16-30-trades/` (same filename). Lines marked (1m bars) are a same-day high/low lookup on the Dukascopy bars, entry → 16:55 NY — hindsight, like the sheet's turn line. One trade is a lead, not evidence._

## What they tried to do
Silver bullet short in the 10–11 hour on NFP day: entry 4410.83 at the bottom edge of the 1h bearish FVG 4411.08–4424.12 (4h FVG 4411.66–4424.49), for the 4h swing low 4395.97 and PDL 4384.69. Stop 4416.23, TP1 4397.95. Against the read: every TF bull.

## What happened
Filled 10:19, MFE 1.65 R (low 4401.89), stopped 11:38. Price took 4418.02, 4430.12, 4433.78, topped at 4440.18 at 13:30, then fell to 4396.63 at 15:50 — TP1 traded after the stop.

## Checklist
| # | Step | Grade | Evidence (known at entry for 1–8) |
|---|---|---|---|
| 1 | Time and activity | partial | SB AM hour, activity normal (0.98×), NFP 109 min earlier |
| 2 | Bias / narrative | fail | Read aligned bull on all TFs; its next draw was the 4h swing high 4418.02, then PDH 4445.66 — the short is against it |
| 3 | Dealing range | partial | 0.517 of the 4h range = the EQ (4409.14) |
| 4 | POI / array | partial | 1h/4h bearish FVG 4411–4424, but price is inside the 1d bullish FVG 4398.44–4441.93 |
| 5 | Liquidity before | partial | Buyside 4410.91–4415.38 taken at 08:30–08:34 (NFP), then sellside at 09:02; the session high 4418.02 untaken |
| 6 | Trigger | partial | FVG in the SB hour, filled at the first (proximal) edge |
| 7 | Stop | fail | 4416.23 is inside the POI (top 4424.12) and 0.043 ADR short of the session / 4h swing high 4418.02 |
| 8 | Targets | pass | TP1 4397.95 front-runs the 4h swing low 4395.97, R:R 2.38, nothing in the way |
| 9 | Management | n/a | Stopped |
| 10 | Attribution | fail | Counter-read short priced at the EQ |

## What they missed / should have seen (known at the entry)
- The read's draw 4418.02 was 0.19 ADR above and untaken; the stop was under it.
- Stop inside our own FVG (4411.08–4424.12): the array had not failed when we were out.
- Price was inside the 1d bullish FVG up to 4441.93 — the counter-read short only makes sense at its top.

## Price we should have looked at
- **Level:** the top of the 1d bullish FVG 4441.93, with the 1h swing high 4443.37 and PDH 4445.66 just above. Known at entry: yes.
- **Distance:** turn 4440.18 at 13:30 (same day, 3 h later) = 0.70 ADR above our entry, 0.57 ADR beyond our stop; 1.75 pts under the FVG top.
- **From there:** 1.04 ADR down to 4396.63 (0.66 above the 4h swing low 4395.97 — the front-run TP1 filled, the pool did not trade).
- **Stop that fits:** above PDH 4445.66. A short at 4440 with that stop is about 0.15 ADR risk for roughly 6–7 R to TP1.

## What the market did (hindsight — lessons to test, not blame)
- Stopped, then TP1 at 15:50.
- TP1 in front of the pool was the right target price: the low was 4396.63, the pool 4395.97.

## Verdict
**lesson loss** — Against the read, wait for the read's own buyside (4418.02, then the 1d FVG top / PDH) before selling.

## For the engine
- Silver bullet: when side ≠ read, require the read's next draw on the stop side to be taken first (new flag `need_read_draw_taken`). In-sample first; pre-registered on 2024-07+ before any default.
- Stop beyond the far edge of the POI (`stop_mode` variant) instead of inside it. In-sample first; pre-registered on 2024-07+ before any default.
