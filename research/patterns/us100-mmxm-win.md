# Patterns — reports/trade-facts-mmxm-US100-2022-01-03-2024-06-28-futures.parquet

Judged on: win rate (TP1 before the stop) · Traits: model, side, weekday, hour, window, quarter, bias, news, news_mins, news_today, tp1_name, reentry, weekly_trend, tp1_only, fvg_size, k_side_matches_read, k_read_kind, k_right_half, k_in_ote, k_range_depth, k_swept_before, k_swept_our_side, k_stop_beyond_pool, k_stop_at_liquidity, k_stop_gap_adr, k_pools_before_tp1, k_tp1_just_past_pool, k_risk_adr, k_rr_tp1, k_news_within_30m, k_momentum, k_range_tf

Base: 221 trades · win 31.7% · mean +0.024 R · period 2022-01-11 → 2024-06-25 · tests run: 58

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| LEAN MORE | k_risk_adr=0.02–0.0653 | 74 | 43% [33%–55%] vs 26% | +0.458 vs -0.194 | +0.174 (+0.174 capped) | +2.6 | yes | 1/1 |
| LEAN MORE | k_rr_tp1=1.01–1.54 | 74 | 41% [30%–52%] vs 27% | -0.031 vs +0.052 | +0.133 (+0.133 capped) | +2.0 | yes | 1/1 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO LESS | k_rr_tp1=2.51–14.5 | 74 | 18% [11%–28%] vs 39% | -0.077 vs +0.075 | -0.212 (-0.212 capped) | -3.2 | yes | 1/1 |
