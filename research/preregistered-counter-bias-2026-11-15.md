# Pre-registered: the second trade of the day — counter-bias setups after the day's draw is reached (written 2026-11-15, before any code or run)

Models: the 2022 model and MMxM. Source: Sharif's old trade NQ Sep 25 2023 (review log #22; in-sample): the 2022 model
took the 10:02 short to the same low he targeted (+1.98 R), but his 11:00 long — from a near-equal low that *added*
sellside — was found by the engine (11:05) and blocked by the daily bias (prev_day_dol bear). Sharif: the cycle doesn't
always complete, "if your on the wrong side, the consolidation we pointed might be a reversal point for a bigger trade,
but BIAS plays a big role" (#20); key times matter more than zones (#21). Idea: once the day's bias-direction move has
been delivered, the next key window may reverse.

## Variants (everything else at the model's defaults)
A setup is **admitted** only if the daily bias gate is the *only* gate it failed (time window, pricing, POI, trigger,
target, cost, news and the one-trade-per-window / no-overlap rules all still apply). The bias side is the side the bias
gate wanted (the opposite of the setup's side).

| name | admit a counter-bias setup when, before its decision … |
|---|---|
| counter: after a bias trade's TP1 | a trade of the same model in the bias direction, filled earlier the same day, has traded to its TP1 |
| counter: after the daily draw | price has traded through the previous day's level on the bias side since 18:00 the evening before (bear bias → below PDL; bull → above PDH) |

Both are judged with bars before the decision only.

## Measure and decision rule
These rules add trades (and can displace a later one through the window cap), so expectancy per trade is the wrong
yardstick. Measure per asset-day: **ΔR = (sum of `runner_r` of the variant's trades) − (the same for the baseline)**,
over the days where the trade list differs ("changed days"). Futures basis; US100 US500 US30 XAUUSD XAGUSD,
2022-01-03 → 2024-06-28; out-of-sample = days from 2023-09-29 (the variants tool's 70/30 split).
2 variants × 2 models = 4 cells: **pass = OOS mean ΔR per changed day > 0 with z ≥ 2.4 over ≥ 30 changed days.**
Reported beside it: the admitted trades (n, win rate, expectancy) and the displaced baseline trades. Every cell is
reported. A pass becomes a forward-v2 candidate.
