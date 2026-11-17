# US30 short — Fri 2026-02-20 09:00 NY · engine +0.83 R (TP1; with partials +0.83) · sheet +0.84 R · day-only +0.84 R
Engine pd_return trade, confirmation run of `recipe4b` on 2024-07 → 2026-11 (FAILED: 81 trades, 33.3% win, −0.17 R; `research/preregistered-recipe4b-2024H2-2026.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2026-02-20-0900-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`. Entry 49319.49 · stop 49467.78 · TP1 49194.38 (pdl, 0.84 R) · risk 0.222 ADR · ADR 668.29. Decided 08:59, filled 09:00.

## What they tried to do
Short after GDP+PCE: the 08:30 15m candle displaced down from a 1h bearish FVG 49370.93–49406.94 (36 pts) that had been reached to its 50%; limit at the gap edge 49319.49, stop 0.10 ADR above the reaction high 49400.95, target the previous day low 49194.38 (0.84 R).

## What happened
Decided 08:59, filled 09:00, 0.08 R of heat (49330.96 at 09:03). PDL taken on the 09:30 open: TP1, all out. Low 49150.98 at 09:41, then the day reversed 0.59 ADR up through London high and the 4h swing high (10:01) and closed 2.3 R above the entry.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | decided 29 min after a high-impact release (GDP+PCE 08:30); last hour 1.33× normal |
| 2 | Bias / narrative | partial | weekly + daily bull (read: 'ltf_pullback, side bull', no match); 4H and 1H bear support a short to a near target |
| 3 | Dealing range | fail | 0.437 of the 1d range: discount, wrong half for a short |
| 4 | POI / array | partial | 1h bearish FVG only 0.054 ADR wide, inside a 4h bullish FVG 49051–49621 |
| 5 | Liquidity before | partial | buyside (1h swing high 49509.99) taken at 03:54, five hours earlier |
| 6 | Trigger | pass | news candle body 0.136 ADR, 5.0×; gap 33.7 pts (0.05 ADR) |
| 7 | Stop | partial | stop 49467.78 is 0.025 ADR short of the last-4h high 49484.20 |
| 8 | Targets | partial | TP1 = PDL at 0.84 R, 0.18 ADR away; at the pool, not in front of it |
| 9 | Management | pass | all out at TP1 09:30; price reversed 11 minutes later |
| 10 | Attribution | partial | counter-daily news trade with a near target: a win, half luck |

## What they missed / should have seen (known at the entry)
- A short in discount inside a 4h bullish FVG, against weekly and daily: only a near target justifies it (it had one).

## What the market did (hindsight — lessons to test, not blame)
- After the PDL sweep the day ran 0.86 ADR up from the low: the sweep of the PDL was the day's Judas, and the recipe traded into it.
- A runner would have been stopped at entry.

## Market conditions
- **Known before the day:** consolidating (20-day efficiency 0.004), backdrop bull, volatility normal (1.13× its 1-year median), a scheduled high-impact release that day (GDP+PCE).
- **The day:** range before the decision 0.44 ADR; whole day 0.85 ADR; 09:30–16:55 range 0.85 ADR, net +0.59 ADR. Release day; the numbers gave a 5× displacement candle. RTH net +0.59 ADR after the PDL was taken on the open. The recipe's kind of morning (news, displacement) — and it paid only because the target was 0.18 ADR away.
- **Day type:** volatile/news.

## Does this look like Sharif's recipe?
- **Area:** 1h FVG 49370.93-49406.94, 0.054 ADR wide; entry +0.077 ADR from its near edge (negative = inside it).
- **15m:** middle candle 08:30 body 0.136 ADR = 5.02× the mean of the 20 before; gap 0.05 ADR (33.7 ticks).
- Real 15m displacement and a retrace entry; the area is thin and the side is against the daily.
- **What he would most likely say:** 'I made a different entry based off the displacement at 8:30 am' is his own practice; here he would add that the PDL was the draw and nothing more (my reading).
- **Verdict:** partly.

## Why it won
News displacement with a near target (PDL, 0.18 ADR) taken on the open before the day turned up.

## Price we should have looked at
49330.96 at 09:03: 0.017 ADR above the entry, 0.205 ADR inside the stop; at the 1h bearish volume imbalance 49337.93–49339.49. Known.

## Realism
- 15m gap closed before the decision: yes (candles 08:15 / 08:30 / 08:45, the third ends at 08:59); the entry is the gap's near edge; the stop is the reaction extreme 49400.95 ∓ 0.10 ADR (that price is on the 1m bars before the decision).
- Fill bar traded 4.9 ticks through the limit; price ran 0 R our way between the decision and the fill.
- TP1 traded 43.4 ticks through within 30 minutes.
- TP1 traded 43 ticks through within 30 min.

## Verdict
**lucky win**

## For the engine
- News days: count TP1-near (≤ 0.25 ADR) vs TP1-far outcomes on this run; the regime study's news-day edge may be the near-target trades only.
- One trade is a lead, not evidence; nothing is re-tuned on 2024-07 → 2026-11.
