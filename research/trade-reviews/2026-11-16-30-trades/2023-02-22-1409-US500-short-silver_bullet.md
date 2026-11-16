# US500 short — Wed 22 Feb 2023 14:09 NY · +2.87 R (TP1 14:15, TP2 14:56) · day-only +2.87 R

Engine silver-bullet trade, in-sample. Fact sheet: `../sheets/2026-11-16-30-trades/2023-02-22-1409-US500-short-silver_bullet.md`.

## What they tried to do
PM silver bullet short after the FOMC-minutes spike ran the 1h swing highs (4016.19 at 14:00; session high 4017.41) into the 1h bearish FVG 4016.14–4019.45, inside the 4h bearish FVG 4007.93–4028.71. Entry 4010.51, stop 4017.66, TP1 3997.34, TP2 the 4h swing low 3982.73. Against the read (daily bull, side bull); 4H and 1H bear.

## What happened
MAE −0.57 R, TP1 14:15, TP2 14:56. The next morning price went back up to 4027.74 (09:56), then fell to the 1d swing low 3948.24 on Friday.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | partial | sb_pm / ny_pm_kz, 14:09: 9 min after the FOMC minutes (medium); activity normal (1.25×) |
| 2 | Bias / narrative | partial | read counter_weekly, side bull; short ≠ read. 4H and 1H bear; target 0.4 ADR away |
| 3 | Dealing range | pass | 0.572 of the 1d range 3763.64–4195.33 = premium |
| 4 | POI / array | pass | 1h bearish FVG inside the 4h bearish FVG; 1d bearish IFVG 4023.62–4042.19 just above |
| 5 | Liquidity before | pass | buyside 1h swing highs 4013.00 (13:26) and 4016.19 (14:00) taken |
| 6 | Trigger | pass | proxy: raid on the release, entry 7 pts under the high, MAE −0.57 R |
| 7 | Stop | partial | 0.25 pts beyond the session high (at the liquidity); inside the 4h FVG, 11 pts under its top 4028.71 |
| 8 | Targets | pass | TP1 above the 4h bullish FVG 3990.71–3999.28, R:R 1.84; TP2 = the 4h swing low exactly (filled) |
| 9 | Management | pass | both partials inside 47 min, day-only |
| 10 | Attribution | pass | good process + win |

Step 6 is a proxy. Step 7 "at the liquidity" is by construction for this model.

## Price we should have looked at
- **The turn on the sheet** (4027.74, Thu 09:56) came 20 h later, after both targets were filled: a different swing. The trade's own turn was the 14:00 spike high 4017.41, inside the POI 4016.14–4019.45: known, and inside our stop.
- **The later high, known at entry:** yes. The top of the 4h bearish FVG 4028.71 (turn 1 pt under it), the 1h bearish FVG 4024.02–4028.71 and the low of the 1d bearish IFVG 4023.62. It is 0.269 ADR above our entry, 0.157 ADR beyond our stop.
- **What it says about our prices:** the stop covered the lower half of the 4h FVG only. The idea was wrong above 4028.71 / the 1d IFVG, not above 4017.41; an overnight runner would have been stopped. For the day-only trade the prices were right.
- **Target:** TP2 at the 4h swing low was the day's low area; the 1d swing low 3948.24 (+8.7 R) came two days later, after the retest of the 4h FVG's top.

## What they missed / should have seen (known at the entry)
- Nothing that cost on the day; the entry was 9 min after a scheduled release.

## What the market did (hindsight — lessons to test, not blame)
- The 4h FVG was filled to its top the next morning before the larger move.

## Verdict
**earned win.** HTF array + raid + near pool target, flat the same day.

## For the engine
- Record on every trade how much of the HTF array is beyond the stop (stop depth in the array, 0–1); test whether a low depth predicts runner stop-outs.
