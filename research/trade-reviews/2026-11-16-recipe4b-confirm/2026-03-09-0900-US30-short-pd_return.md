# US30 short — Mon 2026-03-09 09:00 NY · engine +0.93 R (TP1; with partials +0.46) · sheet +0.47 R · day-only +0.47 R
Engine pd_return trade, confirmation run of `recipe4b` on 2024-07 → 2026-11 (FAILED: 81 trades, 33.3% win, −0.17 R; `research/preregistered-recipe4b-2024H2-2026.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2026-03-09-0900-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`. Entry 46909.97 · stop 47201.62 · TP1 46636.00 (5m swing low, 0.94 R) · risk 0.413 ADR · ADR 706.31. Decided 08:59, filled 09:00.

## What they tried to do
Monday after a gap-down week open: the 'area' is a 4h bearish FVG 46703.47–47365.00 that is 0.937 ADR wide — the weekend gap itself (new week opening gap 47010.00–47443.92 inside it). The 08:30 15m candle displaced down, limit at the gap edge inside the area. Stop 0.10 ADR above the 1h swing high 47130.99; TP1 a 5m swing low (0.94 R), runner to the Asia low.

## What happened
Filled 09:00; open spiked to 47088.90 (09:30, 0.61 R of heat); TP1 46636.00 hit 10:10 (low 46616.04 at 10:11: 20 pts through), runner stopped at entry 10:44: +0.47 R managed (engine vote +0.93 R). The day then ran to 47875 (15:38), −2.5 R at the close.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | premarket Monday; no news; last hour busy (1.52× normal) |
| 2 | Bias / narrative | pass | daily, 4H, 1H bear; weekly bull; read matches |
| 3 | Dealing range | fail | 0.173 of the 4h range: deep discount |
| 4 | POI / array | partial | area 0.937 ADR wide = the weekend gap; inside a 1d bullish FVG 46585–47118, above a 1d bullish IFVG 46675–46850 |
| 5 | Liquidity before | fail | nothing swept |
| 6 | Trigger | pass | body 0.22 ADR, 3.34×; gap 82 pts (0.116 ADR) |
| 7 | Stop | partial | 0.10 ADR beyond the 1h swing high 47130.99, inside the NWOG |
| 8 | Targets | partial | TP1 at 0.94 R; 1h swing low 46837.45 and last-4h low 46739.92 before it |
| 9 | Management | pass | 50% at TP1, runner out at entry: the partial is the whole result |
| 10 | Attribution | partial | same weak location as the two losers of this minute; TP1 by 20 points = luck |

## What they missed / should have seen (known at the entry)
- Daily bullish FVG and IFVG directly under the entry: support in the way of the target.

## What the market did (hindsight — lessons to test, not blame)
- TP1 was the low of the morning to within 20 points; US100 and US500 missed theirs by 0.08–0.17 ADR and lost.

## Market conditions
- **Known before the day:** trending down (20-day efficiency 0.471), backdrop mixed, volatility normal (1.205× its 1-year median), no scheduled high-impact release.
- **The day:** range before the decision 0.97 ADR; whole day 2.03 ADR; 09:30–16:55 range 1.78 ADR, net +0.86 ADR. Same day as the US100/US500 trades: gap-down open, 2.03 ADR day, reversal up (RTH net +0.86 ADR). For this index the state was 'trending down' (efficiency 0.47).
- **Day type:** volatile/news.

## Does this look like Sharif's recipe?
- **Area:** 4h FVG 46703.47-47365.00, 0.937 ADR wide; entry -0.292 ADR from its near edge (negative = inside it).
- **15m:** middle candle 08:30 body 0.22 ADR = 3.34× the mean of the 20 before; gap 0.116 ADR (82.0 ticks).
- As US100: displacement and retrace real, the area is the weekend gap, the sell is in discount.
- **What he would most likely say:** 'if we took our partials we would have won here' — and he did take them (my reading).
- **Verdict:** partly.

## Why it won
The 08:30 displacement had one more R in it; TP1 was scraped at the morning low and the partial banked it before the reversal.

## Price we should have looked at
47088.90 at 09:30: 0.253 ADR above the entry, 0.16 ADR inside the stop; inside the NWOG (low edge 47010.00). Known.

## Realism
- 15m gap closed before the decision: yes (candles 08:15 / 08:30 / 08:45, the third ends at 08:59); the entry is the gap's near edge; the stop is the reaction extreme 47130.99 ∓ 0.10 ADR (that price is on the 1m bars before the decision).
- Fill bar traded 21.0 ticks through the limit; price ran 0 R our way between the decision and the fill.
- TP1 traded 20.0 ticks through within 30 minutes.
- TP1 traded 20 ticks through, for one minute.

## Verdict
**lucky win**

## For the engine
- Count as ideas: three trades of one event should be one row in any tally (the run's idea count already does this).
- One trade is a lead, not evidence; nothing is re-tuned on 2024-07 → 2026-11.
