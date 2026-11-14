# Higher timeframes + trailed runner: results (2026-11-14)

Pre-registration: `research/preregistered-timeframes-trail-2026-11-14.md`. Futures, US100 US500 US30 XAUUSD XAGUSD,
2022-01-03 → 2024-06-28, OOS = last 30%. Measure: expectancy with the runner (`runner_r`). Pass = OOS Δ vs baseline
z ≥ 2.4 with ≥ 30 OOS trades. Logs: `reports/sweep-tf-trail-2026-11-14.log` (2022 model),
`reports/sweep-tf-trail-mmxm-2026-11-14.log` (MMxM rerun after the `_tf_minutes` fix, commit 2393baa).

## Verdict: no cell passes (0 of 6)

| model | variant | OOS n | OOS exp R | Δ vs base | z | pass |
|---|---|---|---|---|---|---|
| 2022 model | baseline (1m entry) | 304 | +0.023 | – | – | – |
| 2022 model | entry 5m | 126 | −0.069 | −0.092 | −0.6 | no |
| 2022 model | entry 15m | 28 | −0.089 | −0.112 | −0.4 | no (n < 30) |
| 2022 model | runner trailed on 5m | 304 | −0.070 | −0.093 | −0.7 | no |
| MMxM | baseline (15m frame, 5m entry) | 237 | −0.077 | – | – | – |
| MMxM | frame 1h → entry 15m | 22 | +0.103 | +0.180 | +0.6 | no (n < 30) |
| MMxM | frame 4h → entry 1h | 0 | – | – | – | no (no trades: 71 candidates in 6 months of US100, all failed the trigger) |
| MMxM | runner trailed on 5m | 237 | −0.041 | +0.036 | +0.3 | no |

## Reading
- Moving the whole model up a timeframe leaves far fewer trades (2022 model: 304 → 126 → 28 OOS) and no better
  ones. The plain higher-TF version keeps every FVG on that chart; Sharif's batch-3 point (review log #14) is narrower:
  a 15m FVG **inside a 4h FVG**, at the right time. That nested rule is the next test, not this one.
- The 5m trail gives back about what it gains: −0.09 R on the 2022 model, +0.04 R on MMxM. 5m swing lows sit close
  behind price; normal pullbacks take the runner out before the 4–5 R runs seen in-sample.
- MMxM 1h → 15m: +0.18 R vs baseline on 22 OOS trades (68 in-sample, 12% in-sample win rate). Too few to count, and
  the in-sample half was poor; noted, not pursued on its own.
