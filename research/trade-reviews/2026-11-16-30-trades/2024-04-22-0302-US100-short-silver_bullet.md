# US100 short — Mon 22 Apr 2024 03:02 NY · +1.01 R (TP1, then stop at entry) · day-only +1.01 R

_Sources: the fact sheet in `research/trade-reviews/sheets/2026-11-16-30-trades/` (same filename). Lines marked (1m bars) are a same-day high/low lookup on the Dukascopy bars, entry → 16:55 NY — hindsight, like the sheet's turn line. One trade is a lead, not evidence._

## What they tried to do
Silver bullet short in the London SB hour: daily/4H/1H bear (counter-weekly), Asia high 17126.61 and a 1h swing high run at 01:33–01:40, entry 17153.68 at the bottom of the 4h bearish FVG 17147.20–17260.90. Stop 17161.95 (8 pts), TP1 17136.99 (2R), TP2 the Asia low 17056.78.

## What happened
Filled 03:02, MAE -0.19 R, TP1 at 03:10, the 1h swing low 17091.54 at 04:09 (+7.5 R), stop at entry 05:43. Second leg from 17187.67 at 09:50 took the Asia low at 10:26 (+11.7 R), low 17005.92.

## Checklist
| # | Step | Grade | Evidence (known at entry for 1–8) |
|---|---|---|---|
| 1 | Time and activity | pass | London SB hour, normal (1.07×), no news |
| 2 | Bias / narrative | pass | Read = counter-weekly, side bear; side matches (daily, 4H, 1H bear) |
| 3 | Dealing range | fail | 0.132 of the 4h range = discount for a short; the pullback is only 0.13 (EQ 17667.26) |
| 4 | POI / array | partial | Entry at the low of the 4h bearish FVG 17147.20–17260.90; the model's POI '1h FVG 17138.69–17272.21' (0.47 ADR wide) is not on the read's list |
| 5 | Liquidity before | pass | Asia high 17126.61 (01:33) and 1h swing high 17128.69 (01:40) taken |
| 6 | Trigger | pass | FVG in the SB hour after the sweep |
| 7 | Stop | partial | 17161.95 = 0.001 ADR over the 1h swing high 17161.70; risk 0.029 ADR (8.3 pts) |
| 8 | Targets | partial | TP1 = fixed 2R at 17136.99 (0.06 ADR away, not a pool); the first pool is the 1h swing low 17091.54 = 7.5 R; TP2 on the Asia low exactly |
| 9 | Management | partial | Stop to entry after a 17-pt TP1 took the second half out before TP2 traded |
| 10 | Attribution | pass | Good price, target too small |

## What they missed / should have seen (known at the entry)
- TP1 capped at 2R = 17 pts while the first pool was 0.21 ADR away (7.5 R).
- With an 8-pt risk, stop-to-entry after TP1 leaves the runner no room (out at 05:43, TP2 traded 10:26).

## Price we should have looked at
- **Level (the turn):** our entry area — the swept highs and the low edge of the 4h bearish FVG 17147.20; MAE 0.19 R (1.6 pts, 0.006 ADR), inside the stop. Known at entry: yes. Right price.
- **Target level we should have priced:** the 1h swing low 17091.54 (0.21 ADR) for TP1 — traded 04:09, +7.5 R on the half instead of +2 R. Then the Asia low 17056.78 (+11.7 R, 10:26); the PDL 16969.61 was not reached (low 17005.92, 1m bars).
- **The sheet's turn line:** 17187.67 at 09:50 is 7 h later, after our exit — the second leg's high, 0.12 ADR above our entry at the 1h swing high 17195.71 inside the same 4h FVG. A known level and a re-entry price, not this trade's turn.
- **Flag (PD-array audit):** POI '1h FVG 17138.69–17272.21' vs the read's 1h IFVG 17138.69–17188.42 and 4h FVG 17147.20–17260.90 — the POI's bounds look merged.

## What the market did (hindsight — lessons to test, not blame)
- +17.9 R available by 11:15; the next day price was 0.9 ADR higher.

## Verdict
**earned win** — With micro risk, TP1 belongs at the first pool, not at 2R.

## For the engine
- Silver bullet `tp1_cap_r=2.0` → test `None` (TP1 = first pool) when risk < 0.05 ADR. In-sample first; pre-registered on 2024-07+ before any default.
- `runner_stop`: test 'tp1'-trailing or the swept high instead of 'entry' for micro-risk trades. In-sample first; pre-registered on 2024-07+ before any default.
