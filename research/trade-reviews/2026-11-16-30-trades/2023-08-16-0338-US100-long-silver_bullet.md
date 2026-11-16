# US100 long — Wed 16 Aug 2023 03:38 NY · -1.00 R (stopped 05:42) · day-only -1.00 R

_Sources: the fact sheet in `research/trade-reviews/sheets/2026-11-16-30-trades/` (same filename). Lines marked (1m bars) are a same-day high/low lookup on the Dukascopy bars, entry → 16:55 NY — hindsight, like the sheet's turn line. One trade is a lead, not evidence._

## What they tried to do
Silver bullet long in the London SB hour: entry 15072.57 at the top of the 1h FVG 15021.80–15076.33, one TP (100%) at the PDH 15265.09 = 6.47 R. Stop 15042.82. Against the read: daily and 4H bear (counter-weekly leg).

## What happened
Filled 03:38, high 15096.61 (0.81 R) at 04:31, stopped 05:42. Then the whole sellside: 1h swing low 15023.12, Asia low, PDL 15011.74 (07:10–07:11), PWL 14969.61, 1d swing low 14952.82, PML 14919.72; day low 14865.71 at 16:00.

## Checklist
| # | Step | Grade | Evidence (known at entry for 1–8) |
|---|---|---|---|
| 1 | Time and activity | pass | London SB hour, normal (0.94×), no news |
| 2 | Bias / narrative | fail | Read = counter-weekly, side bear (daily + 4H bear); the long is against it |
| 3 | Dealing range | partial | 0.288 of the 4h range = discount for a long, but in a bear leg this is a 0.29 pullback where the read wants to sell |
| 4 | POI / array | fail | POI 1h bullish FVG 15021.80–15076.33 overlaps the 1h bearish FVG 15051.61–15074.36 and 1h bearish IFVG 15057.50–15127.21; entry at the session high 15076.80 |
| 5 | Liquidity before | fail | Only buyside taken (Asia high 15062.20 at 21:53) — the wrong side for a long; 15023.12 / 15014.12 / PDL 15011.74 untaken below |
| 6 | Trigger | partial | FVG in the SB hour, bought at its top edge |
| 7 | Stop | fail | 15042.82 is inside the POI (low 15021.80), 0.081 ADR short of the 1h swing low 15023.12, with the Asia low and PDL under that |
| 8 | Targets | fail | One TP at the PDH 15265.09, just past the 4h swing high 15260.70: 0.80 ADR and five pools away, through the 1d bearish IFVG 15138.30–15314.72 |
| 9 | Management | n/a | Stopped |
| 10 | Attribution | fail | Wrong side, wrong edge, no partial |

## What they missed / should have seen (known at the entry)
- Bought the session high after buyside was taken, into the bearish 1h FVG 15051.61–15074.36 the read listed as the first sell array.
- Three sellside pools 0.20–0.25 ADR below the entry, stop above them.
- TP 6.47 R away with no partial at the first pool (1h swing high 15143.20 = 2.4 R).

## Price we should have looked at
- **Level:** none for a long. The known level at our entry price was a sell level: session high 15076.80 with the 1h bearish FVG 15051.61–15074.36.
- **The sheet's turn line:** 15070.18 at 03:38 is the entry minute and a 0.89 R pop — not a turn. Price never turned our way: -7 R by 16:00 (1m bars).
- **If a long at all:** only after the sellside 15023.12–15011.74 (0.20–0.25 ADR below entry) was taken — it was, at 07:10–07:11, and price kept falling, so no long price existed that day.
- **Flag (PD-array audit):** a bullish and a bearish 1h FVG over the same prices (15021.80–15076.33 vs 15051.61–15074.36), and the POI is not in 'arrays near'.

## What the market did (hindsight — lessons to test, not blame)
- Every sellside pool on the map was taken within 11 h: the read's side was the trade.

## Verdict
**lesson loss** — No silver bullet against the read after the wrong side was swept; never one TP at 6.5 R.

## For the engine
- Silver bullet: require the sweep to be on the stop side (sellside for a long) — gate `sweep_side_required`. In-sample first; pre-registered on 2024-07+ before any default.
- `target_mode`: TP1 = the first pool with R:R ≥ 1 (here 15143.20), not the far draw. In-sample first; pre-registered on 2024-07+ before any default.
