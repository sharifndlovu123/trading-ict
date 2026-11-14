# Liquidity targets + hold: results (2026-11-14)

Pre-registration: `research/preregistered-liquidity-targets-2026-11-14.md` (decision on the **futures** basis only, amendment of 2026-11-14). Runs: `research/scripts/run_targets_entry_sweeps.sh`, log `reports/sweep-targets-entry-2026-11-14.log`. US100 US500 US30 XAUUSD XAGUSD, 2022-01-03→2024-06-28, OOS = last 30%. Measure: expectancy with the runner (`runner_r`). Pass = OOS Δ vs baseline z ≥ 2.6 with ≥ 30 OOS trades.

## Verdict

**No cell passes (0 of 8).** Every variant is within ±0.09 R of its baseline OOS on futures (largest |z| 0.7). Where the runner aims (strongest pool, FVGs ahead, the HTF draw held to 16:55) does not move expectancy: the runner is half the position and reaches far targets rarely; holding to 16:55 gives back about what it gains. Review log #4, #6, #9, #12 stay open as review questions, not rules. Sharif's Jun 7 2024 NFP example (+3.3 R vs +1.98 R) is one trade; across 2022–24 the same idea averages ~0.

## Futures (decides)

### TARGETS 2022_model futures

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 953 | 34% | -0.023 | 304 | 36% [30%–41%] | +0.023 ± 0.099 | +0.000 | +0.0 |
| targets: runner to strongest pool | 963 | 34% | -0.032 | 305 | 36% [31%–41%] | -0.064 ± 0.083 | -0.088 | -0.7 |
| targets: FVGs ahead as TP1 candidates | 920 | 34% | -0.035 | 292 | 37% [31%–42%] | +0.031 ± 0.100 | +0.008 | +0.1 |
| targets: both | 927 | 34% | -0.043 | 293 | 37% [32%–43%] | -0.049 ± 0.084 | -0.072 | -0.6 |
| hold: runner to the HTF draw | 973 | 35% | -0.061 | 313 | 35% [30%–41%] | +0.003 ± 0.096 | -0.021 | -0.2 |

### TARGETS pd_return futures

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 2625 | 28% | -0.003 | 976 | 28% [25%–31%] | +0.015 ± 0.063 | +0.000 | +0.0 |
| targets: runner to strongest pool | 2625 | 28% | -0.015 | 976 | 28% [25%–31%] | -0.001 ± 0.062 | -0.017 | -0.2 |
| targets: FVGs ahead as TP1 candidates | 2605 | 30% | +0.009 | 972 | 29% [27%–32%] | +0.014 ± 0.062 | -0.002 | -0.0 |
| targets: both | 2605 | 30% | -0.003 | 972 | 29% [27%–32%] | -0.007 ± 0.061 | -0.023 | -0.3 |
| hold: runner to the HTF draw | 2625 | 28% | -0.031 | 976 | 29% [26%–32%] | +0.039 ± 0.065 | +0.024 | +0.3 |

## CFD (history only)

### TARGETS 2022_model cfd

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 339 | 35% | +0.012 | 88 | 39% [29%–49%] | +0.129 ± 0.157 | +0.000 | +0.0 |
| targets: runner to strongest pool | 344 | 35% | +0.005 | 90 | 39% [29%–49%] | +0.159 ± 0.155 | +0.030 | +0.1 |
| targets: FVGs ahead as TP1 candidates | 329 | 36% | +0.010 | 84 | 39% [30%–50%] | +0.071 ± 0.151 | -0.057 | -0.3 |
| targets: both | 333 | 36% | +0.013 | 86 | 40% [30%–50%] | +0.118 ± 0.153 | -0.010 | -0.0 |
| hold: runner to the HTF draw | 345 | 36% | -0.036 | 88 | 41% [31%–51%] | +0.122 ± 0.155 | -0.007 | -0.0 |

### TARGETS pd_return cfd

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 1019 | 26% | -0.127 | 328 | 31% [26%–36%] | +0.155 ± 0.107 | +0.000 | +0.0 |
| targets: runner to strongest pool | 1019 | 26% | -0.122 | 328 | 31% [26%–36%] | +0.146 ± 0.108 | -0.009 | -0.1 |
| targets: FVGs ahead as TP1 candidates | 1007 | 29% | -0.106 | 326 | 33% [28%–38%] | +0.169 ± 0.107 | +0.014 | +0.1 |
| targets: both | 1007 | 29% | -0.108 | 326 | 33% [28%–38%] | +0.165 ± 0.107 | +0.010 | +0.1 |
| hold: runner to the HTF draw | 1019 | 27% | -0.134 | 328 | 32% [27%–38%] | +0.157 ± 0.107 | +0.002 | +0.0 |

