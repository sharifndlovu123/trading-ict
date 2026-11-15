# Pre-registration — 2022 model: cost/risk gate 0.05 and no premarket, on 2020–2021 (never tested)

Written 2026-11-16, before any run on the period. Status: **draft — waits for Sharif's go-ahead** (a clean period is spent once).

## Why
US100 sweep 2026-11-16 (review log #38, `research/sweeps/2026-11-16-us100-full-sweep.md`), in-sample 2022-01-03 → 2024-06-28:
- Trades with a micro stop (≤ 0.03 ADR from the entry) lose in three models (2022 model 24% win, −0.38 R, n 197).
- The 2022 model with risk ≥ 0.05 ADR: 41.4% win, +0.198 R, z 2.0 (n 203) vs 33.5%, −0.076 R for all trades.
- The 2022 model's NY premarket window: 22% win, −0.40 R (n 108); Fable's ledger shows the same pooled.

## The hold-out
- **Period:** 2020-01-02 → 2021-12-31. No backtest, sweep, read or review has used any date before 2022 (trade store: every run is 2022-01-03 → 2024-06-28 or 2024-07-01+). Bars from 2019-10 serve as warm-up only.
- **Assets:** US100, US500, US30 (Dukascopy CFD 1m; futures cost basis). March 2020 has real trading halts (gaps); they stay in.
- **Model:** `2022_model`, current defaults, vote measure `r` (all out at TP1) and `runner_r` reported beside it.

## Variants (fixed; names as in `ict_engine/eval/variants.py`)
| | Variant | Change vs baseline |
|---|---|---|
| A | `cost <= 0.05R` | `max_cost_r` 0.1 → 0.05 (rejects trades whose round-trip cost exceeds 5% of the risk: the micro-stop trades) |
| B | `no premarket` | `windows` without `ny_premarket` |
| C | `cost <= 0.05R, no premarket` | both |

Only variants that beat the baseline **on each of the three assets in-sample (2022-01-03 → 2024-06-28)** are run on the hold-out; the in-sample table is appended below before the hold-out run.

## Pass bar (per variant, pooled over the three assets on 2020–2021)
1. ≥ 30 trades.
2. Mean R of the variant's trades > 0 **and** above the baseline's mean R, with z ≥ 2.4 for the difference (variant's trades vs the baseline trades it removes, Welch).
3. The sign of the difference holds in at least 2 of 3 assets.
Reported beside it, not part of the bar: win rate with its Wilson range, runner R, R capped at 10 R, the result per year (2020, 2021).

## What each outcome means
- **Pass:** the variant becomes the 2022 model's default through the change gate (decision record + suite), and is then the baseline for further work. 2024-07+ is not needed for this rule.
- **Fail:** logged as failed in `research/review-log.md`; no re-tuning on 2020–2021. The period stays usable only for rules that were not shaped by this result.

## In-sample check (2022-01-03 → 2024-06-28, three assets)
_(appended when the run finishes)_

## Hold-out result (2020–2021)
_(appended after the single run)_
