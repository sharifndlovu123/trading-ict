# Forward test of the recipe — frozen rules, from the first data after 2026-11-13

Written 2026-11-16, after the recipe failed its clean confirmation on 2024-07 → 2026-11 (`research/preregistered-recipe4b-2024H2-2026.md`) and the conditions study suggested where it works (`research/regimes/`, review log #52–54). Every period on disk has now been used to look at the recipe, so the only clean test left is data that does not exist yet. This file is the same idea as `research/forward-test-protocol.md` (`forward-v1`), for the recipe only, with its own clock.

## Frozen
- **Code:** the commit tagged `forward-recipe-v1`. Bug fixes are allowed only if they change no trade of this variant on 2020-01 → 2026-11 (check by re-running); anything else is a new version with a new clock.
- **The rule:** PD-array-return variant `recipe4: recipe3, mornings only` (`ict_engine/eval/variants.py`): a fresh 1h/4h FVG reached to its 50% → a 15m FVG in its direction within 4 hours → limit at that gap's near edge; stop beyond the reaction extreme (no buffer: the buffer failed); TP1 the nearest untaken liquidity at least 1 R away, 50% off, runner at breakeven; no daily bias; side not against both the 1h and 4h structure; entry within 0.25 ADR of the area; `ny_am_kz` only. Futures cost.
- **Assets:** US100, US500, US30 (his index group; the recipe failed on metals and currencies).
- **Conditions, tagged on every trade from data known before the day starts:** volatility state and backdrop (`ict_engine/concepts/regime.py`); a scheduled high-impact release that day (`ict_engine/news/us_calendar.csv` as of this commit, plus rows added later for dates announced later, e.g. Jackson Hole 2026+); the weekday; the session note (holiday / early close / after holiday). Tagged at the fill: whether the entry is in the right half of the read's range (short in premium, long in discount).

## Candidates (fixed now; nothing else counts as a hit)
| # | Candidate | 2020-01 → 2026-11 record (all of it selection data) |
|---|---|---|
| 1 | Every recipe trade | 212 trades, 35.4% win, +0.122 R |
| 2 | Recipe on a **high-volatility day or a high-impact news day** | 102 trades, 42.2% win, +0.451 R (old calendar; positive in 7 of 7 years) |
| 3 | Candidate 2, **entry in the right half of the range, not a Monday, not a holiday / early-close session** | not computed as one rule before this file was written |

## Logging
```
uv run python research/scripts/forward_recipe.py            # fetches new data, appends new trades, prints counts only
```
Trades are appended to `reports/forward/recipe-forward.parquet` (one row per trade, keyed by asset and decision time) and the counts to `research/forward/recipe-forward-log.md`. Run it weekly or whenever.

## Decision rule (fixed now)
- **First look at R:** when candidate 2 has 60 trades, or on 2027-11-16 (12 months), whichever comes first. Before that the script prints counts only. At roughly 10 trades a year per index and about half of them in candidate 2, 60 trades is likely more than a year away: this is a slow test by design.
- **Pass (per candidate):** mean R > 0 with day-clustered z ≥ 2.5 (three candidates, one-sided, about 5% family-wise) and a win rate reported with its range. **Consistent:** mean R > 0 and positive on at least 2 of 3 indices, z below 2.5. **Fail:** anything else.
- Every trade of the forward window gets a written review at the first look (his rule: more than 60 is welcome).
- A failing candidate is not re-tuned on forward data.
