# US30 long — Mon 14 Mar 2022 14:57 NY · +0.57 R (50% at TP1, runner out at entry overnight) · day-only +0.80 R

Engine silver-bullet trade, in-sample. Fact sheet: `../sheets/2026-11-16-30-trades/2022-03-14-1457-US30-long-silver_bullet.md`.

## What they tried to do
PM silver bullet long after the sellside run (PDL 32912.50 at 13:36, 4h swing low 32820.21 at 14:24) into the top of the 1h FVG 32612.76–32820.60. Entry 32919.71, stop 32815.03 (under the session low 32815.28), TP1 33038.78, runner to PDH 33704.10. A 1H pullback long inside a weekly / daily / 4H bear.

## What happened
MAE −0.35 R. TP1 only at 18:36 (after the 16:55 flat time), runner stopped at entry 21:35. Next morning 05:08 price made 32684.08, then ran to PDH (Wed 02:43) and +11 R.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_pm / ny_pm_kz, 14:57; activity normal (0.68×, on the quiet side) |
| 2 | Bias / narrative | partial | read ltf_pullback, side bear; long ≠ read. 1H bull is the lower-TF reason, TP1 0.16 ADR away |
| 3 | Dealing range | pass | 0.162 of the 4h range 32815.28–33460.00 = discount |
| 4 | POI / array | partial | entry 99 pts above the POI's top 32820.60; a 4h bearish FVG 32942.77–32967.73 and 1h bearish FVG 32942.77–33030.74 start 23 pts above the entry |
| 5 | Liquidity before | pass | sellside PDL 32912.50 (13:36) and 4h swing low 32820.21 (14:24) taken |
| 6 | Trigger | pass | proxy: entry after the raid and reclaim of PDL; MAE only −0.35 R |
| 7 | Stop | partial | 0.25 pts beyond the session low 32815.28 (at the liquidity); inside the top 6 pts of the POI, not beyond it |
| 8 | Targets | partial | R:R 1.14; TP1 33038.78 is just past the 1h bearish FVG stack 32942.77–33030.74, so price had to clear the whole stack first |
| 9 | Management | partial | partial at TP1, stop to entry; the overnight hold gave back (day-only +0.80 R > +0.57 R) |
| 10 | Attribution | pass | acceptable process + small win |

Step 6 is a proxy. Step 7 "at the liquidity" is by construction for this model.

## Price we should have looked at
- **The turn on the sheet** (32684.08, Tue 05:08) came 14 h later in the next London session: a different swing, after this trade was closed. The trade's own turn was the 14:24 session low 32815.28 (the raid of the 4h swing low 32820.21 at the top of the POI): known, and inside our stop.
- **The later low, known at entry?** Yes, although the sheet says "none on the map". 32684.08 is inside the trade's own POI, the 1h FVG 32612.76–32820.60 (CE 32716.68), and inside the 1M FVG 32081.24–32963.30 and the body of the 1d bullish OB 32587.78–32739.74 from the read. It is 0.308 ADR below our entry and 0.171 ADR beyond our stop.
- **Where to price it:** the stop only reached the POI's top edge. A stop below the POI (32612.76) would have been 0.40 ADR; the alternative is a limit at the POI's CE 32716.68 with the stop under the 1h swing low 32632.80.
- **Target:** TP1 was inside the first opposing stack; price needed 3.5 h to get there. The real draw was PDH 33704.10 (our TP2), reached 36 h later.

## What they missed / should have seen (known at the entry)
- The first bearish arrays started 23 pts above the fill and covered the whole path to TP1.
- The stop protected 6 pts of a 208-pt POI.

## What the market did (hindsight — lessons to test, not blame)
- Runner stopped at entry, then TP1 again at 22:36 and +11 R; the deeper POI fill came the next morning.

## Verdict
**earned win** (small). The idea and the pool were right; day-only management paid more than the overnight runner.

## For the engine
- Day-only exit on silver-bullet runners; and test the entry at the POI's CE instead of the first FVG above it when the stop would otherwise sit inside the POI.
