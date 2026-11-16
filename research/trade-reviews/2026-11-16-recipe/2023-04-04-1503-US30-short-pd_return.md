# US30 short — Tue 04 Apr 2023 15:03 NY · −1.00 R (stopped 16:13) · day-only −1.00 R · engine −0.81 R (time exit)

Engine pd_return trade, full-recipe variant, in-sample. Fact sheet: `../sheets/2026-11-16-recipe/2023-04-04-1503-US30-short-pd_return.md`. The sheet does not print the POI's bounds, the time the area was reached, or the 15m gap: the POI is inferred from the arrays and the stop (= the reaction extreme); the 15m gap and its displacement candle were measured for this review from the 1m bars before the entry (known at the entry, but not on the sheet).

## What they tried to do
A short late in the NY PM killzone, after a morning that took four sellside pools. Area: the 1h bearish FVG 33365.27–33440.50, reached to its 50% (33402.9) by the 13:30 high 33411.30. 15m bearish FVG 33365.00–33365.70 (0.7 pt) closed at 14:45; limit 33365.00, stop 33411.30, TP1 = 1h swing low 33307.70 (1.24 R), TP2 = previous day low 33247.70.

## What happened
Filled 15:03, MFE +0.86 R, then back up; the engine closed it at the window end (−0.81 R), the sheet's replay is stopped at 16:13. Price topped at 33434.29 at 20:02 and reached +1.17 R by Wed 06:00.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | partial | ny_pm_kz / sb_late, 15:03; activity normal but slow (0.72×), net move 0.04 ADR |
| 2 | Bias / narrative | pass | read ltf_pullback, side bear; weekly and daily bear; short = read |
| 3 | Dealing range | fail | 0.301 of the 1d range 33247.70–33637.26 = discount, the wrong half; the read: pulled back 0.26, "shallow" |
| 4 | POI / array | partial | 1h bearish FVG 33365.27–33440.50 under the 4h bearish FVG 33396.50–33547.74 and the 1w FVG 33409.00–33466.06; entry at its bottom edge; 1d bullish IFVG top 33334.28 is 31 pts below |
| 5 | Liquidity before | fail | sellside taken four times (09:03–11:16), no buyside; 1h swing high 33411.30 untaken |
| 6 | Trigger | fail | 15m gap 0.7 pt (0.001 ADR); filled 18 min after it closed; no momentum in the hour |
| 7 | Stop | fail | stop on the 1h swing high 33411.30 (sits at the liquidity), inside the area (top 33440.50); risk 0.083 ADR |
| 8 | Targets | partial | TP1 just past the 1h swing low 33307.70, 1.24 R; previous day low 0.18 ADR away |
| 9 | Management | n/a | TP1 not reached |
| 10 | Attribution | fail | right side, late and shallow, stop inside the area = the lesson |

## Does this look like Sharif's recipe?
- **(a) At a 1h / 4h area, in the right half?** At the area, yes: the 1h FVG was reached past its 50%. Wrong half: discount 0.30 of the daily range; the deeper 4h FVG 33396.50–33547.74 (0.40–0.77 of the pullback) was barely touched.
- **(b) With the current momentum?** Mixed. The 1H and 4H structure lines still read bull (against). The day itself was selling: four sellside pools taken by 11:16, daily and weekly bear. The last hour was slow (0.72×, net 0.04 ADR).
- **(c) After a real displacement?** No. A 0.7-point 15m gap in a slow hour; risk only 0.083 ADR.
- **(d) What Sharif would most likely say:** "Short is nice, but you're shorting quite late — the move was the morning. Be patient for the 4h FVG."

## Price we should have looked at
- **The turn:** 33434.29 at 20:02 (5 h after the entry, after the day-only exit; the top of the same pullback) = 0.124 ADR above our entry, 0.041 ADR beyond our stop. From there 0.22 ADR down.
- **Level there, known at entry:** yes — inside the 1h FVG (top 33440.50), the 4h bearish FVG 33396.50–33547.74 and the 1w FVG 33409.00–33466.06.
- **Where to price it:** stop beyond the area's far edge 33440.50 (`stop_mode="array"`); it would have held by 6 pts.

## What they missed / should have seen (known at the entry)
- The stop sat inside the area it was trading from, under a 4h and a weekly bearish FVG.
- A 0.7-pt gap is not momentum.
- Four pools already taken our way: the entry was late in the day's move.

## What the market did (hindsight — lessons to test, not blame)
- Stopped in the evening session by 23 pts, then +1.17 R the next morning.

## Verdict
**lesson loss.** Right side, wrong time and stop: late, shallow, and the stop inside the area.

## For the engine
- A minimum size for the 15m trigger gap (`min_trigger_gap_bp` exists; test it at ≈ 0.03 ADR) and `stop_mode="array"` when the reaction extreme is inside the area. In-sample first. One trade is a lead, not evidence.
