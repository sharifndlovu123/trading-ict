# US30 short — Tue 25 Feb 2020 10:00 NY · engine +1.21 R (TP1) · sheet +1.51 R · day-only +1.51 R
Engine pd_return trade, hold-out run of `recipe3: recipe2 + fresh areas only` (pre-registration `research/preregistered-recipe2-2020-2021.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2020-02-25-1000-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`. Entry 28057.45 · stop 28142.85 · TP1 27951.98 (5m swing low, 1.24 R) · risk 0.225 ADR · ADR 380.01.

## What they tried to do
Second day of the February break: D, 4H, 1H all bear. The 'area' is a 1h bearish FVG 28139.40–28140.25, 0.85 points wide, touched at 07:53 (high 28142.85). The 09:30 15m candle fell 71 points (0.19 ADR, 3×) and left a gap 28057.45–28085.31. Limit at its bottom, stop on 28142.85, TP1 a 5m swing low 27951.98 (1.24 R).

## What happened
Filled 10:00 (16 ticks through), high 28077.98 at 10:01 (−0.24 R), then the floor went: TP1 10:20, PDL 10:24, −2.85 ADR by 15:39 (12 R).

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz + sb_am + macro_0950; busy (0.50 ADR, 1.65×); consumer confidence 10:00 at the fill minute (from memory; calendar has no 2020 rows, so the sheet's 'news: none' is a blank, not a fact) |
| 2 | Bias / narrative | pass | D, 4H, 1H all bear |
| 3 | Dealing range | partial | 0.117 of the 4h range 27873.20–29444.75: deep discount, the wrong half for a short; momentum is the excuse |
| 4 | POI / array | fail | a 0.85-point 1h gap (0.002 ADR): not an area. Entry 0.22 ADR below it |
| 5 | Liquidity before | fail | none in the 6 h before |
| 6 | Trigger | pass | real 15m displacement off the 09:30 open: body 0.19 ADR (3.0×), gap 28 points (0.07 ADR) |
| 7 | Stop | partial | on the 1h swing high 28142.85, no buffer; risk 0.225 ADR |
| 8 | Targets | pass | 5m swing low 27951.98 at 1.24 R, in front of the 4h swing low 27919.88 and the PDL 27905.49 |
| 9 | Management | pass | half off at TP1, the rest at the PDL (sheet +1.51 R); the engine's runner made +1.48 R |
| 10 | Attribution | fail | right side and trigger, but the model's reason (the area) was not there = lucky win |

## What they missed / should have seen (known at the entry)
- The POI was a rounding error: 0.85 points. What actually carried the trade was the wave (all timeframes bear) and the 09:30 displacement.

## What the market did (hindsight — lessons to test, not blame)
- The retest turned at 28077.98, inside the 15m gap (top 28085.31), 0.05 ADR above the fill.
- 12 R of range that day; TP1 at 1.24 R and a breakeven runner kept 1.5 R of it.

## Does this look like Sharif's recipe?
- **Area:** a sliver (0.002 ADR), fresh in name only.
- **Side:** with the 1h, 4h and daily.
- **15m:** a real displacement.
- **Early or late:** late in the leg: selling at 0.12 of the 4h range, 0.22 ADR below the 'area'.
- **What he would most likely say:** "nice, you rode the wave on the displacement; but that isn't an area, and you're selling low" (my reading of his notes, not his words).
- **Verdict:** partly.

## Price we should have looked at
28077.98 at 10:01 (same day, same as the sheet): 0.054 ADR against the entry, 0.171 ADR inside the stop. Level there: inside the 15m gap 28057.45–28085.31 (the sheet's map has no level there). Known at the entry.

## Realism
- **15m gap closed before the decision?** Yes. Candles 09:15 / 09:30 / 09:45; the third has all 15 one-minute bars and ends with the 09:59 bar = `decided_at`. Gap 28057.45–28085.31 = 27.86 points (0.073 ADR, 27.9 ticks), re-derived from 1m bars; the entry is its near edge. Middle candle body 0.186 ADR = 2.95× the mean of the 20 before, 56% of its range.
- **Area known before it was used?** Yes. 1h FVG 28139.40–28140.25 (0.002 ADR), middle candle 02-25 03:00, complete 02-25 05:00; its 50% (28139.83) first traded 02-25 07:53 (not on an earlier day); no 1m close beyond the far edge before the decision. Stop = the extreme between that reach and the decision (28142.85 at 07:54), re-derived: matches.
- **Entry more than 4 ticks through the limit?** Fill bar 10:00 (1 min after the decision) traded 16.5 ticks through; 20.5 ticks through at most during the hold. Passes.
- **TP1 traded through or just touched?** Through: 9.0 ticks on the exit bar, 223.0 ticks within 30 minutes.
- **Anything from after the decision?** None found: the stop extreme (07:54) and the TP1 level (printed 02-25 09:46) precede the decision; 5m swings are confirmed one candle later (`swings`, strength 1). News fields are empty because `us_calendar.csv` starts in 2021, not because nothing was scheduled; the news gates are off, so the rule is unaffected.
- Fill 16 ticks through, TP1 traded 223 ticks through within 30 minutes: real.
- **Result:** no problem found.

## Verdict
**lucky win** — most useful change: none for the side; the area must be an area.

## For the engine
- Sliver areas: 3 winners and 4 losers under 0.1 ADR in this batch, so the width floor does not separate here. Record `area_adr` on every row so it can be cut across all 163 trades.
- One trade is a lead, not evidence: count it across the whole run first; nothing is re-tuned on 2020–2021.
