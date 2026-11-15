# Patterns — reports/trade-facts-cameron-US100-2022-01-03-2024-06-28-futures.parquet

Judged on: mean R · Traits: side, weekday, hour, window, quarter, bias, news, news_mins, reentry, weekly_trend, tp1_only, liquidity, fvg_size, k_side_matches_read, k_read_kind, k_right_half, k_in_ote, k_range_depth, k_swept_before, k_swept_our_side, k_stop_beyond_pool, k_stop_at_liquidity, k_stop_gap_adr, k_pools_before_tp1, k_tp1_just_past_pool, k_risk_adr, k_rr_tp1, k_news_within_30m, k_momentum, k_range_tf

Base: 614 trades · win 23.3% · mean -0.248 R · period 2022-01-03 → 2024-06-28 · tests run: 73

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO MORE | window=london_kz | 397 | 27% [23%–32%] vs 17% | -0.123 vs -0.478 | +0.356 (+0.356 capped) | +2.9 | yes | 1/1 |
| LEAN MORE | k_momentum=0.138–0.294 | 204 | 30% [24%–37%] vs 20% | -0.001 vs -0.371 | +0.370 (+0.370 capped) | +2.6 | yes | 1/1 |
| LEAN MORE | k_rr_tp1=2.23–3.63 | 202 | 27% [21%–33%] vs 22% | -0.011 vs -0.365 | +0.354 (+0.354 capped) | +2.5 | yes | 1/1 |
| LEAN MORE | k_in_ote=False | 526 | 24% [21%–28%] vs 17% | -0.199 vs -0.545 | +0.346 (+0.346 capped) | +2.4 | yes | 1/1 |
| LEAN MORE | hour=3 | 163 | 29% [23%–37%] vs 21% | +0.002 vs -0.339 | +0.341 (+0.341 capped) | +2.2 | yes | 1/1 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO LESS | weekday=Wed | 124 | 15% [9%–22%] vs 26% | -0.587 vs -0.163 | -0.424 (-0.424 capped) | -3.3 | yes | 1/1 |
| DO LESS | window=ny_premarket | 92 | 14% [8%–23%] vs 25% | -0.610 vs -0.185 | -0.425 (-0.425 capped) | -3.0 | yes | 1/1 |
| DO LESS | k_rr_tp1=3.63–19.5 | 205 | 9% [6%–13%] vs 31% | -0.524 vs -0.110 | -0.414 (-0.414 capped) | -2.9 | yes | 1/1 |
| LEAN LESS | hour=7 | 68 | 13% [7%–23%] vs 25% | -0.623 vs -0.202 | -0.421 (-0.421 capped) | -2.7 | yes | 1/1 |
| LEAN LESS | k_in_ote=True | 88 | 17% [11%–26%] vs 24% | -0.545 vs -0.199 | -0.346 (-0.346 capped) | -2.4 | yes | 1/1 |
