# Forward test: frozen rules, from 2026-11-13 onwards

Written 2026-11-14, before any data after 2026-11-12 was looked at.
Why: the 2024-07→2026-11-12 hold-out is burned (seen several times). The only clean out-of-sample data left is
data that doesn't exist yet (López de Prado ch.11–12; `references/orderflow.md` §11).

## Frozen
- **Code:** the engine at the commit tagged `forward-v1` = 17b1e5c (the protocol commit c730043 plus `ict_engine/data`, which `.gitignore` had silently excluded; those files are unchanged since 2026-11-13). Bug fixes are
  allowed only if they don't change any decision on 2022–24 (check: re-run 2022–24, same trades). Anything else
  is a new version (`forward-v2`) whose forward clock starts again from the day it is frozen.
- **Models and settings:** registry defaults at `forward-v1`, cost basis **cfd** (the data we have) and
  **futures** (re-costed, same data). Models: `2022_model`, `mmxm`, `silver_bullet`, `cameron`, `pd_return`.
- **Assets:** US100, US500, US30, XAUUSD, XAGUSD.
- **Candidates under test** (chosen on 2022–24 only; nothing else counts as a hit):
  1. each model's pooled baseline (all assets, all windows);
  2. the selection-#2 survivors: SB US30 sb_pm, 2022 model US100 ny_am, Cameron US30 ny_am;
  3. `pd_return` at defaults (added 2026-11-14; its 2022–24 result is recorded below before the forward window is
     opened).

## Logging
Weekly (or whenever data is fetched):
```
uv run python -m ict_engine.data.dukascopy fetch all <last+1> <today>
uv run python -m ict_engine.eval.backtest <asset> <last+1> <today> --model <m> [--cost futures]
uv run python -m ict_engine.eval.store add reports/backtest-*.parquet --commit <forward-v1 sha>
```
The run id includes the period, so log **non-overlapping chunks** (each starts the day after the last one
ended). Overlapping chunks would count the same trades twice. Query with `--start 2026-11-13 --commit <sha>`.

## Decision rule (fixed now)
- **First look:** when every candidate has n ≥ 100 trades **or** on 2027-05-14 (6 months), whichever comes first.
  Before then, only counts are checked (that the pipeline runs), never R.
- **Both instruments are judged** (Sharif, 2026-11-14: he may trade futures and CFDs). Every candidate is scored
  separately on each cost basis. A pass on a basis means "tradeable on that instrument". The futures and CFD runs
  can pick different trades (the cost gate), so they count as separate tests.
- **Pass:** net mean R > 0 with clustered z (`z_cl`) ≥ **3.0** on that basis. This is a Bonferroni-style
  allowance for **8 candidates × 2 bases = 16 tests** (one-sided, 5% family-wise ≈ z 2.96). A candidate that
  passes on both bases is the strongest result. **Primary candidate:** none (on 2022–24 all |z_cl| < 2), so no
  lower bar applies.
- **Fail:** anything else. A failing candidate is not re-tuned on forward data.
- Report gross and net (cost basis cfd and futures) for every candidate, including the losers.

## 2022–24 record of the candidates (for reference; filled before the forward window opens)
CFD = commit 0f2bfad (measured spreads); futures = commit 5996937 (`--cost futures`). Net R per trade.

| Candidate | CFD exp R (n, z_cl) | Futures exp R (n, z_cl) |
|---|---|---|
| 2022 model, pooled | +0.036 (427, 0.5) | −0.058 (1257, −1.4) |
| Cameron, pooled | +0.004 (1018, 0.1) | −0.099 (2134, −2.9) |
| Silver Bullet, pooled | −0.045 (1226, −0.9) | +0.001 (1839, 0.0) |
| MMxM, pooled | −0.068 (475, −1.1) | −0.064 (886, −1.2) |
| SB US30 sb_pm | +0.360 (72, 1.6) | +0.398 (65, 1.6) |
| 2022 model US100 ny_am | +0.282 (92, 1.9) | +0.012 (166, 0.1) |
| Cameron US30 ny_am | +0.160 (185, 1.3) | −0.098 (171, −0.8) |
| pd_return, pooled (commit d8dd5ff) | −0.060 (1347, −1.2) | −0.027 (3601, −0.8) |

The selection-#2 survivors are cell-level winners picked from many cells, so their in-sample z overstates them
(they already failed on the burned hold-out: −0.115R). Two of three don't survive the switch to futures costs
even in-sample. They are kept as candidates only because the selection was pre-registered.

## Amendment (2026-11-14): futures only
Sharif: "skip cfds, focus on futures" (supersedes "both"). Written before the forward window is scored. Only the
**futures** cost basis decides; CFD results are still logged and reported as history but cannot pass. The bar stays
**z_cl ≥ 3.0** (it was set for 16 tests; 8 now need only ≈ 2.7 — kept stricter on purpose, not lowered after the fact).
