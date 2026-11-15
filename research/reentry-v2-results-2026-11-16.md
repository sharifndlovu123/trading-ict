# Results: re-entry v2 + counter-trend small grabs (pre-registration: research/preregistered-reentry-v2-2026-11-16.md)

US100 US500 US30, futures, runner R, 2022-01-03 → 2024-06-28, OOS from 2023-09-29. Sweep: `research/scripts/run_reentry2_sweeps.sh`
→ `reports/reentry2-<model>.parquet`; scored by `research/scripts/reentry2_eval.py`. 2024-07+ untouched.

## H1 — re-entry v2 (no chase + counter-trend re-entry takes TP1 only): **FAIL**
| added re-entries (pooled, both models) | IS n | IS mean | OOS n | OOS mean (z) |
|---|---|---|---|---|
| plain re-entry after a stop | 99 | +0.13 | 31 | −0.50 (−2.79) |
| **v2: no chase + small grab** | 86 | −0.01 | 22 | **−0.56 (−2.44)** |
| no chase only | 86 | +0.11 | 22 | −0.64 (−3.18) |
| small grab only | 99 | +0.04 | 31 | −0.45 (−2.29) |
v2 is worse than the plain re-entry OOS (and ≤ 0 in-sample), so not even a candidate. The 2022 model carries it
(OOS n 18, −0.78 R); MMxM had 4 OOS re-entries. Refusing the chase removes trades that were no worse than the rest.

## H2 — every trade against the weekly (htf40) takes the small grab: **FAIL (both models)**
Paired per trade; the with-weekly trades were identical in both runs (0 changed, 0 unmatched).
| model | counter-trend OOS n | Δ OOS (grab − runner) | z | IS Δ |
|---|---|---|---|---|
| 2022 model | 98 | −0.17 R | −1.37 | −0.11 (n 372) |
| MMxM | 69 | +0.07 R | +0.89 | −0.05 (n 197) |
Whole book OOS: 2022 model −0.04 → −0.11 R; MMxM +0.05 → +0.08 R (z 0.2).

## Side finding (descriptive, not a test): the engine's trades *against* `htf40` were not worse
| baseline | with weekly | against weekly |
|---|---|---|
| 2022 model IS | −0.02 (n 475) | −0.00 (n 372) |
| 2022 model OOS | −0.17 (n 156) | **+0.17** (n 98) |
| MMxM IS | +0.05 (n 259) | −0.08 (n 197) |
| MMxM OOS | −0.12 (n 93) | **+0.28** (n 69) |
Either `htf40` (close vs the 40-day 50%) is not what Sharif reads as the weekly trend, or on these intraday models the
runner still pays on counter-trend days. "Price above the 8-week midpoint" also says premium/discount: a short in an
upper-half range is selling premium, which the framework favours — the two readings point opposite ways.

## What it means
- His review split (+1.29 R taken vs −0.75 R skipped) came from reading the chart with the outcome visible; the two parts
  of it we could turn into rules (no chase; weekly sets the target) don't carry it on unseen trades.
- Re-entry stays off. Counter-trend small grabs stay off. Nothing becomes a default.
- Open: his "weekly trend" needs his own definition (structure: lower highs/lows on 1W? the weekly PD array price is
  reacting from?) before another trend test; the "too late" call likely needs the 4H FVG wait (test C), not a price rule.
