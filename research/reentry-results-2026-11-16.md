# Results: re-entry after a stop-out, same side, same window (2026-11-16)

Pre-registration: `preregistered-reentry-2026-11-16.md`. Sweep: `research/scripts/run_reentry_sweeps.sh` →
`reports/reentry-<model>.parquet`; added trades scored by `research/scripts/reentry_eval.py`. Futures basis, runner R,
US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, OOS from 2023-09-29.

**0 of 2 pass.** The model's next setup after a stop-out is not a better trade.

| model | variant | added IS | added OOS | OOS z |
|---|---|---|---|---|
| 2022 model | re-entry: after a stop, same side | 93 · +0.10 R | **33 · −0.44 R** | **−2.56** |
| 2022 model | control: any second trade | 135 · +0.15 R | 47 · −0.21 R | −1.18 |
| MMxM | re-entry: after a stop, same side | 26 · −0.30 R | 4 · +0.26 R | +0.33 (n < 30) |
| MMxM | control: any second trade | 27 · −0.33 R | 4 · +0.26 R | +0.33 |

Whole book OOS Δ vs baseline: 2022 model −0.045 R (z −0.3); MMxM +0.006 R (z 0.0).

- 2022 model: the in-sample gain reverses OOS and is significantly negative there (US100 22 of the 33, −0.59 R each).
  The stop-out condition is worse than any second trade, so it is not "the same side again after a sweep" that pays.
- MMxM: a second setup in the same window is rare (30 in 2½ years × 5 assets); in-sample it loses −0.30 R.
- Sharif's second entries (trade-handling review) were later and elsewhere: a new FVG forming after the stop (US100
  2023-01-05 07:45 FVG), not the model's next signal right after it. That is what the rule did not capture.

Next: a review of 24 in-sample re-entries (12 per model, 6 won / 6 lost each) — Sharif marks valid / elsewhere / no
re-entry / wrong side / neither, and places his own entry, stop and TPs (`reentry_build.py`, port 8769). A new rule
comes only from that, pre-registered again.
