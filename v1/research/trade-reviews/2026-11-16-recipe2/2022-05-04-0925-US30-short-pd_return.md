# US30 short — Wed 04 May 2022 09:25 NY · engine −1.03 R (stop) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, variant "recipe2: full + not against 1h&4h + within 0.25 ADR + before 14:00" (1h/4h FVG to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop beyond the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows; three recipe gates). Facts: `research/trade-reviews/sheets/2026-11-16-recipe2/2022-05-04-0925-US30-short-pd_return.md`; row in `reports/recipe2-US30-2022-01-03-2024-06-28.parquet`.

## What they tried to do
FOMC day. Weekly, daily, 4H bear; 1H bull (pullback). The 4h bearish FVG 33149.28–33309.50 (Friday 29 Apr to Sunday's open) was reached to its 50% at 05:54 after Asia high and a 1h swing high were taken; high 33275.58 at 07:23. The 08:30 15m candle displaced down (2.5× the mean) and left a gap 33204.10–33221.00. Limit 33204.10, stop 33275.58, TP1 the 5m swing low 33103.50 (1.41 R).

## What happened
Filled 09:25. At 09:49 price ran the high by 4.7 points (33280.24) and took the stop; then it fell: TP1 traded 10:34, low 33018.70 at 11:35 (2.59 R). After the FOMC statement it rallied 1,100 points.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz; normal (0.86×); FOMC statement five hours later, known in advance |
| 2 | Bias / narrative | pass | W, D, 4H bear; side matches the read (lower-TF pullback) |
| 3 | Dealing range | partial | 0.469 of the 4h range = just under the EQ 33254.28 |
| 4 | POI / array | partial | a 4h FVG, 0.25 ADR wide, but already used: 50% reached 02 May, fully filled 03 May 11:32 with a 1m body close above it (no 4h close above) |
| 5 | Liquidity before | pass | Asia high 33217.24 (05:42) and the 1h swing high 33251.25 (05:58) taken first |
| 6 | Trigger | pass | 15m displacement at 08:30: gap 16.9 points (0.027 ADR), flag true |
| 7 | Stop | fail | stop on the session high 33275.58 with no buffer, inside the area (far edge 33309.50 is 0.053 ADR further), previous day high 33344.21 above; risk 0.112 ADR |
| 8 | Targets | pass | 5m swing low at 1.41 R; the last-4h low 33165.06 before it |
| 9 | Management | n/a | stopped before TP1 |
| 10 | Attribution | partial | good read, stop on the pool = acceptable loss |

## What they missed / should have seen (known at the entry)
- The stop sat exactly on the morning high inside the area; the area's own far edge 33309.50 and the previous day high were the levels that would make the idea wrong.
- FOMC at 14:00: a morning short had to be out before it (it would have been: TP1 10:34).

## What the market did (hindsight — lessons to test, not blame)
- Stopped by 4.7 points (0.007 ADR), then TP1 44 min later.
- A stop beyond the area's far edge (33309.50, risk 105 points) survives; TP1 at the same level is then 0.95 R.

## Does this look like Sharif's recipe?
- **Area to its 50%?** Yes (33229.39 at 05:54), a 4h area; third visit.
- **Side vs 1h/4h structure:** split (1h bull, 4h bear); with W and D.
- **Displacement on the 15m?** Yes, 2.5× the mean body at 08:30.
- **Early or late?** Inside the area, 0.04 ADR under its 50%; on time.
- **What he would most likely say:** "we just got swept out by a minor liq grab, but nice eye."
- **Verdict:** partly.

## Price we should have looked at
Same swing: 33280.24 at 09:49, 0.12 ADR above the entry and 0.007 ADR beyond the stop. Level there: the session high / 1h swing high 33275.58 (the stop itself); the area's far edge 33309.50 was never reached. Known at the entry.

## Look-ahead and realism check
- **15m FVG's third candle closed before the decision?** Yes. Candles 08:15 / 08:30 / 08:45; the third has all 15 one-minute bars and ends with the 08:59 bar; `decided_at` = 08:59 (that bar's stamp, i.e. known at its close). Gap 33204.10–33221.00 = 16.9 points (0.026 ADR), re-derived from 1m bars.
- **Area known before it was used?** Yes. 4h FVG 33149.28–33309.50, third candle closed 05-01 21:59; 50% traded 05-04 05:54. History: earlier days: near edge 05-01 23:39, 50% 05-02 10:32, filled 05-03 11:32, 1m body close beyond the far edge 05-03 11:32, 4h close beyond none.
- **Fill after the decision?** Yes: 09:25, 26 min later; the first bar after the decision that reaches the limit.
- **Could the limit fill?** Fill bar traded 6.2 ticks through the limit; 76.1 ticks through during the hold.
- **Stop distance vs cost:** risk 71.48 points = 71 ticks = 0.112 ADR; futures cost 0.027 R. Stop = the reaction extreme 33275.58 (07:23), no buffer, exit on touch. Realistic.
- **Anything from after the decision?** None found: the stop extreme (07:23) and the TP1 level (printed 05-04 03:35) precede 08:59; structure states use completed candles (1h bull, 4h bear); ADR 636.82 from completed days. The engine re-run reproduces entry, stop and TP1 exactly.
- **Area validity:** by the model's 1m rule this area was invalid since 03 May 11:32; no 4h candle closed above it, so by its own timeframe's closes it was still alive. The two rules disagree.
- **Result:** no problem found; the area was stale (a validity bug, not look-ahead).

## Verdict
**acceptable loss** — most useful change: when the reaction extreme is inside the area, put the stop beyond the area's far edge.

## For the engine
- `stop_mode`: "reaction" unless the extreme is inside the area, then beyond the far edge. On all 130 trades roughly 17 of the 58 stops saw TP1 trade later the same day (from my bar check, not the simulator); test in-sample.
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
