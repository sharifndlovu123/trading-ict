# Patterns — reports/trade-facts-cameron-US100-2022-01-03-2024-06-28-futures.parquet

Judged on: win rate (TP1 before the stop) · Traits: side, weekday, hour, window, quarter, bias, news, news_mins, reentry, weekly_trend, tp1_only, liquidity, fvg_size, k_side_matches_read, k_read_kind, k_right_half, k_in_ote, k_range_depth, k_swept_before, k_swept_our_side, k_stop_beyond_pool, k_stop_at_liquidity, k_stop_gap_adr, k_pools_before_tp1, k_tp1_just_past_pool, k_risk_adr, k_rr_tp1, k_news_within_30m, k_momentum, k_range_tf

Base: 614 trades · win 23.3% · mean -0.248 R · period 2022-01-03 → 2024-06-28 · tests run: 73

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO MORE | k_rr_tp1=0.999–2.23 | 207 | 34% [28%–41%] vs 18% | -0.207 vs -0.269 | +0.166 (+0.166 capped) | +4.6 | yes | 1/1 |
| DO MORE | k_momentum=0.138–0.294 | 204 | 30% [24%–37%] vs 20% | -0.001 vs -0.371 | +0.106 (+0.106 capped) | +2.9 | yes | 1/1 |
| DO MORE | window=london_kz | 397 | 27% [23%–32%] vs 17% | -0.123 vs -0.478 | +0.104 (+0.104 capped) | +2.9 | yes | 1/1 |
| LEAN MORE | k_pools_before_tp1=0 | 376 | 26% [22%–31%] vs 18% | -0.171 vs -0.371 | +0.078 (+0.078 capped) | +2.2 | yes | 1/1 |
| LEAN MORE | hour=3 | 163 | 29% [23%–37%] vs 21% | +0.002 vs -0.339 | +0.084 (+0.084 capped) | +2.2 | yes | 1/1 |
| LEAN MORE | k_tp1_just_past_pool=False | 385 | 26% [22%–31%] vs 19% | -0.172 vs -0.377 | +0.072 (+0.072 capped) | +2.0 | yes | 1/1 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO LESS | k_rr_tp1=3.63–19.5 | 205 | 9% [6%–13%] vs 31% | -0.524 vs -0.110 | -0.218 (-0.218 capped) | -6.0 | yes | 1/1 |
| LEAN LESS | weekday=Wed | 124 | 15% [9%–22%] vs 26% | -0.587 vs -0.163 | -0.110 (-0.110 capped) | -2.6 | yes | 1/1 |
| LEAN LESS | k_pools_before_tp1=1 | 207 | 17% [13%–23%] vs 26% | -0.390 vs -0.176 | -0.089 (-0.089 capped) | -2.5 | yes | 1/1 |
| LEAN LESS | window=ny_premarket | 92 | 14% [8%–23%] vs 25% | -0.610 vs -0.185 | -0.108 (-0.108 capped) | -2.3 | yes | 1/1 |
| LEAN LESS | k_momentum=0.037–0.138 | 205 | 18% [13%–24%] vs 26% | -0.393 vs -0.176 | -0.079 (-0.079 capped) | -2.2 | yes | 1/1 |
| LEAN LESS | hour=7 | 68 | 13% [7%–23%] vs 25% | -0.623 vs -0.202 | -0.113 (-0.113 capped) | -2.1 | yes | 1/1 |
| LEAN LESS | k_tp1_just_past_pool=True | 229 | 19% [14%–24%] vs 26% | -0.377 vs -0.172 | -0.072 (-0.072 capped) | -2.0 | yes | 1/1 |
