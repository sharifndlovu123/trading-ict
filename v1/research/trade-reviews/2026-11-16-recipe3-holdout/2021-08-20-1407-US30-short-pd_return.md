# US30 short — Fri 20 Aug 2021 14:07 NY · engine +1.16 R (tp1) · sheet +0.60 R · day-only +0.60 R
Engine pd_return trade, variant "recipe3: recipe2 + fresh areas only" (1h/4h FVG, fresh, to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop on the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows; not against 1h&4h; within 0.25 ADR; before 14:00). Hold-out 2020–21. Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2021-08-20-1407-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`.

## What they tried to do
Friday afternoon. Weekly and daily bull, 4H bear, 1H bull since 09:00. A 4h bearish FVG 35002.00–35247.21 (245 points, 0.803 ADR) from 18 Aug. Price rallied all morning through London high, Asia high and PDH (35002.00 at 09:46), reached the 50% (35124.60) at 12:04 and made 35174.79 at 12:49. The 13:30 15m candle (body 0.047 ADR, 0.45× the mean) left a 2-point gap 35122.24–35124.21. Limit 35122.24, stop 35174.79, TP1 a 5m swing low 35059.21 (1.2 R).

## What happened
Decided 13:59, the last minute the rule allows. Price dipped 0.64 R, came back to 35124.27 at 14:07 (2 points through the limit), fell to TP1 at 14:45 (low 35056.7), then returned to the entry at 15:28.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_pm_kz; last hour normal (1.42×); Friday afternoon, decided one minute before the 14:00 cut-off |
| 2 | Bias / narrative | fail | against the daily and weekly (bull) and against the day itself: 1h bull since 09:00, six buyside pools taken on the way up; only the 4h is bear |
| 3 | Dealing range | pass | 0.787 of the daily range = premium, in the OTE |
| 4 | POI / array | partial | 4h FVG reached to its 50%, but it is 0.8 ADR wide: "inside the area" covers most of a day's range |
| 5 | Liquidity before | pass | buyside taken: Asia high 34921.80, 4h swing high 34995.22, PDH 35002.00 (all by 09:46) |
| 6 | Trigger | fail | no displacement: the middle candle is 0.45× the mean body and the gap is 2 points (2 ticks, 0.006 ADR) |
| 7 | Stop | partial | on the 1h swing high 35174.79, no buffer, risk 0.172 ADR |
| 8 | Targets | partial | TP1 a 5m swing low at 1.2 R; no pool before it |
| 9 | Management | pass | half off at TP1, runner out at the entry at 15:28 |
| 10 | Attribution | fail | weak process + win = luck |

## What they missed / should have seen (known at the entry)
- There was no displacement to trade: a 2-tick gap after a candle half the average size.
- The 1h had turned bull that morning and price had taken PDH; the short had only the 4h behind it.

## What the market did (hindsight — lessons to test, not blame)
- TP1 was the low of the move (35056.7, 2.5 ticks through); price was back at the entry 43 minutes later.

## Does this look like Sharif's recipe?
- **Area:** 4h FVG, 0.803 ADR wide (the widest of the batch), formed two days earlier, reached to its 50% at 12:04; entry at the 50%.
- **Side vs structure:** split on 1h/4h (1h bull, 4h bear); **against** the daily and weekly structure (bull).
- **15m displacement or a small gap?** No: a small gap (2 ticks, 0.006 ADR) from a candle 0.45× the mean body.
- **Early or late?** Late: 115 min after the 50%, Friday 14:00.
- **What he would most likely say:** "no major displacement occurred as yet, wasn't worth any trade" (his 10 Aug 2023 note).
- **Verdict:** not.

## Price we should have looked at
Same swing: 35124.27 at 14:07, 0.007 ADR above the entry and 0.165 ADR inside the stop. Level there: the area's 50% 35124.60 and the top of the 1d bearish FVG 35121.20. Known at the entry.

## Realism
- 15m gap closed before the decision? Yes: candles 13:15 / 13:30 / 13:45, third complete, decision 13:59.
- **Fill: not realistic.** Between the fill bar (14:07) and TP1 (14:45) price traded at most 2.0 ticks through the limit (high 35124.27 vs 35122.24). It first trades more than 4 ticks through at 15:29, after TP1. Under the 4-tick rule this winner does not exist.
- TP1: the exit bar traded 2.5 ticks through 35059.21; the day's low was 9.5 ticks through (14:46). A touch, then a turn.
- Later information: none found.
- Result: **fails the fill check** (one of the winners the 4-tick rule removes).

## Verdict
**lucky win** — no displacement, a 2-tick gap, a 2-tick fill and a 2.5-tick TP1; not the recipe.

## For the engine
- A minimum 15m gap in ADR (candidate ≥ 0.04 ADR with a middle-candle body ≥ 2× the mean): `min_trigger_gap_bp` exists; test it in ADR terms in-sample first.
- Keep reporting the 4-tick fill rule beside every result of this model.
