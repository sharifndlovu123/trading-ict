# Pre-registered selection #1: "trade these models in these windows"

Written 2026-11-13, after the store held both periods, before any selection query was run.

- **Selection data:** store rows with day ≤ 2024-06-28 (2022-01-03 → 2024-06-28), current defaults
  (commit 5cc1abe), all 5 assets pooled.
- **Buckets:** model family × time window (3 models; London, premarket, NY AM, macros, NY PM; SB's 3 windows).
- **Keep a bucket if:** n ≥ 60 traded, exp R > 0, and both halves (early/late by date) > 0.
- **Test:** trade only the kept buckets on 2024-07-01 → 2026-11-12 (commit 8601da6 runs; same defaults).
  Report pooled exp R ± se and per-bucket results. Pass = pooled exp R > 0. Edge = z ≥ 2.
- **Comparison:** all buckets (no selection) on the same test period.
- One shot: whatever the result, the rule is not changed and re-run on this test period.

## Result (run 2026-11-13): FAIL

- Kept (2022–24): SB sb_pm (+0.11R, n 204), 2022 ny_am (+0.05, n 303), 2022 ny_pm (+0.04, n 224).
- On test: pooled −0.134 ± 0.044R (n 876), vs −0.102 for all buckets unselected. Every kept bucket was negative (−0.08, −0.12, −0.22).
- MMxM ny_premarket was NOT kept: +0.09R overall in 2022–24 with 5 assets, but its later half was −0.23. On test it was +0.12R.
- Reading: window-level results in 2022–24 did not predict 2024-07+ for these models as coded. Time selection alone is not the edge yet. The direction call (39% of losses bias-wrong) is the bigger lever.
