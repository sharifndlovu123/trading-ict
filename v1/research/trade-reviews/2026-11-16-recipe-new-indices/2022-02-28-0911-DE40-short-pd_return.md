# DE40 short — Mon 28 Feb 2022 09:11 NY · engine −1.02 R (stop 10:33) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, the unchanged recipe (`recipe4`) on indices it had never seen (`research/preregistered-recipe-new-indices.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe-new-indices/2022-02-28-0911-DE40-short-pd_return.md`; row in `reports/recipe-new-indices-trades.parquet`. Entry 14252.28 · stop 14356.29 · TP1 14145.25 (5m swing low, 1.03 R) · runner 14023.77 · risk 0.28 ADR · ADR 375.6. POI 4h FVG 14136.57–14518.65. Decided 08:59, filled 09:11.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz, busy 1.99×, no US release; the driver is a weekend of unscheduled headlines (a gap Monday) |
| 2 | Bias / narrative | pass | aligned: weekly, daily, 4H, 1H all bear |
| 3 | Dealing range | fail | 0.414 of the 4h range 13793.16–14902.90: discount side of EQ |
| 4 | POI / array | partial | the 4h bearish FVG 14136.57–14518.65 is 382 pts = 1.02 ADR wide: it is the weekend gap, not a zone. Its 50% (14327.61) was reached at 07:55 (high 14356.29). The new week opening gap 14246.59–14659.78 and a 1w bullish FVG 14199.26–14407.76 cover the same prices |
| 5 | Liquidity before | fail | no pool taken in the 6 h before |
| 6 | Trigger | partial | 08:30 candle −0.22 ADR, gap 26.97 pts (0.072 ADR); but it is a swing inside the overnight range 14104–14356, not a break of it |
| 7 | Stop | fail | on the 1h swing high 14356.29, no buffer, in the middle of the area being sold: its far edge is 162 pts above the stop |
| 8 | Targets | pass | TP1 14145.25, 1.03 R, nothing in between; 1h swing low 14104.28 beyond |
| 9 | Management | n/a | MFE +0.31 R |
| 10 | Attribution | partial | right side, stop in the middle of an ADR-wide area + loss |

## Market conditions
Known before the day: volatility **high**, state **consolidating**, backdrop **bear**, no US release, **Monday**. Sunday opened 1.1 ADR below Friday's close (weekend sanctions headlines, from memory; not in the calendar). The day then filled the gap: 09:44 → 14516.9 at 11:28 (+0.79 ADR), turned at the Xetra close and gave back 0.87 ADR by 15:39. Day type: **volatile/news** (unscheduled).

## Why it lost
The short was placed in the lower half of a gap that price was still filling. The rally topped at 14516.9, 1.8 pts under the 4h FVG's far edge 14518.65, at 11:28. The stop was at the half-way mark. TP1 traded Tuesday 04:43 and price ran +5.2 R to the previous week low.

## Instrument notes
- A weekend gap of 1.1 ADR makes a "4h FVG" that is a whole day's range wide; "reached to its 50%" then means very little, and a stop at the reaction high sits mid-gap.
- The turn came at 11:28, two minutes before the cash close: on the DAX the far edge and the close arrived together.
- European headline risk is not in the US calendar.

## Would Sharif take it?
Area: yes, but an ADR wide. 15m momentum: partly. Side: yes. Right half: no (0.41). **Maybe** — more likely he waits for the gap to fill to its far edge.

## Verdict
**lesson loss** — right idea, stop in the middle of the area. One trade is a lead, not evidence.

## For the engine
- Cap the POI width (e.g. ≤ 0.5 ADR) or, for wider areas, require the far half; count stopped-then-target by area width. Check on all 193 trades before believing it; nothing is re-tuned on this run.
