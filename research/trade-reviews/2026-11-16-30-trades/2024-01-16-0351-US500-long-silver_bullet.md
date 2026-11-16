# US500 long — Tue 16 Jan 2024 03:51 NY · +1.81 R (TP1 + TP2) · day-only +1.81 R

_Sources: the fact sheet in `research/trade-reviews/sheets/2026-11-16-30-trades/` (same filename). Lines marked (1m bars) are a same-day high/low lookup on the Dukascopy bars, entry → 16:55 NY — hindsight, like the sheet's turn line. One trade is a lead, not evidence._

## What they tried to do
Silver bullet long in the London SB hour: weekly/daily/4H bull with a 1H pullback, Asia low 4762.97 and the 4h swing low 4758.02 taken, entry 4757.73 just above the 1h FVG 4745.90–4754.94. Stop 4751.71, TP1 the 1h swing high 4766.03, TP2 the Asia high 4771.22.

## What happened
Filled 03:51, MAE -1.0 R (the session low was retested to within a tick of the stop), TP1 07:38, TP2 08:40. Price went on to the equal highs 4779.28 (10:40), high 4782.20; lows 4750.37 at 09:51 and 4746.67 at 14:19.

## Checklist
| # | Step | Grade | Evidence (known at entry for 1–8) |
|---|---|---|---|
| 1 | Time and activity | pass | London SB hour, busy (2.36×), no news |
| 2 | Bias / narrative | pass | Read = lower-TF pullback, side bull; side matches |
| 3 | Dealing range | partial | 0.645 of the 4h range (premium for a long); the pullback is 0.35, EQ 4739.40 not reached |
| 4 | POI / array | partial | POI 1h FVG 4745.90–4754.94; entry 2.8 pts above it, in the 4h IFVG 4754.17–4767.11 |
| 5 | Liquidity before | pass | Asia low 4762.97 (00:58) and 4h swing low 4758.02 (03:01) taken |
| 6 | Trigger | pass | FVG in the SB hour after the sweep |
| 7 | Stop | fail | 4751.71 = 0.006 ADR under the session low 4751.96 and 0.7 pts ABOVE the 1d bullish IFVG 4747.31–4751.00 — in front of the array, not beyond it |
| 8 | Targets | pass | TP1 on the 1h swing high, TP2 on the Asia high, R:R 1.38; nothing in the way |
| 9 | Management | pass | Half at TP1, rest at TP2 |
| 10 | Attribution | pass | Good read; the stop survived by a tick |

## What they missed / should have seen (known at the entry)
- The 1d bullish IFVG 4747.31–4751.00 started 0.7 pts under the stop: the stop was in front of the HTF array that should have defended the trade.
- Both TPs on the pools exactly (both filled this time).

## Price we should have looked at
- **Stop level:** under the 1d bullish IFVG low 4747.31 (0.10 ADR below our stop). Known at entry: yes. MAE before the exit was -1.0 R; the later lows 4750.37 (09:51, sheet: 0.031 ADR beyond our stop) and 4746.67 (14:19, 1m bars) were both at that IFVG.
- **Entry level:** the POI / 4h IFVG 4748.85–4755.10, e.g. 4754.9 with the stop at 4746.5: risk 0.19 ADR, TP1 +1.3 R, equal highs +2.9 R.
- **Lucky or right?** Right idea and levels, lucky on the stop (within a tick).
- **Targets:** TP2 Asia high 4771.22 = +2.24 R; price took the 1h equal highs 4779.28 (+3.58 R) two hours later and made 4782.20 (+4.06 R). PDH 4788.73 was not reached. About 1.8 R left on the second half.
- **The sheet's turn line** (4750.37 at 09:51) is after both TPs: the second leg's low, same known level.

## What the market did (hindsight — lessons to test, not blame)
- After TP2: one more low into the 1d IFVG, then the equal highs.

## Verdict
**earned win** — Put the stop beyond the 1d IFVG it was leaning on; let the second half run to the 1h equal highs.

## For the engine
- New `stop_mode` 'beyond_array': if an HTF array in our favour starts ≤ 0.05 ADR beyond the stop, move the stop past its far edge and re-check R:R. In-sample first; pre-registered on 2024-07+ before any default.
- Runner target = the next pool after TP2 when side = read (test on silver bullet). In-sample first; pre-registered on 2024-07+ before any default.
