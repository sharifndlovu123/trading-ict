# Pre-registration — order flow against the trade in the last 30 minutes, NQ 2024-H2

Written 2026-11-16, before the feature was computed on any trade after 2024-06-28. Sharif approved spending the hold-out on 2026-11-16 ("proceed with 1–3").

## Where the idea comes from
Microstructure study 2026-11-16 (`research/microstructure/2026-11-16-study.md`, review log #41), US100 trades 2024-01-02 → 2024-06-28 with NQ futures flow: trades entered after 30 minutes of aggressor flow **against** them earned +0.269 R, those entered after flow **with** them −0.161 R (Δ −0.43 R, z −1.7, n 246, same sign in both quarters). The earlier pre-registered H2 on 2024 (5-minute window) pointed the same way and failed (z −0.54). The study's own expectation: this fails.

## The test (fixed now)
- **Feature:** `imb30` = (buy − sell) / (buy + sell) of NQ aggressor volume over the 30 minutes before the fill, sign flipped for shorts (> 0 = flow with the trade). `research/scripts/micro_features.flow_imbalance(flow, filled_at, 30, side)`, flow = `data/orderflow/NQ-flow1m-2024.parquet`. Known at the fill.
- **Cuts:** the first-half terciles, unchanged: **against** = imb30 ≤ −0.014, **with** = imb30 ≥ +0.025.
- **Trades:** US100, fills 2024-07-01 → 2024-12-31, models 2022 model, MMxM and silver bullet at their defaults, futures cost, from the existing runs `reports/backtest[-mmxm|-silver_bullet]-US100-2024-07-01-2026-11-12-futures.parquet` (made 2026-11-14, before this idea existed). Cameron is parked and left out. Outcome = `r` (all out at TP1, the vote measure).
- **Hypothesis:** mean R(against) > mean R(with).
- **Pass:** at least 30 trades in each group and one-sided z ≥ 2.4, standard errors clustered by trading day.
- **Reported beside it, not part of the bar:** win rates, the middle tercile, Q3 vs Q4, each model.

## What each outcome means
- **Pass:** `imb30` becomes a tag on backtest rows and a candidate gate ("no entry after 30 minutes of flow with the trade") through the change gate. It could only be used live or on data with futures trades (NQ 2024 today; more needs paid data).
- **Fail:** logged; order flow stays a review aid. The 2024-H2 flow split is not reused for this idea.

Price outcomes on 2024-07+ have been looked at many times (the forward runs). The flow split on that period has only been used once before, with a different window (5 minutes, H2 of the first order-flow pre-registration).

## Result
_(appended after the single run)_
