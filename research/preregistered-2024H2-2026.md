# Pre-registered checks: unseen data 2024-07-01 → 2026-11-12

Written 2026-11-13, before any model was run on this period. Every rule below was chosen
on 2022-01 → 2024-06 data. Assets: US100, US500, US30, XAUUSD, plus XAGUSD (never used to tune anything).

| # | claim (from 2022–24 sweeps) | passes if, on the unseen period |
|---|---|---|
| 1 | 2022 model: the cost gate (≤ 0.1R) helps | baseline exp R > "no cost gate" |
| 2 | 2022 model: TP1 cap 2R ≥ uncapped | baseline exp R ≥ "tp1 uncapped" |
| 3 | bias prev_day_dol ≥ prev_day (old default), all 3 models | ≥ in at least 2 of 3 models, and pooled ≥ |
| 4 | MMxM: 5m entry > 1m entry | baseline exp R > "entry 1m (old default)" |
| 5 | SB: the POI gate helps | baseline exp R > "no poi" |
| 6 | exit on a HTF close through the FVG hurts | the exit variant < baseline in at least 2 of 3 models |
| 7 | no model has shown an edge yet | report each baseline's exp R ± se; positive only counts if z ≥ 2 |

A claim that fails here is reverted or re-examined. It is not re-tuned on this period.

## Results (run 2026-11-13)

| # | result |
|---|---|
| 1 | pass (weak): 2022 baseline −0.123 vs no cost gate −0.184 (z 1.2) |
| 2 | pass: −0.123 vs uncapped −0.139 |
| 3 | **fail**: prev_day_dol − prev_day = −0.006 (2022), −0.006 (MMxM), +0.045 (SB). Only 1 of 3 models; the two losses are ties |
| 4 | pass: MMxM 5m −0.030 vs 1m −0.111 (z 1.4); third hold-out in a row |
| 5 | tie: SB −0.130 vs no poi −0.132 |
| 6 | **fail**: the FVG-close exit was slightly better in R in all 3 models (+0.008 / +0.029 / +0.015), with a lower win rate |
| 7 | 2022 model −0.123 ± 0.040 (z −3.1); SB −0.130 ± 0.034 (z −3.8); MMxM −0.030 ± 0.042 (z −0.7). Two models lose reliably on unseen data |
