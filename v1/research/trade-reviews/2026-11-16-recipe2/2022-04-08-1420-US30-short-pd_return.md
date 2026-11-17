# US30 short — Fri 08 Apr 2022 14:20 NY · engine +1.95 R (TP1) · sheet +1.65 R · day-only +1.65 R
Engine pd_return trade, variant "recipe2: full + not against 1h&4h + within 0.25 ADR + before 14:00" (1h/4h FVG to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop beyond the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows; three recipe gates). Facts: `research/trade-reviews/sheets/2026-11-16-recipe2/2022-04-08-1420-US30-short-pd_return.md`; row in `reports/recipe2-US30-2022-01-03-2024-06-28.parquet`.

## What they tried to do
Engine: short from a 1h bearish FVG 34863.58–34908.04 dated 05 Apr 05:00, returned to at 12:25 (high 34915.79 at 12:28), after a quiet 15m gap 34834.79–34841.26 at 13:30. Limit 34834.79, stop 34915.79, TP1 the 5m swing low 34675.24 (1.97 R). Weekly and 4H bear, daily and 1H bull.

## What happened
Decided 13:59, filled 14:20, 13 points of heat (34847.80 at 14:21), drifted down all afternoon. TP1 traded in the 15:59 bar, a 72-point spike to 34673.74 that closed at 34743.75, one minute before the 16:00 exit.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_pm_kz, Friday; last hour 0.146 ADR = 0.61× the normal; decided 13:59 |
| 2 | Bias / narrative | partial | split: 4H and weekly bear, 1H and daily bull; the engine read says bull |
| 3 | Dealing range | pass | 0.82 of the daily range 32340.27–35383.25 = premium |
| 4 | POI / array | fail | the area had failed three days earlier: on 05 Apr price filled it at 09:32, a 1m body closed above 34908.04 at 09:33 and the 09:00 1h candle closed above it. The engine restarts an area's life at 00:00 each day, so it looked fresh. The real level at that price was the 1d bearish FVG 34903.10–35053.29 |
| 5 | Liquidity before | partial | London high 34759.30 taken 10:52; the 1h equal highs 34918.50 stayed untouched 2.7 points above the high |
| 6 | Trigger | fail | 15m middle candle body 0.033 ADR = 0.44× the mean, gap 6.5 points (0.012 ADR): no displacement |
| 7 | Stop | fail | stop 34915.79 is 2.7 points short of the 1h equal highs 34918.50 (the pool is the magnet) |
| 8 | Targets | partial | 1.97 R, reached only by the 15:59 spike, 1.5 points through |
| 9 | Management | pass | day trade, flat by the close |
| 10 | Attribution | fail | weak process + win = luck |

## What they missed / should have seen (known at the entry)
- The area was already used up: filled and closed through on 05 Apr.
- No displacement: a 6-point gap in a quiet early afternoon.
- Equal highs 34918.50 resting just above the stop.

## What the market did (hindsight — lessons to test, not blame)
- The high 34915.79 held all afternoon; the equal highs were not taken.
- Without the 15:59 spike the trade exits at the 16:00 open 34744.80 = +1.11 R, not +1.95 R.

## Does this look like Sharif's recipe?
- **Area to its 50%?** Price traded to 34885.81, but the area was no longer valid (failed 05 Apr 09:33).
- **Side vs 1h/4h structure:** split (1h bull, 4h bear).
- **Displacement on the 15m?** No: body 0.44× the mean, gap 6.5 points.
- **Early or late?** Entry 0.055 ADR below the area, 94 min after the return, decided 13:59 on a Friday.
- **What he would most likely say:** "no major displacement occurred as yet, wasn't worth any trade" (his US500 10 Aug 2023 note).
- **Verdict:** no.

## Price we should have looked at
Same swing: 34847.80 at 14:21, 0.025 ADR above the entry and 0.131 ADR inside the stop, 6.5 points above the 15m gap's top (34841.26). Known. The session high 34915.79 under the 1d bearish FVG's low edge 34903.10 and the equal highs 34918.50 was the level that mattered.

## Look-ahead and realism check
- **15m FVG's third candle closed before the decision?** Yes. Candles 13:15 / 13:30 / 13:45; the third has all 15 one-minute bars and ends with the 13:59 bar; `decided_at` = 13:59 (that bar's stamp, i.e. known at its close). Gap 34834.79–34841.26 = 6.47 points (0.012 ADR), re-derived from 1m bars.
- **Area known before it was used?** Yes. 1h FVG 34863.58–34908.04, third candle closed 04-05 06:59; 50% traded 04-08 12:25. History: earlier days: near edge 04-05 08:02, 50% 04-05 09:31, filled 04-05 09:32, 1m body close beyond the far edge 04-05 09:33, 1h close beyond 04-05 09:00.
- **Fill after the decision?** Yes: 14:20, 21 min later; the first bar after the decision that reaches the limit.
- **Could the limit fill?** Fill bar traded 2.5 ticks through the limit; 13.0 ticks through during the hold.
- **Stop distance vs cost:** risk 81.0 points = 81 ticks = 0.155 ADR; futures cost 0.023 R. Stop = the reaction extreme 34915.79 (12:28), no buffer, exit on touch. Realistic.
- **Anything from after the decision?** None found: the stop extreme (12:28) and the TP1 level (printed 04-08 10:49) precede 13:59; structure states use completed candles (1h bull, 4h bear); ADR 520.94 from completed days. The engine re-run reproduces entry, stop and TP1 exactly.
- **Stale area:** invalid by the model's own rule (body close beyond the far edge) since 05 Apr. **TP1:** filled by a 1.5-point (1.5 tick) overshoot in the last bar before the time exit; on another feed it may not trade. Worth +0.84 R versus the 16:00 exit.
- **Result:** no look-ahead; realism flag (see the note above); the area was stale (a validity bug, not look-ahead).

## Verdict
**lucky win** — the area was dead and there was no displacement; the daily FVG above did the work.

## For the engine
- Bug to fix through the change gate: `returns()` runs `gap_lifecycle` on today's bars only, so an area filled or closed through on an earlier day is treated as fresh. Scale check below.
- Minimum displacement for the 15m trigger (middle body ≥ 1× the mean of 20, or the detector's displacement flag).
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
