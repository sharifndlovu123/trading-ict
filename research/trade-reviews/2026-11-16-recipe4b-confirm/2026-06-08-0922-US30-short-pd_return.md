# US30 short — Mon 08 Jun 2026 09:22 NY · engine -1.02 R (stop) · sheet -1.00 R · day-only -1.00 R
Engine pd_return trade, confirmation run of `recipe4b` (pre-registration `research/preregistered-recipe4b-2024H2-2026.md`, outcome FAIL). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2026-06-08-0922-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`. Entry 50995.94 · stop 51116.33 · TP1 50825.94 (5m swing low, 1.41 R) · risk 0.21 ADR · ADR 583.75 · area 4h FVG 50861.46–51084.06 (0.38 ADR) · decided 09:14, filled 09:22.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz, premarket fill 8 min before the 09:30 open; last hour normal (0.26 ADR, 1.31×); no news near |
| 2 | Bias / narrative | fail | weekly, daily and 4H bull, only the 1H bear: a short against the higher TF, target must be near (it was: 0.29 ADR) |
| 3 | Dealing range | fail | 0.49 of the 4h range 50320.73–51695.70: discount half for a short |
| 4 | POI / array | partial | 4h bearish FVG 50861.46–51084.06 (0.38 ADR), built across the weekend gap (Fri 14:00 / Sun 18:00); entry inside it; a second 4h bearish FVG 51188.94–51372.75 sat above |
| 5 | Liquidity before | pass | buyside taken first: 1h swing high 50818.50 at 03:47, Asia high 50861.46 at 06:36 |
| 6 | Trigger | partial | 08:45 15m body 47.5 pts = 1.6× the mean; gap 26.5 pts (0.045 ADR): a small push, not a displacement |
| 7 | Stop | partial | 51116.33 = session high 51057.95 + 0.10 ADR: beyond the pool and the area top, but 0.12 ADR below the next 4h bearish FVG, with the 09:30 open 8 minutes away |
| 8 | Targets | pass | TP1 = 5m swing low 50825.94, 1.41 R, nothing in the way |
| 9 | Management | n/a | stopped 09:30, eight minutes after the fill |
| 10 | Attribution | fail | counter-HTF short with a weak trigger, filled just before the open: the lesson |

## Market conditions
Consolidating, bull backdrop, normal volatility (0.99×), efficiency 0.16, no news (CPI two days later). Sheet: weekly and daily bull, 1H bear since Sunday evening; activity normal. The day: RTH range 0.93 ADR, opened mid-range, spiked 0.48 ADR above the entry in the first two minutes (high 51276.45 at 09:32), then sold all day to close at 0.08 of the range. A volatile down day after an opening stop run: the short was the right side for the day.

## Does this look like Sharif's recipe?
Area: a real 4h FVG, reached to its 50% in London, buyside swept first. 15m: a small push (1.6×), not the momentum he waits for. Timing: filled in the premarket. He would most likely say: "you sold a bit early, the NY session was a better choice here; notice the 4h FVG above" (close to his own words on US100 13 May 2022 and US500 14 Mar 2022). **Verdict: partly.**

## Why it lost / why it won
**Lost to a stop run, then reversal.** The 09:30 open ran the session high and the stop (0.10 ADR buffer) by another 0.27 ADR into the next 4h bearish FVG 51188.94–51372.75, turned there at 09:32, and TP1 traded at 13:02; the move reached 8.6 R by Tuesday.

## What the market did (hindsight)
- Engine exit stop at 06-08 09:30; MAE -1.17 R; best in favour the same day +2.19 R at 15:26; RTH range 0.93 ADR, net -0.34 ADR.

## Price we should have looked at
51276.45 at 09:32 (same swing): 0.481 ADR above the entry, 0.274 ADR beyond the stop. Level: the 4h bearish FVG 51188.94–51372.75, on the map before the entry. "Be patient until the area": the area that mattered was the higher one.

## Realism
Trigger closed before the decision (08:30 / 08:45 / 09:00, decided 09:14). Area complete Sun 22:00, 50% first reached 07:14, reaction high 51057.95 at 07:37; stop re-derived: matches. Fill 3.5 ticks through on the bar, 140 later. The area's third candle is the Sunday reopen: a weekend-gap FVG. No look-ahead found.

## Verdict
**lesson loss** — most useful change: no fill between 09:15 and 09:30 for a setup decided in the premarket; or wait for the open's run into the higher area.

## For the engine
- Report recipe trades filled 09:00–09:29 against those filled after 09:30, both periods; and "another same-side HTF FVG within 0.3 ADR beyond the stop" as a split.
- One trade is a lead, not evidence. Nothing is re-tuned on 2024-07 → 2026-11; any rule from this goes in-sample first, then a new pre-registration.
