# Patterns — reports/trade-facts-silver_bullet-US100-2022-01-03-2024-06-28-futures.parquet

Judged on: mean R · Traits: side, weekday, hour, window, quarter, bias, news, news_mins, news_today, tp1_name, reentry, weekly_trend, tp1_only, fvg_size, k_side_matches_read, k_read_kind, k_right_half, k_in_ote, k_range_depth, k_swept_before, k_swept_our_side, k_stop_beyond_pool, k_stop_at_liquidity, k_stop_gap_adr, k_pools_before_tp1, k_tp1_just_past_pool, k_risk_adr, k_rr_tp1, k_news_within_30m, k_momentum, k_range_tf

Base: 461 trades · win 30.4% · mean -0.002 R · period 2022-01-03 → 2024-06-28 · tests run: 68

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| LEAN MORE | k_risk_adr=0.0463–0.085 | 154 | 36% [29%–44%] vs 27% | +0.299 vs -0.153 | +0.451 (+0.434 capped) | +2.2 | yes | 1/1 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| LEAN LESS | k_read_kind=aligned | 113 | 26% [19%–34%] vs 32% | -0.323 vs +0.102 | -0.425 (-0.417 capped) | -2.6 | yes | 1/1 |
| LEAN LESS | k_stop_gap_adr=0.015–1.16 | 152 | 24% [18%–32%] vs 33% | -0.271 vs +0.130 | -0.401 (-0.393 capped) | -2.3 | yes | 1/1 |
