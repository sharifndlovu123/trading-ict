# US30 short — Tue 26 Apr 2022 09:36 NY · engine +1.52 R (TP1) · sheet +1.54 R · day-only +1.54 R
Engine pd_return trade, variant "recipe2: full + not against 1h&4h + within 0.25 ADR + before 14:00" (1h/4h FVG to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop beyond the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows; three recipe gates). Facts: `research/trade-reviews/sheets/2026-11-16-recipe2/2022-04-26-0936-US30-short-pd_return.md`; row in `reports/recipe2-US30-2022-01-03-2024-06-28.parquet`.

## What they tried to do
4H and 1H bear, weekly bear, daily still bull. A 10-point 1h bearish FVG 33982.06–33992.29 formed in London (known 04:59) and was tagged at 05:08 (high 33988.09). Almost four hours later the 08:30 15m candle displaced down (body 0.127 ADR, 3.3× the mean) and left a gap 33871.04–33889.56. Limit 33871.04, stop 33988.09, TP1 the previous week low 33691.25 (1.54 R).

## What happened
Decided 08:59. Price first ran 1.23 R toward the target, came back and filled at 09:36, made 33895.23 at 10:07 (−0.21 R), then fell: previous week low 10:19, previous day low 15:18, day low 33184.72 (5.9 R).

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz; last hour normal (0.98×); no news |
| 2 | Bias / narrative | partial | with 1h and 4h (both bear) and the weekly; the daily is bull and the engine read says bull |
| 3 | Dealing range | partial | 0.485 of the daily range = at the EQ (33917.28) |
| 4 | POI / array | partial | the area is a sliver: 10 points, 0.019 ADR, touched once in London 231 min before the decision |
| 5 | Liquidity before | fail | no liquidity taken in the 6 h before |
| 6 | Trigger | pass | a real 15m displacement at 08:30: gap 18.5 points (0.035 ADR), displacement flag true |
| 7 | Stop | partial | on the 1h swing high 33988.09, no buffer; risk 0.221 ADR |
| 8 | Targets | partial | TP1 exactly at the previous week low, 1.54 R; the session low 33726.78 sits before it |
| 9 | Management | pass | all off at TP1 (TP1 = the final target) |
| 10 | Attribution | partial | right side and momentum, thin area, late entry: a win that the recipe only half describes |

## What they missed / should have seen (known at the entry)
- The entry was 0.209 ADR below the area: the trade is a 15m momentum short, not a sell at the area.
- The whole position came off at the previous week low; the next pool (previous day low 33313.78) was 1.0 ADR lower.

## What the market did (hindsight — lessons to test, not blame)
- The retrace stopped at 33895.23, 5.7 points above the 15m gap's top.
- The day ran 5.9 R; the plan had no runner because TP1 and the final target were the same level.

## Does this look like Sharif's recipe?
- **Area to its 50%?** Technically (33987.17 at 05:08), but the area is 10 points wide, so "its 50%" means nothing here.
- **Side vs 1h/4h structure:** with both.
- **Displacement on the 15m?** Yes: 3.3× the mean body, at 08:30.
- **Early or late?** Late: 231 min after the touch, 0.21 ADR from the area.
- **What he would most likely say:** "short is nice, but you're shorting quite late" (his US500 10 Jun 2022 note).
- **Verdict:** partly.

## Price we should have looked at
Same swing: 33895.23 at 10:07, 0.046 ADR above the entry and 0.175 ADR inside the stop. Level there: the 15m gap's top 33889.56 (the gap filled and held). Known at the entry.

## Look-ahead and realism check
- **15m FVG's third candle closed before the decision?** Yes. Candles 08:15 / 08:30 / 08:45; the third has all 15 one-minute bars and ends with the 08:59 bar; `decided_at` = 08:59 (that bar's stamp, i.e. known at its close). Gap 33871.04–33889.56 = 18.52 points (0.035 ADR), re-derived from 1m bars.
- **Area known before it was used?** Yes. 1h FVG 33982.06–33992.29, third candle closed 04-26 04:59; 50% traded 04-26 05:08. History: formed today.
- **Fill after the decision?** Yes: 09:36, 37 min later; the first bar after the decision that reaches the limit.
- **Could the limit fill?** Fill bar traded 12.7 ticks through the limit; 24.2 ticks through during the hold.
- **Stop distance vs cost:** risk 117.05 points = 117 ticks = 0.221 ADR; futures cost 0.016 R. Stop = the reaction extreme 33988.09 (05:08), no buffer, exit on touch. Realistic.
- **Anything from after the decision?** None found: the stop extreme (05:08) and the TP1 level (printed 04-22 16:09) precede 08:59; structure states use completed candles (1h bear, 4h bear); ADR 530.45 from completed days. The engine re-run reproduces entry, stop and TP1 exactly.
- **Result:** no problem found.

## Verdict
**earned win** — the 15m displacement with 1h and 4h was the trade; the area added nothing.

## For the engine
- Minimum area width (≥ 0.05 ADR) before "reached to its 50%" counts. On all 130 trades, areas 0.02–0.05 ADR wide: n 11, −0.34 R; ≤ 0.02 ADR: n 10, +0.73 R (one +4.37 R trade). Unclear; needs the audit.
- When TP1 equals the final target, keep a runner to the next external pool.
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
