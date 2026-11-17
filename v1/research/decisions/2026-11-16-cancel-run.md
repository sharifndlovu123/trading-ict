# Decision — cancel a resting limit after a 1 R run (`cancel_run_r`), 2026-11-16

**Source:** trade reviews #47–56 ("resting limits are never cancelled; fills hours after the move left").
**Change:** option `cancel_run_r` on the plan (simulator, `manage()`, four models), off by default; tests; suite 593 passed.
**Evidence:** 2022-01-03 → 2024-06-28, three indices, futures cost (`reports/cancelrun-2022-01-03-2024-06-28.parquet`; dropped trades in `reports/cancelrun-dropped-2022-24.parquet`).

| Model | Baseline | With cancel at 1 R | Dropped trades |
|---|---|---|---|
| 2022 model | 1,103 trades, 33.8% win, −0.067 R | 949, 34.6%, −0.045 R | 180, 30.6%, −0.153 R |
| MMxM | 618, 30.6%, −0.004 R | 471, 32.5%, −0.014 R | 152, 25.7%, +0.040 R |
| Silver bullet | 1,214, 31.8%, +0.011 R | 1,163, 32.0%, +0.006 R | 139, 28.1%, −0.028 R |
| Recipe, mornings | 67, 41.8%, +0.270 R | 58, 37.9%, +0.208 R | 9, 66.7%, +0.667 R |

By index, year and volatility the sign of the change is mixed for every model (no model improves on all three indices).

**Decision: stays off.** Stale fills are not worse trades than the rest, except weakly for the 2022 model (not significant, and US30 gets worse). The reviewers' complaint is about realism of a few trades, not about the average. The option stays available.
