# US30 short — Wed 2026-03-04 10:00 NY · engine -1.01 R (stop; with partials -1.01) · sheet -1.00 R · day-only -1.00 R
Engine pd_return trade, confirmation run of `recipe4b` on 2024-07 → 2026-11 (FAILED: 81 trades, 33.3% win, −0.17 R; `research/preregistered-recipe4b-2024H2-2026.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2026-03-04-1000-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`. Entry 48505.42 · stop 48827.12 · TP1 48250.70 (5m swing low, 0.79 R) · risk 0.458 ADR · ADR 702.15. Decided 09:59, filled 10:00.

## What they tried to do
Short after buyside was taken into a 4h bearish FVG 48659.43–48759.96 (0.14 ADR; high 48756.90): the 09:30 15m candle displaced down 0.32 ADR, limit at the gap edge 48505.42. Stop 0.10 ADR above the reaction high, TP1 the London low 48250.70 (0.79 R), runner to PDL.

## What happened
Filled 10:00 on the retrace, MFE 0.07 R, then straight back up: stopped 10:27 at 48827.12. High 48856.43 at 11:47, 0.04 ADR past the stop, then down: TP1 Thursday 10:08, PDL Thursday 14:30, +4.7 R by Friday.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz, sb_am, macro 09:50; no news; last hour 0.58 ADR = 1.17× normal |
| 2 | Bias / narrative | partial | weekly + daily bull (daily protected higher low 48386.97 only 0.2 ADR below); 4H and 1H bear; read says side bull, no match |
| 3 | Dealing range | fail | 0.056 of the 1d range: the bottom of discount, wrong half for a short |
| 4 | POI / array | partial | 4h bearish FVG 0.14 ADR, but inside a 1d bullish FVG 48404–48843 with a 1w bullish FVG 48769–48852 on top |
| 5 | Liquidity before | pass | buyside 4h swing high 48694.85 taken at 09:20 into the area |
| 6 | Trigger | pass | body 0.322 ADR, 4.0×; gap 85 pts (0.121 ADR). Entry 0.22 ADR below the area |
| 7 | Stop | fail | stop 48827.12 is 0.062 ADR short of the PDH 48870.80, with the 1w FVG top 48852.19 between |
| 8 | Targets | partial | TP1 London low at 0.79 R, just past the 1h swing low 48282.90; the daily protected low 48386.97 in the way |
| 9 | Management | n/a | stopped 27 minutes after the fill |
| 10 | Attribution | partial | good sweep and trigger, stop short of the PDH: acceptable loss with a stop lesson |

## What they missed / should have seen (known at the entry)
- The stop sat under the PDH and the weekly FVG top: 0.06 ADR more would have cleared both.
- Price was inside a daily bullish FVG at the bottom of the daily range: the daily had to break before a short could run.

## What the market did (hindsight — lessons to test, not blame)
- High 48856.43: 0.042 ADR beyond the stop, 14 pts under the PDH, then −2.65 ADR over two days.
- Same day after the turn only 48687 (−0.56 R at the close): even a wider stop was a loser on the day-only rule; the move paid Thursday.

## Market conditions
- **Known before the day:** consolidating (20-day efficiency 0.127), backdrop mixed, volatility normal (1.189× its 1-year median), no scheduled high-impact release.
- **The day:** range before the decision 0.78 ADR; whole day 0.92 ADR; 09:30–16:55 range 0.72 ADR, net +0.19 ADR. Busy open (0.78 ADR range before the decision) then rotation: RTH range 0.72 ADR, net +0.19. A range day inside daily and weekly bullish gaps; the displacement did not follow through until the next day.
- **Day type:** range day.

## Does this look like Sharif's recipe?
- **Area:** 4h FVG 48659.43-48759.96, 0.143 ADR wide; entry +0.219 ADR from its near edge (negative = inside it).
- **15m:** middle candle 09:30 body 0.322 ADR = 4.02× the mean of the 20 before; gap 0.121 ADR (85.1 ticks).
- His sequence (sweep → displacement → retrace) is there; the entry is 0.22 ADR under the area and the stop is short of the PDH.
- **What he would most likely say:** 'we just got swept out by a minor liq grab, but nice eye' (his words on a similar loss); and 'sold a bit too early' — the retrace went back to the 4h area and above.
- **Verdict:** partly.

## Why it lost
Stop run then reversal: run by 0.042 ADR into the PDH / weekly FVG top, then the idea worked — a day late.

## Price we should have looked at
48856.43 at 11:47: 0.50 ADR above the entry, 0.042 ADR beyond the stop. Level: 1w bullish FVG top 48852.19 and PDH 48870.80. Known at the entry.

## Realism
- 15m gap closed before the decision: yes (candles 09:15 / 09:30 / 09:45, the third ends at 09:59); the entry is the gap's near edge; the stop is the reaction extreme 48756.9 ∓ 0.10 ADR (that price is on the 1m bars before the decision).
- Fill bar traded 98.1 ticks through the limit; price ran 0 R our way between the decision and the fill.
- TP1 did not trade that day.
- Fill bar traded 98 ticks through (price retraced straight through the limit).

## Verdict
**acceptable loss**

## For the engine
- Stop beyond the nearest pool within 0.1 ADR of the buffered stop (here PDH): count on this run how many of the 40 stops were 'short of a pool'. The fixed 0.10 buffer failed out-of-sample; a pool-aware stop is a different rule and needs its own pre-registration.
- One trade is a lead, not evidence; nothing is re-tuned on 2024-07 → 2026-11.
