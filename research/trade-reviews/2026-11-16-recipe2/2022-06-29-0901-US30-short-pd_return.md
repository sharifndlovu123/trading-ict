# US30 short — Wed 29 Jun 2022 09:01 NY · engine −1.03 R (stop) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, variant "recipe2: full + not against 1h&4h + within 0.25 ADR + before 14:00" (1h/4h FVG to its 50% → 15m FVG within 4 h → limit at the gap's near edge → stop beyond the reaction extreme → TP1 nearest untaken liquidity ≥ 1 R; no daily bias; NY windows; three recipe gates). Facts: `research/trade-reviews/sheets/2026-11-16-recipe2/2022-06-29-0901-US30-short-pd_return.md`; row in `reports/recipe2-US30-2022-01-03-2024-06-28.parquet`.

## What they tried to do
Weekly, daily, 1H bear; 4H bull. The 4h bearish FVG 31016.80–31101.75 left by Tuesday's sell-off was returned to for the first time: 1h equal highs taken 07:57, the 50% (31059.27) at 08:01, high 31083.07 at 08:15. The 08:30 GDP candle sold off and left a 2.7-point gap 31008.80–31011.51. Limit 31008.80, stop 31083.07, TP1 the 5m swing low 30888.59 (1.62 R), in front of the London low.

## What happened
Filled 09:01. At 09:19 price reached 31082.80, 0.27 points under the stop. It then fell to 30888.78 at 09:41, 0.19 points short of TP1. At the open's reversal it took the stop (09:51, high 31157.80). The day faded back to the entry by the close; TP1 traded overnight.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | pre-market, decided 29 min after GDP; normal (1.21×) |
| 2 | Bias / narrative | pass | W, D, 1H bear; side matches the read |
| 3 | Dealing range | fail | 0.356 of the daily range = discount for a short; inside the 1d bullish IFVG 30878.50–31379.30 |
| 4 | POI / array | pass | a fresh 4h bearish FVG (0.12 ADR), first return, reached to its 50% |
| 5 | Liquidity before | pass | buyside 1h equal highs 31017.79 taken 07:57 |
| 6 | Trigger | partial | middle candle 2.0× the mean body, but the gap is 2.7 points (0.004 ADR) |
| 7 | Stop | fail | stop on the session high 31083.07, inside the area: its far edge 31101.75 is 0.027 ADR further; risk 0.107 ADR |
| 8 | Targets | pass | 1.62 R, in front of the London low 30876.70 and the 1h equal lows 30873.59 |
| 9 | Management | partial | +1.62 R of open profit with nothing banked: no partial before TP1 |
| 10 | Attribution | pass | good process + loss = acceptable loss |

## What they missed / should have seen (known at the entry)
- The stop was inside the area, on the morning high.
- A short in the discount of the daily range inside a daily bullish IFVG: a small grab, so a nearer first partial fits.

## What the market did (hindsight — lessons to test, not blame)
- Both ends were decided by a quarter of a point: the stop survived by 0.27 and TP1 was missed by 0.19.
- The stop run reached 31157.80, 56 points beyond the area and 36 under the next 4h bearish FVG 31193.78–31516.57.

## Does this look like Sharif's recipe?
- **Area to its 50%?** Yes: a 4h area, 31059.27 at 08:01, first return.
- **Side vs 1h/4h structure:** split (1h bear, 4h bull); with W and D.
- **Displacement on the 15m?** A fair candle at 08:30 (2× the mean), a sliver of a gap.
- **Early or late?** 8 points under the area, 58 min after the 50%; on time.
- **What he would most likely say:** "nice, this was just a loss" / "we just got swept out by a minor liq grab."
- **Verdict:** partly.

## Price we should have looked at
Same swing: 31082.80 at 09:19, 0.106 ADR above the entry and 0.27 points inside the stop: the 08:15 high 31083.07 (double top). After the stop: 31157.80 at 09:52, 0.214 ADR above the entry and 0.107 ADR beyond the stop, between the area's far edge 31101.75 and the next 4h bearish FVG 31193.78. All known at the entry.

## Look-ahead and realism check
- **15m FVG's third candle closed before the decision?** Yes. Candles 08:15 / 08:30 / 08:45; the third has all 15 one-minute bars and ends with the 08:59 bar; `decided_at` = 08:59 (that bar's stamp, i.e. known at its close). Gap 31008.80–31011.51 = 2.71 points (0.004 ADR), re-derived from 1m bars.
- **Area known before it was used?** Yes. 4h FVG 31016.80–31101.75, third candle closed 06-28 21:59; 50% traded 06-29 08:01. History: earlier days: near edge not touched, 50% not reached, filled no, 1m body close beyond the far edge none, 4h close beyond none.
- **Fill after the decision?** Yes: 09:01, 2 min later; the first bar after the decision that reaches the limit.
- **Could the limit fill?** Fill bar traded 12.8 ticks through the limit; 100.0 ticks through during the hold.
- **Stop distance vs cost:** risk 74.27 points = 74 ticks = 0.107 ADR; futures cost 0.026 R. Stop = the reaction extreme 31083.07 (08:15), no buffer, exit on touch. Realistic.
- **Anything from after the decision?** None found: the stop extreme (08:15) and the TP1 level (printed 06-29 07:15) precede 08:59; structure states use completed candles (1h bear, 4h bull); ADR 695.77 from completed days. The engine re-run reproduces entry, stop and TP1 exactly.
- **Outcome is inside feed noise:** stop safe by 0.27 points, TP1 missed by 0.19 points (YM tick = 1). On futures this trade could as easily be +1.6 R, or stopped at 09:19.
- **Result:** no problem found.

## Verdict
**acceptable loss** — most useful change: TP1 a few ticks in front of the level, and a first partial at 1 R.

## For the engine
- `tp1_front_run` (e.g. 2–4 ticks before the pool). The mirror risk exists: 6 of the run's 47 TP1 exits traded less than one tick through TP1 in the exit bar (+9.0 R together). Both belong in one fill-realism test.
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
