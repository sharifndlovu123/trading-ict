# Results: counter-bias second trade after the day's draw (2026-11-15)

Pre-registration: `preregistered-counter-bias-2026-11-15.md` (before code). Build `0fd4d48`. Scorer:
`research/scripts/counter_bias_eval.py` → `reports/counter-bias-results.md`, `reports/counter-bias-trades.parquet`.
Futures basis, runner R; US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28; OOS from 2023-09-29. Pass = OOS mean
ΔR per changed asset-day > 0 with z ≥ 2.4 over ≥ 30 changed days.

**0 of 4 cells pass.**

| model | variant | OOS changed days | OOS ΔR/day | z | admitted (OOS) n / win / exp R | IS ΔR/day (z) |
|---|---|---|---|---|---|---|
| 2022 model | after a bias trade's TP1 | 17 (< 30, not countable) | −0.22 | −0.6 | 21 / 38% / −0.10 | +0.21 (+0.7) |
| 2022 model | after the daily draw | 60 | +0.12 | +0.5 | 73 / 45% / +0.24 | −0.03 (−0.2) |
| MMxM | after a bias trade's TP1 | 5 (< 30, not countable) | −0.20 | −0.5 | 5 / 20% / −0.20 | +0.19 (+0.7) |
| MMxM | after the daily draw | 122 | +0.05 | +0.3 | 139 / 26% / +0.04 | +0.04 (+0.5) |

## Reading
- Counter-bias trades admitted after the day's draw are roughly break-even (2022 model +0.24 R OOS but −0.04 R IS;
  MMxM ≈ +0.03–0.04 R both halves). Letting them in neither helps nor hurts reliably.
- "After a bias trade's TP1" is rare (17 / 5 OOS days) and flips sign between halves.
- Sharif's Sep 25 2023 11:00 long — the case that inspired this — is not reachable by this rule: the engine's version
  (11:05) also fails the POI gate because the turn **added** liquidity instead of sweeping it (review log #22, #27). The
  missing piece is a no-sweep trigger, not a bias exception.
