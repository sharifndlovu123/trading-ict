# 30 trades of the older models on 2021 reviewed (15 winners, 15 losers)

The run: the 2022 model, MMxM and silver bullet at their defaults on 2021, three indices, their first run on that year (`research/preregistered-conditions-2021.md`): −0.09 / +0.03 / −0.10 R; the two conditions hypotheses with enough trades were not supported. Two reviewers, 15 trades each, with each day's market conditions. 30 hand-picked trades are leads; the "would Sharif take it" grade was made knowing the outcome.

## What the reviewers found
**No look-ahead** on any of the 30.

**Losers (15)**
- **12 of 15 were stopped and then TP1 traded.** In most the turn was at a pool or array already on the map, 0.02–0.14 ADR beyond the stop. The stop sat on or in front of a pool in nearly every trade (the stop step fails in 14 of 15 in one batch).
- The rest: wrong side for the day (a counter-HTF short before NFP, fading the FOMC rally, a short into a busy sell-off's bounce), premium longs with the array below, a late short in discount after the sweep had already happened.
- Risk of 0.02–0.03 ADR on four of the losers; entry gaps under a point on several.

**Winners (15)**
- About half are graded lucky: stops of 6–24 points that survived by under two points, targets 9–45 points away, on quiet or range days.
- The earned ones look alike across the three models: entry at or inside a 4h / 1d array or straight after a pool run, a 15m shift, and the turn within 0.05 ADR of the entry.

**Would Sharif take it?** (area first, then 15m momentum, the side of where price is now, the right half of the range)
| | Winners | Losers |
|---|---|---|
| Yes or maybe (10 trades) | 7 | 3 |
| No (20 trades) | 8 | 12 |
The three "maybe" losers each turned within 0.05 ADR beyond the stop: his later entry, after the area is tagged and the 15m turns, would have been in after that. Small numbers and graded with hindsight, but it is the same picture as the recipe reviews: the trades that fit his description do better than the rest of what these models take.

**Market conditions:** the label known in the morning separated little. What separated outcomes was the kind of day it became: days that turned volatile on a release lost for all three models (0 wins of 5 in one batch), quiet and range days produced the small-target wins. MMxM on high-volatility mornings: 2 wins, 1 loss (by 0.16 points), the same direction as the hypothesis that had too few trades.

## Flags
- Fills on a touch (0.002–0.09 points through the limit on two trades); a stop that survived by 0.16 points; a stop hit on the 09:30 bar at its exact price with no slippage.
- Holidays: a win on Martin Luther King Jr. Day (the feed ends 12:59); New Year's Eve not tagged (a thin session worth a tag; Veterans Day is a normal stock-market day).
- Engine FVGs of 0.003–1.0 points; sweeps that are 5–7 hours old or 1-minute swings (the 2022 model).
- Targets 23–27 R away late on a Friday or after FOMC.
- One event counted for two models (the same stop on 18 Oct).
- The vote books the whole position at TP1; with his partials the wins are about half (+1.78 → +0.91 R).
- A time-exit "win" with `vote = False` that is −1 R if held overnight.
