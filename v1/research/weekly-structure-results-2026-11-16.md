# Results: counter-trend small grabs with the weekly structure (pre-registration: research/preregistered-weekly-structure-2026-11-16.md + amendments 1–2)

US100 US500 US30, futures, runner R, 2022-01-03 → 2024-06-28, OOS from 2023-09-29. Sweep: `research/scripts/run_weekly_sweeps.sh`
→ `reports/weekly-<model>.parquet`; scored by `research/scripts/weekly_eval.py`. 2024-07+ untouched. The weekly structure
is the rule fitted to Sharif's in-sample labels (95% of 243 weeks); neutral never occurs after the 800-day warm-up.

## Result: **FAIL on both models** (pass = OOS paired Δ > 0, z ≥ 2.4, ≥ 30 counter-structure trades)
| model | counter-structure trades IS (Δ) | OOS n | OOS runner → small grab | **OOS Δ (z)** |
|---|---|---|---|---|
| 2022 model | 477 (−0.05 R, z −0.95) | 115 | −0.23 → −0.20 R | **+0.03 R (+0.41)** |
| MMxM | 217 (−0.03 R, z −1.16) | 83 | +0.19 → +0.26 R | **+0.07 R (+1.06)** |
Trades with the structure: unchanged (0 of 513 and 0 of 318 differ), as required. Whole book OOS: 2022 model −0.04 → −0.03 R,
MMxM +0.05 → +0.09 R — both inside noise. This was the last definition of "weekly trend" tried on this OOS; no third one.

## Descriptive (baseline runner R, not a test)
| model | IS with / against | OOS with / against |
|---|---|---|
| 2022 model | −0.01 (n 374) / −0.02 (n 477) | +0.11 (n 139) / −0.23 (n 115) |
| MMxM | −0.08 (n 239) / +0.08 (n 217) | −0.09 (n 79) / +0.19 (n 83) |
In-sample the weekly structure separates nothing for either model. OOS the 2022 model leans his way (with − against
= +0.34 R, ≈ z 1.6) and MMxM the other way (−0.28 R). Opposite signs on two models with no IS support = noise, not a
filter. The weekly structure and `htf40` agree on only 55–57% of trades: they are different readings.

## What it means
- Closing counter-weekly trades at TP1 neither helps nor hurts; the targets the models already use are mostly near
  liquidity, so "small grab" changes little (the runner part is small).
- The weekly structure is kept as a **context column** (and bias rule `weekly_structure`) — it matches his reading — but
  it does not become a trade rule. Whether it matters at the *selection* level (which days/areas to trade at all) is the
  next question; the engine-read review (`research/scripts/read_build.py`, port 8772) asks Sharif to judge the engine's
  whole top-down read, not trades.
