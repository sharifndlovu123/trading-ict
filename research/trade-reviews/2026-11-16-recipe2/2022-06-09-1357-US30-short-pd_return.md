# US30 short — Thu 09 Jun 2022 13:57 NY · engine +1.82 R (TP1) · sheet +1.83 R · day-only +1.83 R
Engine pd_return trade, variant "recipe2: full + not against 1h&4h + within 0.25 ADR + before 14:00" (1h/4h FVG to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop beyond the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows; three recipe gates). Facts: `research/trade-reviews/sheets/2026-11-16-recipe2/2022-06-09-1357-US30-short-pd_return.md`; row in `reports/recipe2-US30-2022-01-03-2024-06-28.parquet`.

## What they tried to do
Weekly, daily and 1H bear; 4H bull. Price was in the OTE of the daily leg. Engine: a 1h bearish FVG 32951.72–32953.09 (1.4 points wide, known 09:59) was tagged in the next minute (high 32955.22). Nearly four hours later the 13:15 15m candle broke down and left a 57-point gap 32797.79–32855.21. Limit 32797.79, stop 32955.22, TP1 the previous week low 32509.20 (1.83 R).

## What happened
Decided 13:44, filled 13:57, 30 points of heat (32828.29 at 13:59), then straight down: 1h swing low 14:43, 1d swing low 15:01, previous week low 15:28, day low 32261.80 (3.4 R). CPI the next morning took it 9 R.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_pm_kz; decided 13:44; normal (0.86×) |
| 2 | Bias / narrative | pass | W, D, 1H bear; side matches the read |
| 3 | Dealing range | pass | 0.621 of the daily range = premium, in the OTE |
| 4 | POI / array | fail | the area is 1.4 points wide (0.002 ADR), touched one minute after it formed and 224 min before the decision |
| 5 | Liquidity before | partial | London and Asia lows were taken at 08:44–08:50 (sellside, already gone); the 10:00 high is the 1h swing high |
| 6 | Trigger | pass | 15m break: gap 57 points (0.09 ADR), body 1.5× the mean |
| 7 | Stop | partial | on the 1h swing high 32955.22, no buffer; risk 0.247 ADR |
| 8 | Targets | partial | TP1 exactly at the previous week low, 1.83 R; two pools before it (1h low 32676.73, 1d low 32613.07) with no partial planned |
| 9 | Management | pass | all off at TP1 (TP1 = final target) |
| 10 | Attribution | partial | right side and momentum, no real area |

## What they missed / should have seen (known at the entry)
- The entry was 0.242 ADR below the area, at the edge of the 0.25 gate: this is a 15m breakdown short, not a sell at an area.
- No runner: TP1 and the final target were the same level, the day before CPI.

## What the market did (hindsight — lessons to test, not blame)
- The retrace stopped at 32828.29, the middle of the 15m gap (its 50% is 32826.50).
- The day ran 3.4 R and the next day 9 R.

## Does this look like Sharif's recipe?
- **Area to its 50%?** The area is a 1.4-point line; price poked 2 points through it at 10:00.
- **Side vs 1h/4h structure:** split (1h bear, 4h bull); with W and D.
- **Displacement on the 15m?** Yes: a 57-point gap.
- **Early or late?** Late: 0.24 ADR from the line, 224 min after the touch.
- **What he would most likely say:** "short is nice, but you're shorting quite late."
- **Verdict:** partly.

## Price we should have looked at
Same swing: 32828.29 at 13:59, 0.048 ADR above the entry and 0.199 ADR inside the stop. Level there: the 50% of the 15m gap (32826.50). Known at the entry.

## Look-ahead and realism check
- **15m FVG's third candle closed before the decision?** Yes. Candles 13:00 / 13:15 / 13:30; the third has all 15 one-minute bars and ends with the 13:44 bar; `decided_at` = 13:44 (that bar's stamp, i.e. known at its close). Gap 32797.79–32855.21 = 57.42 points (0.090 ADR), re-derived from 1m bars.
- **Area known before it was used?** Yes. 1h FVG 32951.72–32953.09, third candle closed 06-09 09:59; 50% traded 06-09 10:00. History: formed today.
- **Fill after the decision?** Yes: 13:57, 13 min later; the first bar after the decision that reaches the limit.
- **Could the limit fill?** Fill bar traded 4.7 ticks through the limit; 30.5 ticks through during the hold.
- **Stop distance vs cost:** risk 157.43 points = 157 ticks = 0.247 ADR; futures cost 0.012 R. Stop = the reaction extreme 32955.22 (10:00), no buffer, exit on touch. Realistic.
- **Anything from after the decision?** None found: the stop extreme (10:00) and the TP1 level (printed 06-02 10:28) precede 13:44; structure states use completed candles (1h bear, 4h bull); ADR 637.02 from completed days. The engine re-run reproduces entry, stop and TP1 exactly.
- **Result:** no problem found.

## Verdict
**earned win** — a momentum short with the higher timeframes from premium; the 1h line is a label, not the reason.

## For the engine
- On a wide 15m gap (≥ 0.05 ADR) test the limit at the gap's 50% with the stop beyond the gap: here the same turn with 30% of the risk. In-sample; `entry_level="ce"` exists.
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
