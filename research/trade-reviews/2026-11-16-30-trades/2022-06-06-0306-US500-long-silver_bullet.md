# US500 long — Mon 06 Jun 2022 03:06 NY · −1.00 R (stopped 12:02 after +5.8 R open) · day-only −1.00 R

Engine silver-bullet trade, in-sample. Fact sheet: `../sheets/2026-11-16-30-trades/2022-06-06-0306-US500-long-silver_bullet.md`.

## What they tried to do
London silver bullet long from the 4h zone 4125.00–4149.14 after the Asia high run. Entry 4135.84, stop 4130.10, one target: PDH 4189.90, 100%, R:R 9.41. A 4H / 1H pullback long inside a weekly and daily bear.

## What happened
Price dipped to 4132.84 at 03:33 (−0.52 R), took the 1h swing highs 4143.20 (03:51) and 4162.60 (10:01), peaked near 4169 at 10:06 (+5.8 R), then came all the way back: stopped 12:02, 1h swing low 4125.83 at 12:04, PDL that night.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london / sweet spot, 03:06; activity normal (0.88×); no news |
| 2 | Bias / narrative | partial | read ltf_pullback, side bear; long ≠ read. 4H / 1H bull, but the near target the rule asks for was not used |
| 3 | Dealing range | fail | 0.653 of the 1d range 3810.24–4308.75 = premium, inside the bearish OTE 4119.32–4204.06 where the read sells |
| 4 | POI / array | partial | the model's POI 4125.00–4149.14 is the read's 4h bearish IFVG (same prices); 4h bearish FVG 4143.20–4157.54 starts 7 pts above the entry |
| 5 | Liquidity before | fail | only buyside taken (Asia high, EQH, 1h swing high 4135.50 at 03:04); no sellside raid before the long |
| 6 | Trigger | pass | proxy: MAE −0.52 R, then 6.3 R our way |
| 7 | Stop | partial | 4.3 pts (0.042 ADR) SHORT of the 1h swing low 4125.83; risk 0.056 ADR |
| 8 | Targets | fail | one TP at PDH, 0.52 ADR and four pools away (4143.20, 4162.60, 4183.85), "just past" the 4h swing high, through the whole bearish OTE; no partial |
| 9 | Management | fail | +5.8 R open with nothing banked and the stop never moved |
| 10 | Attribution | fail | good entry price, no exit price = the lesson |

Step 6 is a proxy.

## Price we should have looked at
- **The turn:** 4132.84 at 03:33, 0.029 ADR below the entry and inside the stop, at the 1h bullish FVG 4132.40–4133.05 / 1h volume imbalance 4134.04–4134.34 (known). The entry price was right.
- **The price we missed was the target.** The high (about 4169, +5.8 R, 0.33 ADR) was inside the read's sell arrays: 4h bearish IFVG 4155.70–4176.04 and 1h bearish IFVG 4161.20–4170.33, just past the 1h swing high 4162.60. All known at entry. PDH 4189.90 was another 0.20 ADR.
- **Where to price it:** TP1 in front of the 1h swing high 4162.60 (+4.6 R, 0.26 ADR) or at the 4h bearish FVG 4143.20–4157.54; only a runner for PDH.

## What they missed / should have seen (known at the entry)
- A counter-daily long in the bearish OTE with the read's sell arrays between entry and target.
- Four pools before the only TP.

## What the market did (hindsight — lessons to test, not blame)
- +5.8 R, then −10 R: the pullback ended in the daily OTE and the bear leg resumed.

## Verdict
**lesson loss.** The single most useful change: a first target at the nearest pool / opposing HTF array when the trade is against the read.

## For the engine
- Never 100% on one TP when R:R to it is above 3: force a TP1 at the nearest pool or opposing 4h+ array in front (new flag `tp1_front_array`; `tp1_cap_r` exists and is the simple version). Check why this plan has one TP (TP1 and TP2 both resolved to PDH?).
