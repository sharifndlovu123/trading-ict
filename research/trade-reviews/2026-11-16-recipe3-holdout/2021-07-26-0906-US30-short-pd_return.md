# US30 short — Mon 26 Jul 2021 09:06 NY · engine -1.05 R (stop) · sheet -1.00 R · day-only -1.00 R
Engine pd_return trade, variant "recipe3: recipe2 + fresh areas only" (1h/4h FVG, fresh, to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop on the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows; not against 1h&4h; within 0.25 ADR; before 14:00). Hold-out 2020–21. Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2021-07-26-0906-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`.

## What they tried to do
Weekly and daily bull, 4H bear, 1H bull. A 1h bearish FVG 34956.28–35021.73 (65 points, 0.173 ADR) left in the Sunday-evening reopen (formed 25 Jul 20:00, known 21:59). Its 50% (34989.00) traded at 08:17; the high of the reaction was 35001.30 at 08:27. The 08:30 15m candle closed down (body 0.104 ADR, 2.1× the mean) and left a gap 34961.30–34969.53. Limit 34961.30, stop 35001.30, TP1 the 1h swing low 34904.03 (1.43 R).

## What happened
Decided 08:59. Price ran 0.53 R down first, came back and filled at 09:06, then the cash open took the stop at 09:30, the Asia high at 09:31 and made 35097.50 at 09:36, 1.3 points under the previous day high 35098.76. Back at the entry 10:28, PDH taken 11:36, day high 35164.23 at 16:02. TP1 traded only on Tue 09:37.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz; last hour normal (0.88×); no news |
| 2 | Bias / narrative | fail | against the daily and the weekly (both bull); 1h bull, 4h bear = split; engine read: lower-TF pullback inside a bull trend |
| 3 | Dealing range | pass | 0.926 of the daily range = premium |
| 4 | POI / array | partial | 1h FVG 0.173 ADR, fresh, reached to its 50% at 08:17; it comes from the thin Sunday reopen |
| 5 | Liquidity before | fail | the buyside above was untaken: Asia high 35040.30 (0.22 ADR), PDH 35098.76 (0.38 ADR); overnight it was sellside that got taken (PDL 34848.72 at 03:41) |
| 6 | Trigger | partial | 08:30 candle is 2.1× the mean body (displacement flag true) but the gap is 8 points = 0.022 ADR |
| 7 | Stop | fail | on the session high 35001.30, no buffer, risk 0.105 ADR; Asia high and PDH sit just above |
| 8 | Targets | partial | TP1 exactly at the 1h swing low 34904.03 (not front-run), 1.43 R |
| 9 | Management | n/a | stopped before any management |
| 10 | Attribution | fail | weak process (short under two untaken buyside pools, against the daily) + loss |

## What they missed / should have seen (known at the entry)
- Two untaken buyside pools within 0.4 ADR above the stop (Asia high, PDH) with the daily and weekly bull: the draw was up.
- Sellside had been taken overnight (PDL at 03:41) and price had recovered 0.3 ADR: the Judas leg was already down, not up.

## What the market did (hindsight — lessons to test, not blame)
- The high of the swing was 35097.50, 1.3 points under PDH; price then gave the entry back at 10:28 but never reached TP1 that day.
- The 2-day turn on the sheet (35164.23 at Mon 16:02, "none on the map") is the day high after PDH was taken at 11:36, not this swing.

## Does this look like Sharif's recipe?
- **Area:** 1h FVG, 0.173 ADR wide, fresh (formed the evening before), reached to its 50% 42 min before the decision; entry inside it.
- **Side vs structure:** split on 1h/4h (1h bull, 4h bear); **against** the daily and weekly structure (bull).
- **15m displacement or a small gap?** Borderline: the 08:30 candle has size (0.104 ADR, 2.1×) but leaves only an 8-point gap (0.022 ADR). Counted as a small gap.
- **Early or late?** Early: before the cash open, before the buyside above was taken.
- **What he would most likely say:** "sold too early … we had to be a little more patient" (his 20 Jan 2022 note): the place to sell was PDH, and only after a displacement down from there.
- **Verdict:** partly.

## Price we should have looked at
Same swing: 35097.50 at 09:36, 0.359 ADR above the entry and 0.254 ADR beyond the stop. Level there: the previous day high 35098.76 (missed by 1.3 points). Known at the entry (on the sheet as a pool above, 0.38 ADR).

## Realism
- 15m gap closed before the decision? Yes: candles 08:15 / 08:30 / 08:45, the third has 15 one-minute bars, decision stamped 08:59.
- Fill: 09:06, after the decision; the fill bar traded 6.2 ticks through the limit (74 during the hold). Fillable.
- TP1: not reached.
- Later information: none found. Area known 25 Jul 21:59, 50% traded 08:17, stop extreme printed 08:27.
- Result: no problem.

## Verdict
**lesson loss** — a short under PDH and the Asia high against a bull daily; the turn came at PDH.

## For the engine
- Test: skip a short when an untaken session high or PDH lies within 0.4 ADR above the stop and the daily is bull (mirror for longs). Flag off, in-sample 2022–24 first.
- A batch is a lead, not evidence.
