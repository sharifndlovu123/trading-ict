# US500 short — Fri 29 Jan 2021 03:50 NY · engine -1.07 R (stop) · sheet -1.00 R · day-only -1.00 R
Engine silver_bullet trade, first run on 2021 (`research/preregistered-conditions-2021.md`). Facts: `research/trade-reviews/sheets/2026-11-16-conditions-2021/2021-01-29-0350-US500-short-silver_bullet.md`. Entry 3748.65 · stop 3753.30 · TP1 3740.85 (5m swing low, 1.68 R) · final 3710.75 (PDL) · risk 4.65 pts = 0.079 ADR · ADR 58.55 · window sb_london · POI 1h FVG 3748.20–3757.64 · engine FVG 0.69 pt · decided 03:48, filled 03:50, stopped 04:01.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | sb_london; last hour **busy** (0.43 ADR, 2.82×); PCE at 08:30 (+280 min) |
| 2 | Bias / narrative | partial | weekly/daily bull; 4H and 1H bear since 27 Jan: a lower-TF pullback with structure behind it; target 0.59 ADR away |
| 3 | Dealing range | partial | 0.542 of the 1d range 3605.00–3870.05: 11 pts above the EQ 3737.53 |
| 4 | POI / array | partial | lower edge of the 1h bearish FVG 3748.20–3757.64, overlapped by a 1w bullish VI 3754.64–3758.94; the 4h bearish FVG 3765.15–3780.04 above |
| 5 | Liquidity before | fail | what was taken was **sellside** (Asia low 22:23, PWL 3748.45 22:41, 1h swing low 3737.34 23:19): the target side. No buyside taken |
| 6 | Trigger | fail | the 03:15 15m candle was **+0.244 ADR up**, the strongest of the last six: momentum against the short. Gap 0.69 pt |
| 7 | Stop | fail | 3753.30 is 0.069 ADR short of the last-4h high 3757.35, inside the POI gap |
| 8 | Targets | pass | TP1 5m swing low 3740.85, 1.68 R, nothing in front |
| 9 | Management | n/a | stopped 04:01, 11 minutes |
| 10 | Attribution | fail | sold into a bounce after the sellside was taken: the lesson |

## Market conditions
CSV (known before the day): **consolidating**, **bull** backdrop, **low** volatility (0.77× its 1-year median), efficiency 0.091, scheduled high-impact news: PCE. CSV says low volatility (0.77×) but the week was not: 4H/1H bear since 27 Jan, last hour 2.8× normal. PCE at 08:30. The day: bounce to 3780.90 at 08:48 (Asia high, 4h bearish FVG), then −1.5 ADR to 3692.4 at 13:17; RTH range 1.44 ADR, net −0.90. **Volatile/news**, a sell-off day.

## Why it lost / why it won
**Lost: too early, at the wrong array.** PWL and the Asia low had just been taken and the 15m was bouncing hard; the bounce went 0.47 ADR beyond the stop to the 4h bearish FVG / Asia high before the day sold off. The wide-stop counterfactual lost as well (−1.05 R).

## What the market did (hindsight)
- TP1 traded at 05:17, price then rallied to 3780.90 at 08:48 (−6.9 R) and fell to PDL 3710.75 at 12:37 (+8 R) and 3693.74 at 13:17 (+12 R)
- MFE before the stop 0.6 R

## Price we should have looked at
3780.90 (08:48): **0.551 ADR above the entry, 0.471 ADR beyond the stop**. Known levels: 4h bearish FVG 3765.15–3780.04, 4h bearish VI 3775.24–3787.45, 1d bearish IFVG 3775.70–3795.74, Asia high 3782.65. All known at the entry.

## Would Sharif take it?
**false** — Not here. The side fits (4H/1H bear) but the 15m momentum was up and the area was the 4h bearish FVG / 1d IFVG at 3765–3795. He would wait for that and for the 15m to turn (after PCE).

## Realism
Fill bar 03:50 high 3750.90 (2.2 pts through). Gap 0.69 pt = under 3 ES ticks. Risk 4.65 pts while the last hour ranged 25 pts.

## Verdict
**lesson loss** — most useful change: after sellside is taken and the 15m bounces, sell from the higher array, not the first gap.

## For the engine
- SB short when the last 15m candle before the decision closed up by ≥ 0.15 ADR (and mirror): split on 2022–24. Also the "fuel spent" split (last pool taken was on the target side).
- One trade is a lead, not evidence. 2021 is now used for this model; any rule goes in-sample (2022–24) first, then a new pre-registration.
