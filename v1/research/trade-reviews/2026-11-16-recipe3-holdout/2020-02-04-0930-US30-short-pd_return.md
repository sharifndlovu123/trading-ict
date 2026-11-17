# US30 short — Tue 04 Feb 2020 09:30 NY · engine −1.06 R (stop) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, hold-out run of `recipe3: recipe2 + fresh areas only` (pre-registration `research/preregistered-recipe2-2020-2021.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe3-holdout/2020-02-04-0930-US30-short-pd_return.md`; row in `reports/recipe3-holdout-US30-2020-01-02-2021-12-31.parquet`. Entry 28771.57 · stop 28802.90 · TP1 28705.87 (5m swing low, 2.1 R) · risk 0.103 ADR · ADR 303.73.

## What they tried to do
Counter-trend short on the second day of a sharp rebound. Daily bull, 1H bull since 03:00, only the 4H still bear. The 4h bearish FVG 28762.90–28821.23 (0.19 ADR, from 31 Jan) was reached to its 50% at 08:44, high 28802.90 at 08:58. The 09:00 15m candle fell 32 points and left a gap 28771.57–28780.32. Limit at its bottom, stop on 28802.90, TP1 a 5m swing low 28705.87 (2.1 R).

## What happened
Filled in the 09:30 opening minute (28 ticks through), spiked to 28799.47 on the same bar, dipped to +0.96 R at 09:32, then the open drove up: stopped 09:35. Day high 28903.97; the rally ran to the previous month high the next evening (−20 R).

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz; normal hour (0.18 ADR); filled on the 09:30 opening bar; calendar has no 2020 rows, so the sheet's 'news: none' is a blank, not a fact |
| 2 | Bias / narrative | fail | against the daily (bull) and the 1H (bull since 03:00); the engine read (bull) disagrees with the side; momentum 0.53 ADR per 4h candle up |
| 3 | Dealing range | pass | 0.509 of the daily range 28119.70–29400.90: just in premium |
| 4 | POI / array | pass | one 4h bearish FVG, 0.19 ADR, 4 days old, first reach of its 50% (69% deep) |
| 5 | Liquidity before | pass | buyside 1h swing high 28762.90 at 07:30, on the way into the area |
| 6 | Trigger | partial | 15m candle body 0.105 ADR (2.2×), gap 8.75 points (0.029 ADR): modest, pre-open |
| 7 | Stop | partial | on the session high 28802.90, no buffer; risk 31 points (0.10 ADR) into the cash open |
| 8 | Targets | pass | 5m swing low 28705.87 at 2.1 R, nothing in the way |
| 9 | Management | pass | stop honoured |
| 10 | Attribution | fail | counter-momentum side, tight stop at the open + loss = the lesson |

## What they missed / should have seen (known at the entry)
- 'The no. 1 focus is where we currently are': daily bull, 1H bull, a 0.5 ADR-per-candle rebound. The short had only the 4h state for it.
- A 31-point stop under a session high, entered one minute before the cash open of an index with a 304-point ADR.

## What the market did (hindsight — lessons to test, not blame)
- The day's high was 28903.97 at 14:11, 0.33 ADR beyond the stop, 4 points under the 1h swing high 28908.00; no sell worked that day or the next.
- The sheet's 'turn' (28799.47 at 09:30) is the fill bar's spike, five minutes before the stop.

## Does this look like Sharif's recipe?
- **Area:** 4h FVG, 0.19 ADR, fresh, reached to its 50% (69%).
- **Side:** with the 4h only; against the 1h and the daily.
- **15m:** a modest gap (0.03 ADR) before the open; passes the size test, not a momentum shift.
- **Early or late:** early in the session (09:30 bar), inside the area at its low edge.
- **What he would most likely say:** "wrong side: the momentum is buying heavy; the bias was read too rigidly off the 4h" (my reading of his notes, not his words).
- **Verdict:** partly.

## Price we should have looked at
no same-swing turn; day high 28903.97 at 14:11: 0.436 ADR against the entry, 0.333 ADR beyond the stop. Level there: 1h swing high 28908.00, previous week high 28932.50 above it. Known at the entry.

## Realism
- **15m gap closed before the decision?** Yes. Candles 08:45 / 09:00 / 09:15; the third has all 15 one-minute bars and ends with the 09:29 bar = `decided_at`. Gap 28771.57–28780.32 = 8.75 points (0.029 ADR, 8.8 ticks), re-derived from 1m bars; the entry is its near edge. Middle candle body 0.105 ADR = 2.23× the mean of the 20 before, 74% of its range.
- **Area known before it was used?** Yes. 4h FVG 28762.90–28821.23 (0.192 ADR), middle candle 01-31 02:00, complete 01-31 10:00; its 50% (28792.07) first traded 02-04 08:44 (not on an earlier day); no 1m close beyond the far edge before the decision. Stop = the extreme between that reach and the decision (28802.90 at 08:58), re-derived: matches.
- **Entry more than 4 ticks through the limit?** Fill bar 09:30 (1 min after the decision) traded 27.9 ticks through; 37.1 ticks through at most during the hold. Passes.
- **Stop:** traded 5.8 ticks through on the exit bar; TP1 after the stop that day: no.
- **Anything from after the decision?** None found: the stop extreme (08:58) and the TP1 level (printed 02-04 07:04) precede the decision; 5m swings are confirmed one candle later (`swings`, strength 1). News fields are empty because `us_calendar.csv` starts in 2021, not because nothing was scheduled; the news gates are off, so the rule is unaffected.
- Filled on the 09:30 bar, 28 ticks through: real. Stopped 09:35, 6 ticks through.
- **Result:** no problem found.

## Verdict
**lesson loss** — most useful change: no short against a 1H + daily bull rebound on the 4h state alone.

## For the engine
- `structure_gate='not_against'` lets a trade through when one of 1h/4h agrees. A 'the 1h must agree' version removes 2 losers (this one, 10 Mar) and 2 winners (both 8 Jan trades) in this batch: no help here; count it across all 77.
- One trade is a lead, not evidence: count it across the whole run first; nothing is re-tuned on 2020–2021.
