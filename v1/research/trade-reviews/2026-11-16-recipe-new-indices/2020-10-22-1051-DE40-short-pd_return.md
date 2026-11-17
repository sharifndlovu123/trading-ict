# DE40 short — Thu 22 Oct 2020 10:51 NY · engine −1.03 R (stop 11:14) · sheet −1.00 R · day-only −1.00 R
Engine pd_return trade, the unchanged recipe (`recipe4`) on indices it had never seen (`research/preregistered-recipe-new-indices.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe-new-indices/2020-10-22-1051-DE40-short-pd_return.md`; row in `reports/recipe-new-indices-trades.parquet`. Entry 12483.30 · stop 12543.90 · TP1 12380.27 (5m swing low, 1.70 R) · risk 0.27 ADR · ADR 224.9. POI 1h FVG 12538.90–12544.75. Decided 10:44, filled 10:51.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_am_kz + sb_am + 10:50 macro, busy 1.59×, no release; but the fill is 39 minutes before the Xetra close |
| 2 | Bias / narrative | pass | aligned: weekly, daily, 4H, 1H all bear; monthly equal lows 12273.78 resting below |
| 3 | Dealing range | fail | 0.167 of the 4h range 12342.26–13184.60: deep discount for a short. The London low 12342.26 had held 5 pts above the previous month low 12337.20 at 03:13 and price had rallied 1.0 ADR since |
| 4 | POI / array | partial | 1h bearish FVG 12538.90–12544.75 is 5.9 pts (0.026 ADR); 50% reached 10:00–10:06 (high 12543.90), far edge not. A 1d bullish IFVG 12171.60–12461.46 lies 22 pts under the entry |
| 5 | Liquidity before | partial | buyside taken (1h swing high 12514.30, Asia high 12520.00 at 06:16), but four hours earlier and price kept going to 12586.20 |
| 6 | Trigger | pass | 10:15 candle −0.19 ADR; gap 24.96 pts (0.111 ADR) between the 10:00 low 12508.26 and the 10:30 high 12483.30 |
| 7 | Stop | partial | on the 10:00 reaction high; the session high 12586.20 is 0.19 ADR beyond (short of the pool, not on it) |
| 8 | Targets | partial | TP1 12380.27, 1.70 R; the last-4h low 12458.29 is 25 pts under the entry (0.4 R) and the daily bullish IFVG starts at 12461 |
| 9 | Management | n/a | MFE +0.19 R; stopped in 23 minutes |
| 10 | Attribution | partial | aligned side and a real displacement, wrong half and late in the instrument's day + loss |

## Market conditions
Known before the day: volatility **normal**, state **consolidating**, backdrop **mixed**, no release, not Monday. The DAX made its day in its own morning: 03:00–06:59 ranged 1.0 ADR, low 12342.26 at 03:13 just above the previous month low, then up all day (net +0.52 ADR, high 12605.8 at 14:16). The New York dip 09:30–10:33 was the pullback. Day type: **trend day** (up, a reversal from the London low).

## Why it lost
The short sold the low of a pullback in an up day. The fill bar was already the bounce; the 10:45 and 11:00 candles (+0.16, +0.21 ADR) went straight back through the gap and the stop at 11:14, into the Xetra close. Price then took the session high 12586.20 at 13:14. The higher timeframes said bear; the day said the sellside had been defended.

## Instrument notes
- The DAX day (range, low, reversal) was done between 03:00 and 08:00 New York. The recipe's morning window meets it in its last two hours, when it is pulling back or closing out.
- Fill 39 minutes before the cash close; the last 30 minutes ran against the trade.
- The named area is 6 pts on a 12,500 index.

## Would Sharif take it?
Area: yes (small). 15m momentum: yes. Side: HTF bear, but price that day was rallying from a defended low. Right half: no (0.17). **No** — a short at the bottom sixth of the range after the low held.

## Verdict
**acceptable loss** — the rule was followed; the lesson is location and the DAX clock. One trade is a lead, not evidence.

## For the engine
- For DE40/UK100 test the same recipe in the instrument's own morning (03:00–06:00 NY) against the NY window, pre-registered; report NY-window trades by where the session low/high was made. Check on all 193 trades before believing it; nothing is re-tuned on this run.
