# US30 short — Tue 26 Jan 2021 14:55 NY · engine -1.06 R (stop) · sheet -1.00 R · day-only -1.00 R
Engine silver_bullet trade, first run on 2021 (`research/preregistered-conditions-2021.md`). Facts: `research/trade-reviews/sheets/2026-11-16-conditions-2021/2021-01-26-1455-US30-short-silver_bullet.md`. Entry 30980.78 · stop 31010.75 · TP1 30950.20 (5m swing low, 1.02 R) · final 30710.26 (PWL) · risk 30.0 pts = 0.080 ADR · ADR 374.15 · window sb_pm · POI 1h FVG 31000.29–31021.24 · engine FVG 3.0 pts · decided 14:48, filled 14:55, stopped 15:24.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_pm, NY PM killzone; last hour normal (0.166 ADR, 0.92×); FOMC is the next day |
| 2 | Bias / narrative | fail | weekly, daily, 4H and 1H all bull (1H since 06:00); the read is "aligned, bull": a short with no lower-TF break |
| 3 | Dealing range | partial | 0.548 of the 4h range 30607.21–31288.30: 0.05 above the EQ 30947.75 |
| 4 | POI / array | partial | the POI 1h bearish FVG 31000.29–31021.24 is 20 pts above the entry; the entry is under it, on top of a 1d bullish VI 30909.78–30959.71 |
| 5 | Liquidity before | partial | PDH 31111.50 taken at 09:33, more than 5 h earlier |
| 6 | Trigger | partial | 14:15 15m candle −0.095 ADR, then +0.027; a 3-pt gap |
| 7 | Stop | fail | 31010.75 is 0.004 ADR short of the last-4h high 31012.29 and **inside** the POI (top 31021.24) |
| 8 | Targets | partial | TP1 30950.20 at 1.02 R, landing inside the 1d bullish VI; final PWL 0.72 ADR away at 14:55 |
| 9 | Management | n/a | stopped 15:24 |
| 10 | Attribution | fail | against every timeframe, stop inside the area: the lesson |

## Market conditions
CSV (known before the day): **consolidating**, **bull** backdrop, **low** volatility (0.58× its 1-year median), efficiency 0.259, scheduled high-impact news: none. Sheet: all four timeframes bull, price inside a 1d IFVG; activity normal; FOMC statement the next afternoon. The day: PDH swept at 09:33 (31116.3), then a slow slide to 30921.2 at 15:55; RTH 0.52 ADR, net −0.31. A pre-FOMC **quiet grind** down.

## Why it lost / why it won
**Lost: the stop was inside the area the trade was built on.** The retrace filled the 1h bearish FVG to 31016.73 at 15:29, 6 pts beyond the stop and still inside the gap, then fell 2.6 ADR into the FOMC day. The wide-stop counterfactual won (+0.64 R).

## What the market did (hindsight)
- stopped 15:24, turn 15:29, TP1 traded 15:49; PWL 30710 gone by Wed 06:46 (+9 R), +31 R by Wed 18:58
- the side was right although every timeframe read bull

## Price we should have looked at
31016.73 (15:29): **0.096 ADR above the entry, 0.016 ADR beyond the stop**, inside the 1h bearish FVG 31000.29–31021.24 above the last-4h high 31012.29. Known.

## Would Sharif take it?
**false** — No. Everything read bull and price sat at the EQ; no 15m momentum down. Outcome aside, this is a reversal catch, not his trade.

## Realism
Fill bar 14:55 high 30988.30 (7.5 pts through). Stop bar 15:24 high 31011.24, 0.5 pt through the stop. **Stop placed inside the POI gap** (10 pts under its top).

## Verdict
**lesson loss** — most useful change: stop beyond the far edge of the gap that is the POI.

## For the engine
- SB: stop = far edge of the POI FVG (+ buffer) when the POI is a 1h FVG the entry sits under; compare with the current stop on 2022–24 (cf_wide_stop already hints: +0.64 here).
- One trade is a lead, not evidence. 2021 is now used for this model; any rule goes in-sample (2022–24) first, then a new pre-registration.
