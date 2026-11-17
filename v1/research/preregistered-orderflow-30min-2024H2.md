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
Run once, 2026-11-16 (`research/scripts/flow30_holdout.py`), 229 US100 trades, 2024-07-01 → 2024-12-31:

| Group | n | Win % | Mean R |
|---|---|---|---|
| Flow against the trade (imb30 ≤ −0.014) | 90 | 31.1 | −0.109 |
| Middle | 76 | 25.0 | −0.288 |
| Flow with the trade (imb30 ≥ +0.025) | 63 | 30.2 | −0.088 |

Against − with: **−0.021 R, one-sided z −0.08 (day-clustered). FAIL** (needs 2.4). Q3: against −0.257 vs with +0.007; Q4: +0.038 vs −0.181 (the sign flips). Per model: 2022 model −0.248 vs +0.121; MMxM −0.023 vs −0.230; silver bullet +0.007 vs −0.148.

**Outcome:** the first-half difference (+0.27 vs −0.16 R) was noise. Order flow stays a review aid; no tag or gate is added. Not reused for this idea.
