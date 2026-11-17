# US30 short — Tue 08 Oct 2024 10:00 NY · engine -0.66 R (time exit 16:00) · sheet -1.00 R · day-only -0.70 R
Engine pd_return trade, confirmation run of `recipe4b` on 2024-07 → 2026-11 (FAILED; `research/preregistered-recipe4b-2024H2-2026.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2024-10-08-1000-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`. Entry 41978.93 · stop 42131.58 · TP1 41866.46 (5m swing low, 0.74 R, 50%) · final 41841.30 (previous week low) · risk 0.34 ADR · ADR 446.82. Decided 09:59, filled 10:00.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz, sb_am, 09:50 macro; last hour normal (1.08×); no news |
| 2 | Bias / narrative | fail | weekly, daily, 4H bull; only the 1H bear (since 07 Oct 14:00); read ltf_pullback, side bull: the short is the pullback leg |
| 3 | Dealing range | fail | 0.246 of the 4h range 41841.30–42400.47: discount, inside the buyers' OTE (pullback 0.77) |
| 4 | POI / array | pass | 4h bearish FVG 42047.94–42119.50 (0.16 ADR) from 07 Oct 10:00, 50% (42083.72) first reached at the 09:30 open, intact |
| 5 | Liquidity before | partial | the open spike to 42086.90 into the area is the inducement; no named pool taken since the Asia high at 05:03 |
| 6 | Trigger | pass | 09:30 candle 42044.78 → 41906.45: body 0.31 ADR (7.1×), gap 22.8 pts (0.051 ADR) |
| 7 | Stop | pass | 0.10 ADR above the 09:30 high = 42131.58: above the area (42119.50); 0.029 ADR short of the 1h swing high 42144.47 |
| 8 | Targets | fail | TP1 0.74 R at a 5m swing low; final = the 4h protected low 41841.30 with a 4h bullish FVG 41778–41850 and the 1w bullish FVG 41540–41844 under it: 0.25 ADR of room into weekly support; entry 0.15 ADR below the area |
| 9 | Management | pass | flat at 16:00, −0.66 R; no stop |
| 10 | Attribution | partial | real area and displacement, but sold late into HTF support + loss |

## Market conditions
Known before the day: **trending up**, backdrop **bull**, volatility **normal** (1.10× its 1-year median), 20-day efficiency 0.31, no scheduled high-impact release. No news, vol 1.10×, trending up in a bull backdrop. The open spiked into the 4h gap and dropped 0.46 ADR in 30 minutes, then nothing: low 41886.92 at 10:36 and a slow grind back up to the day high 42130.96 at 15:43. RTH range 0.59 ADR, net +0.08. A range day inside a bull trend: the counter-trend short had one 30-minute window. Day type: **range day** (the day's range and direction are hindsight).

## Does this look like Sharif's recipe?
- **Area:** yes, a fresh 4h gap reached to 50% at the open.
- **15m momentum:** yes, the strongest of the batch (7.1×).
- **Side:** the area's; against weekly, daily and 4H, "where we currently are" was the bottom quarter of the 4h range.
- **Early or late:** late: by the fill the displacement had spent 0.46 ADR and the entry was 0.15 ADR under the area.
- **What he would most likely say:** "short is nice, but you're shorting quite late; this is back in discount, wait for the retest of the FVG" (first clause his words from 10 Jun 2022; the rest my reading).
- **Verdict:** partly.

## Why it lost
**Wrong side for the trend, sold at the bottom of the range.** The move the recipe keyed on was complete when the trade was placed: it stalled 20 pts above TP1 (+0.60 R), right over the 4h protected low and the weekly bullish FVG, and the bull trend took it back to the area's far edge by the close (stop missed by 0.6 pt).

## Price we should have looked at
For the short, the level was the area itself: price returned to 42130.96 at 15:43, 0.340 ADR against the entry, 0.001 ADR inside the stop, just past the area's far edge 42119.50 (known). The first reaction after the fill was 42001.96 at 10:05 (0.052 ADR, 1w VI bottom 42007.80), good for +0.60 R only.

## Realism
- Area formed 07 Oct 10:00–18:00, 50% first reached 08 Oct 09:30, intact; reaction high 42086.90; stop matches.
- 15m gap candles 09:15 / 09:30 / 09:45, complete at 09:59 = decided_at; gap 22.8 pts re-derived. No look-ahead.
- Fill bar 10.5 pts through: real.
- **Near-stop booked as a time exit:** the day high was 0.6 pt under the stop; −0.66 R flatters it. The sheet's overnight replay is stopped the next morning (−1.00 R).
- TP1 0.74 R (target rule on the unbuffered risk).

## Verdict
**lesson loss** — most useful change: no entry more than ~0.1 ADR beyond the area when the target is the HTF protected level.

## For the engine
- Across the 81: counter-weekly-and-daily trades whose final target is within 0.3 ADR of a weekly/4h bullish (bearish) area.
- One trade is a lead, not evidence; nothing is re-tuned on 2024-07 → 2026-11.
