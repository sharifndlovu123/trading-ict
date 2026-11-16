# US100 short — Fri 19 Feb 2021 03:40 NY · engine +1.04 R (tp1) · sheet +0.55 R · day-only +0.55 R
Engine silver_bullet trade, first run on 2021 (`research/preregistered-conditions-2021.md`). Facts: `research/trade-reviews/sheets/2026-11-16-conditions-2021/2021-02-19-0340-US100-short-silver_bullet.md`. Entry 13642.89 · stop 13650.97 · TP1 13634.04 (5m swing low, 1.10 R) · final 13553.05 (Asia low) · risk 8.08 pts = 0.032 ADR · ADR 253.00 · window sb_london · POI 1h FVG 13648.90–13722.90 · engine FVG 0.85 pt · decided 03:39, filled 03:40, TP1 03:43.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london; last hour normal (0.128 ADR, 1.11×); no news |
| 2 | Bias / narrative | partial | weekly/daily/4H bull; 1H bear since 16 Feb, its protected lower high 13656.89 only 0.06 ADR above the entry |
| 3 | Dealing range | fail | 0.31 of the 4h range 13525.12–13904.90: **discount**, the wrong half; the read has price in the OTE for a long |
| 4 | POI / array | fail | entry is 6 pts under the POI (1h FVG 13648.90–13722.90); a 1w bullish VI 13610.62–13631.19 sits 0.05 ADR below |
| 5 | Liquidity before | pass | Asia high 13644.20 taken at 03:02 |
| 6 | Trigger | fail | 15m flat (+0.041, −0.012 ADR); gap 0.85 pt = 0.003 ADR; decided and filled a minute apart |
| 7 | Stop | fail | 13650.97 is 0.001 ADR beyond the last-4h high 13650.72; risk 8 pts; 1h swing high 13658.40 just above |
| 8 | Targets | partial | TP1 13634.04 is 8.9 pts away (1.10 R), in front of the 1w bullish VI; the final target is through that VI |
| 9 | Management | partial | TP1 after 3 min, the other half out at entry 03:55 |
| 10 | Attribution | fail | wrong half, no trigger, 9-pt target: luck |

## Market conditions
CSV (known before the day): **consolidating**, **bull** backdrop, **low** volatility (0.79× its 1-year median), efficiency 0.084, scheduled high-impact news: none. Sheet: weekly/daily/4H bull, 1H bear; activity normal; no news; monthly options expiry Friday. The day: up through London to 13731.1 at 08:49 (PDH 13724.79, 4h bearish FVG), then down to 13538.8 at 13:10; range 0.76 ADR, net −0.04. **Range day**.

## Why it lost / why it won
**Won 9 points in three minutes, then the market went the other way.** TP1 was a 5m swing low 0.035 ADR away. After it filled, price took the stop-side highs one by one (13658, 13673, 13702, PDH) and ran 0.35 ADR against before the real turn at the PDH / 4h bearish FVG.

## What the market did (hindsight)
- the runner was out at entry at 03:55; −10.9 R against by 08:49; the Asia low (final target) traded at 13:09
- engine books +1.04 R, partial management +0.55 R

## Price we should have looked at
The swing the trade aimed at turned at 13731.10 (08:49): **0.349 ADR above the entry, 0.317 ADR beyond the stop**, at the 4h bearish FVG 13689.79–13730.44, the 1h bearish FVG 13694.59–13735.26 and the PDH 13724.79. Known at the entry. (The trade's own MAE was 3.4 pts, 0.013 ADR.)

## Would Sharif take it?
**false** — No. Short in the discount half with a flat 15m, under the area rather than in it. The area was the 4h bearish FVG / PDH 0.2–0.35 ADR higher, where it turned.

## Realism
Risk 8.08 pts (32 ticks) and a 0.85-pt gap pass every gate. TP bar 03:43 low 13633.19: 0.85 pt through TP1. Costs are about 4% of risk.

## Verdict
**lucky win** — most useful change: a short in the discount half needs the higher array; skip the scalp under it.

## For the engine
- SB pricing gate: this short passed "pricing" at 0.31 of the 4h range; check what range the gate uses (leg-start ↔ DOL equilibrium) against the read's current range on 2022–24.
- One trade is a lead, not evidence. 2021 is now used for this model; any rule goes in-sample (2022–24) first, then a new pre-registration.
