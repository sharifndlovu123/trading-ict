# Patterns — reports/trade-facts-US100-2022-01-03-2024-06-28-futures.parquet

Judged on: mean R · Traits: side, weekday, hour, window, quarter, bias, news, news_mins, news_today, tp1_name, arm, reentry, weekly_trend, tp1_only, liquidity_kind, fvg_size, k_side_matches_read, k_read_kind, k_right_half, k_in_ote, k_range_depth, k_swept_before, k_swept_our_side, k_stop_beyond_pool, k_stop_at_liquidity, k_stop_gap_adr, k_pools_before_tp1, k_tp1_just_past_pool, k_risk_adr, k_rr_tp1, k_news_within_30m, k_momentum, k_range_tf

Base: 573 trades · win 33.5% · mean -0.014 R · period 2022-01-03 → 2024-06-28 · tests run: 79

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| LEAN MORE | k_risk_adr=0.051–0.387 | 188 | 43% [36%–50%] vs 29% | +0.210 vs -0.123 | +0.334 (+0.374 capped) | +2.1 | yes | 1/1 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| LEAN LESS | news_mins=-45–237 | 48 | 23% [13%–37%] vs 34% | -0.463 vs +0.027 | -0.490 (-0.460 capped) | -2.9 | yes | 1/1 |
| LEAN LESS | window=ny_premarket | 108 | 22% [15%–31%] vs 36% | -0.402 vs +0.076 | -0.478 (-0.445 capped) | -2.6 | yes | 1/1 |
