# Patterns — reports/trade-facts-silver_bullet-US100-2022-01-03-2024-06-28-futures.parquet

Judged on: win rate (TP1 before the stop) · Traits: side, weekday, hour, window, quarter, bias, news, news_mins, news_today, tp1_name, reentry, weekly_trend, tp1_only, fvg_size, k_side_matches_read, k_read_kind, k_right_half, k_in_ote, k_range_depth, k_swept_before, k_swept_our_side, k_stop_beyond_pool, k_stop_at_liquidity, k_stop_gap_adr, k_pools_before_tp1, k_tp1_just_past_pool, k_risk_adr, k_rr_tp1, k_news_within_30m, k_momentum, k_range_tf

Base: 461 trades · win 30.4% · mean -0.002 R · period 2022-01-03 → 2024-06-28 · tests run: 68

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| LEAN MORE | k_rr_tp1=0.999–1.63 | 154 | 39% [32%–47%] vs 26% | -0.150 vs +0.072 | +0.129 (+0.129 capped) | +2.8 | yes | 1/1 |
| LEAN MORE | weekly_trend=bull | 279 | 34% [29%–40%] vs 25% | +0.109 vs -0.172 | +0.093 (+0.093 capped) | +2.1 | yes | 1/1 |
| LEAN MORE | k_stop_gap_adr=0.001–0.015 | 32 | 47% [31%–64%] vs 29% | +0.634 vs -0.049 | +0.177 (+0.177 capped) | +2.1 | yes | 1/1 |
| LEAN MORE | tp1_name=5m swing high | 195 | 35% [29%–42%] vs 27% | +0.103 vs -0.079 | +0.087 (+0.087 capped) | +2.0 | yes | 1/1 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO LESS | k_rr_tp1=2.67–31.4 | 154 | 18% [13%–25%] vs 36% | +0.005 vs -0.005 | -0.183 (-0.183 capped) | -4.0 | yes | 1/1 |
| LEAN LESS | weekly_trend=bear | 182 | 25% [19%–31%] vs 34% | -0.172 vs +0.109 | -0.093 (-0.093 capped) | -2.1 | yes | 1/1 |
