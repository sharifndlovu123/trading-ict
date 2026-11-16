# US30 short — Fri 13 Jun 2025 09:29 NY · engine +0.72 R (TP1) · with the runner +0.35 R
Engine pd_return trade, variant "recipe4b: mornings only, stop + 0.10 ADR, target kept", confirmation run 2024-07 → 2026-11 (FAILED). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2025-06-13-0929-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`; extra numbers from 1m bars.

## What they tried to do
Overnight gap down on unscheduled news (the open was 0.66–0.84 ADR below Thursday's close; nothing on the calendar). Area: the 1h bearish FVG the overnight drop left, 42432.60–42748.54 (0.62 ADR); price climbed back to its 50% in the premarket (07:01–08:36). 15m gap at 09:14. Limit at the gap edge, stop 0.10 ADR above the premarket reaction high, TP1 a 5m swing low at 0.74 R; runner to the Asia low.

## What happened
Price dipped 0.68 R before the fill at 09:29. The open spiked to 42580 at 09:32 (0.43 R against) and dropped 140 points in the next minute: TP1 at 09:33. London low 09:55; the runner was stopped at the entry at 11:30 (high 42608 at 11:52); Asia low at 14:27, close 2.8 R in favour (net −0.62 ADR). Same idea on three indices (one idea: two stops, one TP1).

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz, filled 1–4 minutes before the cash open; no scheduled release; activity normal (1.2–1.3×) |
| 2 | Bias / narrative | partial | W bear, D bull (4H bull on US100/US500, bear on US30), 1H bear; engine read = bull, side does not match; the short rides the overnight leg |
| 3 | Dealing range | pass | 0.70 of the 1d range: premium, in the OTE |
| 4 | POI / array | pass | a real displacement area from the overnight drop, reached to its 50% |
| 5 | Liquidity before | fail | no pool taken in the 6 h before; the Asia high is untaken above |
| 6 | Trigger | fail | 15m middle candle 1.0× the mean body (0.04 ADR); gap 14.5 points (0.028 ADR): no displacement; filled after price had already dipped 0.68 R |
| 7 | Stop | partial | 0.10 ADR above the premarket high 42595.89; 0.20 ADR inside the area's far edge; it held by 0.13 ADR |
| 8 | Targets | partial | TP1 0.74 R at a 5m swing low; the 1h swing low and London low are the real pools 0.24–0.3 ADR below |
| 9 | Management | partial | half at TP1, runner stopped at the entry before the afternoon leg |
| 10 | Attribution | fail | a premarket limit with no displacement and a stop inside the area, minutes before the open |

## Market conditions
- **Known before the day:** consolidating, mixed backdrop, normal volatility (1.027× its 1-year median), scheduled high-impact release: no; 20-day efficiency 0.156.
- **The read:** Weekly bear (since March), daily bull (11 May on US100/US500, 11 Jun on US30), 1H bear since 12 Jun. "Daily bull against the weekly bear: expect small grabs."
- **The day:** Unscheduled overnight news and a gap down; `news_day` = no and volatility "normal" on the 20-day measure, so the morning conditions did not flag it. Day range 0.75–1.05 ADR, net −0.62 ADR, two-sided on US100/US500, down on US30.
- **Day type:** volatile/news.

## What they missed / should have seen (known at the entry)
- The 15m "gap" came from candles smaller than average: nothing had displaced.
- The stop was 0.20 ADR inside the area's far edge with the Asia high above, placed minutes before 09:30.

## What the market did (hindsight — lessons to test, not blame)
- The open spiked up into the rest of the area on all three indices within three minutes; where it stopped relative to each stop decided the result.

## Does this look like Sharif's recipe?
- Area: yes, real, at its 50%. 15m momentum: none. Entry before the open, stop inside the area.
- **What he would most likely say:** "no major displacement occurred as yet, wasn't worth any trade" — he would wait for the open to push into the area and displace down, then sell with the stop beyond that sweep.
- **Verdict:** not.

## Why it won
**The opening spike stopped short of the stop.** The same idea as US100 and US500 in the same four minutes: there the open ran the stops, here it turned 0.13 ADR inside it and a 0.74 R target was hit a minute later. The Dow was the weakest index and trended down.

## Price we should have looked at
Same swing: 42580.00 at 09:32 — 0.099 ADR above the entry, 0.131 ADR inside the stop, 11 points under the area's 50% (42590.6) and the premarket high 42595.89. The area's far edge / Asia high was the level: a sell after the open reached it, stop beyond it.

## Realism
15m gap closed before the decision (09:00–09:14): yes. Resting limit not cancelled after the pre-fill dip. Fills 0.8–10 points through. The sheet's "turn" line (12:18 on US100/US500) is a later swing; recomputed. Unscheduled news is not in the calendar by design. Three trades, one idea. TP1 traded 15 points through in its minute. `r` books the whole position at TP1 (+0.72); half + runner gives +0.35. No later information found.

## Verdict
**lucky win**

## For the engine
- Trigger candle must be a displacement (body ≥ 1.5–2× the mean and a minimum in ADR); on areas wider than ~0.3 ADR the stop goes beyond the far edge or the trade waits.
- One trade (one batch) is a lead, not evidence: in-sample test first, pre-registration before any default; no re-tuning on 2024-07 → 2026-11.
