# US30 short — Mon 10 Feb 2025 10:00 NY · engine −0.13 R (flat 16:00) · day-only −0.07 R
Engine pd_return trade, variant "recipe4b: mornings only, stop + 0.10 ADR, target kept", confirmation run 2024-07 → 2026-11 (FAILED). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2025-02-10-1000-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`; extra numbers from 1m bars.

## What they tried to do
Area: the 4h bearish FVG 44369.28–44657.03 from Friday's sell-off (0.56 ADR wide, middle candle 0.99 ADR). Monday gapped up into it: 50% (44513) reached 07:27, high 44623.25 at 09:32. The 09:30 15m candle fell 0.39 ADR (18.8× the mean) and left a 114-point gap. Limit 44434.25, stop 44674.69, TP1 = PWL 43815.24 (2.57 R, 1.2 ADR away).

## What happened
Filled 10:00, worst 44496.5 at 10:06, best 0.57 R at 12:12 (about 44297, in the 1d bullish FVG 44207.60–44330.30), then sideways. Flat at 16:00 for −0.13 R. Day range 0.63 ADR.

## Checklist
| # | Step | Grade | Evidence (known at entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz, sb_am, the 09:50 macro; no release; activity busy (1.58×) |
| 2 | Bias / narrative | partial | W, D and 4H bull, only the 1H bear; engine read = bull pullback; the short needs a near target and has a far one |
| 3 | Dealing range | fail | 0.13 of the 4h range: discount; the 4H protected low 44339.78 is 0.2 ADR below |
| 4 | POI / array | pass | a real 4h displacement gap from Friday, reached past its 50%, far edge not touched |
| 5 | Liquidity before | partial | Asia high taken 04:01 (buyside, for us); but a 1h swing low was already taken at 09:42, before the entry |
| 6 | Trigger | pass | 09:30 candle 18.8× the mean body; gap 0.22 ADR; fill on the first return to it |
| 7 | Stop | pass | 0.10 ADR beyond the session high and 0.03 ADR beyond the area's far edge; wide (0.47 ADR) |
| 8 | Targets | fail | TP1 1.2 ADR away with the 1d bullish FVG, the 4H protected low and two 4h swing lows before it; none planned as a partial |
| 9 | Management | partial | no partial was possible; flat at the close |
| 10 | Attribution | partial | the sequence is right; the target ignored everything between |

## Market conditions
- **Known before the day:** trending up, bull backdrop, normal volatility (1.114× its 1-year median), scheduled high-impact release: no; 20-day efficiency 0.469.
- **The read:** Weekly, daily and 4H bull (4H protected low 44339.78), 1H bear since 7 Feb. Price inside the 1w IFVG 44325.00–44573.75.
- **The day:** No release; gap up 0.47 ADR, a 0.52 ADR drop in the first half hour, then a flat afternoon: day range 0.63 ADR, net −0.24 ADR. Calm bull backdrop: not a recipe day, and a 1.2 ADR target could not be reached.
- **Day type:** range day.

## What they missed / should have seen (known at the entry)
- The 09:30 candle had already spent 0.39 ADR and the entry sat 0.2 ADR above the 4H protected low and a daily bullish FVG.
- TP1 skipped four nearer pools.

## What the market did (hindsight — lessons to test, not blame)
- Price stalled in the daily bullish FVG at 0.57 R and went sideways; with the sheet's overnight hold the trade reached 1.45 R on Wednesday (CPI).

## Does this look like Sharif's recipe?
- Area: a real 4h gap at its 50%. 15m momentum: unmistakable. NY morning, stop beyond the extreme.
- **What he would most likely say:** "short is nice, but you're shorting quite late" — the displacement was the move; and partials at the first swing low, not PWL.
- **Verdict:** fully.

## Why it lost
**A target too far for a quiet day.** Stop 0.47 ADR, target 1.2 ADR, day range 0.63 ADR; the entry came after the day's only push and above daily support.

## Price we should have looked at
Same swing (against us): 44496.5 at 10:06 — 0.121 ADR above the entry, 0.346 ADR inside the stop, at the area's 50% (44513) and inside the 15m gap. The level that mattered was on the other side: the 1d bullish FVG top 44330.30 / 4H protected low 44339.78, 0.2 ADR below the entry, where the move ended.

## Realism
15m gap closed before the decision: yes. Fill 9 points through. TP1 selection skipped nearer pools (4h swing low 44056.73 at 1.6 R). The sheet holds overnight (+0.77 R); the engine is flat at 16:00. No later information found.

## Verdict
**acceptable loss**

## For the engine
- TP1 = the nearest untaken pool at ≥ 1 R, not the furthest named one; cap TP1 distance at the room left in the ADR.
- One trade (one batch) is a lead, not evidence: in-sample test first, pre-registration before any default; no re-tuning on 2024-07 → 2026-11.
