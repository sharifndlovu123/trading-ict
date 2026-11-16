# US30 short — 2021-03-05 10:06 NY · engine +3.07 R (TP1) · sheet +1.54 R · day-only +1.54 R
Engine pd_return trade, hold-out run of `recipe3: recipe2 + fresh areas only`. Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2021-03-05-1006-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`. Decided 09:59, filled 10:06, entry 31164.70, stop 31266.05, TP1 30851.56; ADR 413.2. Extra figures (area life, 15m candles, ticks) re-derived from 1m bars.

## What they tried to do
A pullback leg inside a bullish daily. After NFP price rallied through the whole 1h bearish FVG to 31266.05 (09:16, the 1w bearish IFVG), and the 09:30 candle displaced down 0.26 ADR. Short on the retrace to the 15m gap, stop on the high, TP1 the 1h swing low 30851.56.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz, sb_am, macro_0950; last hour 0.791 ADR = busy (2.65× normal); news: NFP Fri 08:30 (-96 min); NFP 89 min before; the busiest hour of the batch |
| 2 | Bias / narrative | partial | daily bull, weekly bull; at the decision 1h bear, 4h bear; engine read ltf_pullback, side matches: False; against the daily and weekly (bull); 1h and 4h bear give the lower-TF reason; the target is 0.69 ADR away |
| 3 | Dealing range | n/a | The sheet gives no half; the entry is 0.57 up the 1h area |
| 4 | POI / array | pass | 1h FVG 31026.73–31270.25, 0.589 ADR wide, known 03-04 13:59; 50% first traded 03-05 08:45; deepest 0.98 of the area before the trigger; entry inside; a 1w bearish IFVG 31251.28–31288.22 at the top of the area, where the high 31266.05 was made |
| 5 | Liquidity before | pass | buyside 1h swing high 30939.76 at 06:28 |
| 6 | Trigger | pass | 15m candles 09:15/09:30/09:45: middle body 0.255 ADR (3.5× the mean of 20), gap 30.82 points = 0.075 ADR (30.8 ticks) |
| 7 | Stop | partial | stop 31266.05 = the reaction extreme (09:16), no buffer; risk 0.245 ADR (101 ticks) |
| 8 | Targets | pass | TP1 30851.56 (5m swing low) at 3.09 R; pools before it: 1h swing low 30851.56; TP1 on the 1h swing low itself (not in front of it) |
| 9 | Management | pass | TP1 11:14, runner out at entry 12:45; the day then reversed to the previous day high |
| 10 | Attribution | pass | Sound process + win |

## What the market did (hindsight — lessons to test, not blame)
- Price ran 1.45 R down before filling us, came back to 31210.00 (10:07, −0.45 R), then TP1 at 11:14 and 3.96 R at 11:28.
- The afternoon took the previous day high (15:15): the engine read (bull, lower-TF pullback) was the right big picture; the short was the pullback.
- Sheet turn line (2-day window): 31210.0 at Fri 10:07 — 0.45 R (0.11 ADR) past our entry, inside our stop; from there it ran 4.41 R (1.08 ADR) our way. Known levels at that price: 1h bearish FVG 31026.73–31270.25

## Does this look like Sharif's recipe?
- **Area:** 1h FVG, 0.589 ADR wide (243.52 points); first trade to the 50% since it formed (03-05 08:45); near edge first touched 03-05 08:41. Reached to its 50%: yes, 74 min before the decision; deepest point 0.98 of the area.
- **Side vs structure:** 1h bear, 4h bear: with both. Daily bull (weekly bull): the trade is **against** the daily structure.
- **15m displacement:** a real displacement: middle candle body 0.255 ADR = 3.5× the mean of the last 20, gap 0.075 ADR (30.82 points), 3-candle leg 0.429 ADR.
- **Early or late:** Neither: the area was filled almost to its far edge (0.98) before the displacement. Entry inside; filled 7 min after the decision.
- **What he would most likely say:** "price reached that area … on the 15 we see momentum building down; that's where your decision is nice".
- **Verdict:** fully.

## Price we should have looked at
Same swing: 31210.00 at 10:07, 0.110 ADR above the entry and 0.136 ADR inside the stop. Levels there: the 15m gap top 31195.52 (14 points lower) and the upper quarter of the area. Known at the entry.

## Realism
- **15m gap closed before the decision?** Yes. Third candle 09:45 has all 15 one-minute bars and ends with the 09:59 bar = `decided_at`. Fill 7 min later.
- **Entry traded through the limit?** Fill bar 35.5 ticks through; at most 45.3 ticks during the hold. More than 4 ticks: a real fill.
- **TP1 traded through or touched?** Exit bar 0.3 ticks through; 88.4 ticks through within the next hour: traded through.
- **Later information?** None found: the area was known 03-04 13:59; the stop extreme printed at 09:16 and the TP1 level before the decision; structure states use completed candles.
- TP1 exit bar (11:14) traded 0.3 ticks through the target: a touch on that bar. The next bars went 88 ticks through within the hour, so the exit is real.
- **Result:** see the notes above; fill and exit hold.

## Verdict
**earned win** — most useful change: none.

## For the engine
- Reference case: counter-daily short that works as a pullback leg; TP1 at the first 1h swing, no runner expected.
- One trade is a lead, not evidence: in-sample test first, pre-registration before any default.
