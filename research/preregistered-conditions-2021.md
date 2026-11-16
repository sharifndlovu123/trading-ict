# Pre-registration — the older models by market condition, on 2021 (never run for them)

Written 2026-11-16, before any run of the 2022 model, MMxM or silver bullet on any date in 2021. Sharif approved the order of work that ends with this run ("proceed", 2026-11-16).

## Where the hypotheses come from
Conditions study 2026-11-16 (`research/regimes/`, review log #52): each model's trades on 2020 and 2022-01 → 2026-11 (three indices), cut by the day's conditions (`ict_engine/concepts/regime.py`, known before the day starts). All of it found after the fact.
| | In the condition | On its other days |
|---|---|---|
| Silver bullet on **low-volatility** days | 615 trades, 32.2% win, +0.037 R (positive in 3 of 6 years) | 2,297 trades, −0.070 R |
| 2022 model on **trending-up** days | 517 trades, 29.2% win, −0.195 R (z −3.4; negative in 5 of 6 years) | 2,200 trades, −0.057 R |
| MMxM on **high-volatility** days | 522 trades, 33.0% win, +0.079 R (positive in 3 of 5 years) | 1,079 trades, −0.023 R |

## The run
The three models at their defaults, futures cost, US100 / US500 / US30, **2021-01-04 → 2021-12-31**. 2021 was a calm bull year: of its index-days 59% were low-volatility, 32% normal, 9% high; 28% trending up, 69% consolidating.

## Hypotheses and outcomes (fixed now)
| # | Hypothesis | Confirmed when | Otherwise |
|---|---|---|---|
| H1 | Silver bullet does better on low-volatility days | ≥ 60 trades in each group; mean R on low-volatility days > 0 and above the other days with one-sided Welch z ≥ 2.4 | same sign, z below 2.4: "leans the same way"; opposite sign: "not supported" |
| H2 | The 2022 model does worse on trending-up days | ≥ 60 trades in each group; mean R on trending-up days below the other days with one-sided z ≥ 2.4 | same sign: "leans the same way"; opposite: "not supported" |
| H3 | MMxM does better on high-volatility days | ≥ 30 trades on high-volatility days (2021 has few such days); mean R > 0 and above the other days with z ≥ 2.4 | fewer than 30: "too few to judge" |
Three hypotheses, so 2.4 is the bar for each. A confirmed H1 or H3 makes the condition a candidate gate through the change gate; a confirmed H2 makes "skip trending-up days" a candidate gate for the 2022 model.

Reported beside them, with no bearing on the outcomes: each model's plain result on 2021 (its first out-of-sample year here), by index; the same conditions cut for backdrop, state and news.

## After the run
A written review of at least 30 of the 2021 trades (15 winners, 15 losers, spread over the three models).

## Result
_(not run)_
