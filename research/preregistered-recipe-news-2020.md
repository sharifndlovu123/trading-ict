# Pre-registration — the recipe on news days, 2020 (the one split never looked at)

Written 2026-11-16, before the 2020 recipe trades were split by news in any way. Until today the news calendar started on 2021-01-07, so no 2020 trade has ever carried a news tag.

## Where the idea comes from
Conditions study 2026-11-16 (`research/regimes/`, review log #52): on the morning recipe's trades from 2021 to 2026, days with a scheduled high-impact release made +0.53 R (n 59) and the other days −0.13 R (n 116); the sign was the same in each of the six years. Found after the fact, on every recipe trade from 2021 on.

## The test (fixed now)
- **Trades:** the morning recipe without a stop buffer (`recipe4: recipe3, mornings only`), three indices, decided in 2020: the rows already in `reports/variants-pd_return-2020-01-02-2021-12-31-recipe4.parquet` (36 trades). Nothing is re-run.
- **News day:** the trade's day has at least one **high-impact** event in `ict_engine/news/us_calendar.csv` as extended today (NFP, CPI, PPI, retail sales, GDP, PCE, FOMC statement / press conference, ISM manufacturing, the Jackson Hole speech).
- **Measure:** mean `r` on news days against the other days.

## Outcomes (decided now)
36 trades cannot reach significance, so this is a direction check, and it is recorded as such.
| Outcome | Condition |
|---|---|
| **Supports** | at least 8 trades in each group, news-day mean R > 0 **and** above the other days' mean by at least 0.2 R |
| **Does not support** | news-day mean R at or below the other days' mean, or ≤ 0 |
| **Unclear** | anything else (including fewer than 8 trades in a group) |
Either way the rule stays a lead for the forward log; "supports" only means the one unseen split points the same way.

Reported beside it: win rates; the split with the volatility state (2020 was mostly high-volatility); ISM-only days separately, since ISM was not in the calendar when the idea was found.

## Result
_(not run)_
