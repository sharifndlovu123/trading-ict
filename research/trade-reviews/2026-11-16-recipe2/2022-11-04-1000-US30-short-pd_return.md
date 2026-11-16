# US30 short — Fri 04 Nov 2022 10:00 NY · -1.02 R (stop 10:10) · day-only -1.00 R
Engine trade, variant recipe2 (full + not against 1h&4h + within 0.25 ADR + before 14:00). Fact sheet: `../sheets/2026-11-16-recipe2/2022-11-04-1000-US30-short-pd_return.md`.

## What they tried to do
Sell a 4h bearish FVG 32207.00–32492.24 (0.41 ADR wide) on NFP day. Its 50% (32349.62) was reached at 09:13, high 32371.30; the 09:30 15m candle dropped and left a gap 32292.27–32316.05. Limit 32292.27, stop 32371.30 (79 pts, 0.114 ADR), TP1 the 5m swing low 32123.20 (2.14 R), runner PDL 31708.70. 4h bear, 1h and daily bull, weekly bear.

## What happened
Filled 10:00, best 0.11 R, stopped 10:10. Price ran to 32605.78 at 10:41 (0.34 ADR beyond the stop), then fell 0.98 ADR; TP1 traded at 11:50.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz, sb_am; activity normal (0.98×); NFP 90 min earlier |
| 2 | Bias / narrative | partial | Split: 4h bear, 1h bull (since 06:00), 15m bull, daily bull; the read is counter_weekly bull — the short is against where price is now |
| 3 | Dealing range | pass | 0.82 of the 1d range 28627.03–33075.50: premium |
| 4 | POI / array | partial | 4h FVG entered only to 58%. Bigger arrays start right above the stop: 1w bearish FVG 32367.09–33515.58, 1d bearish IFVG 32382.77–32588.24 |
| 5 | Liquidity before | pass | Buyside taken all morning (1h highs 05:01–06:51, PDH 32241.78 at 07:09) — a run up, not a single sweep |
| 6 | Trigger | partial | A 2.7× candle (body 0.80) with a 0.034 ADR gap: a reaction, not yet a shift — the 1h was still bull |
| 7 | Stop | fail | 79-pt stop (0.114 ADR) on the session high with the last hour's range at 0.36 ADR, and directly under the weekly FVG's low edge 32367.09 |
| 8 | Targets | pass | 2.14 R to a 5m swing low, nothing in the way; runner to PDL |
| 9 | Management | n/a | Stopped |
| 10 | Attribution | fail | Too early under a bigger area, stop inside the noise + loss |

## Does this look like Sharif's recipe?
**partly.** Area reached to its 50%: yes. Side: split — with the 4h, against the 1h and the daily. 15m: a decent candle, small gap. Timing: too early — price had only reached the middle of the 4h FVG while the weekly FVG and daily IFVG began just above. He would most likely say: "the short was way too early, this is back to the premium pricing — be a little more patient".

## Price we should have looked at
Same-swing turn: **32605.78 at 10:41** — 0.451 ADR past the entry, 0.337 ADR beyond the stop: 17 pts over the top of the 1d bearish IFVG (32588.24), above the 4h FVG's far edge 32492.24, inside the 1w bearish FVG. All on the sheet at entry.

## Look-ahead and realism check
- 15m FVG's third candle closed before the decision: **yes** (candles 09:15 / 09:30 / 09:45, third closed 09:59; decided 09:59, all 15 one-minute bars present).
- Fill after the decision: **yes** (decided 09:59 → filled 10:00; the first 1m bar after the decision that reaches the limit).
- Could the limit fill: **yes** — fill bar high 32335.26 (43 pts, 0.54 R through); 152 pts within 15 minutes.
- Stop distance vs cost: risk 0.114 ADR, cost 0.024 R (futures basis). The stop is small for the hour (a third of the last hour's range).
- Anything from after the decision in the row: **no** — stop = the extreme between the area's 50% (09:13) and 09:59; TP1 5m swing low printed 09:50, known 09:59 — the same minute as the decision (allowed: known ≤ decided); the area was formed 2 Nov 21:59. 
**Realism: ok.**

## What the market did (hindsight — lessons to test, not blame)
- Stopped in 10 minutes, then TP1 at 11:50 from 0.34 ADR higher.
- Same day, same minute as the US100 short: one idea, two losses (the indices are not independent trades).

## Verdict
lesson loss — sold the middle of the 4h FVG with a tight stop under a weekly and a daily area. Change: when a higher-timeframe array begins within 0.1 ADR beyond the stop, wait for it.

## For the engine
- Gate: no entry when an opposing-side HTF array (1d/1w) starts within 0.1 ADR beyond the stop (or move the stop beyond it and re-check R:R); and count same-minute trades on correlated indices as one in the z-score. In-sample first.
