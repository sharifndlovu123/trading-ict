# Entry-quality gates: results (2026-11-14)

Pre-registration: `research/preregistered-entry-quality-2026-11-14.md` (decision on the **futures** basis only, amendment of 2026-11-14). Runs: `research/scripts/run_targets_entry_sweeps.sh`, log `reports/sweep-targets-entry-2026-11-14.log`. US100 US500 US30 XAUUSD XAGUSD, 2022-01-03→2024-06-28, OOS = last 30%. Measure: expectancy all out at TP1. Pass = OOS Δ vs baseline z ≥ 2.6 with ≥ 30 OOS trades.

## Verdict

**No cell passes (0 of 15).** Best: Cameron and PD return 'no chop' +0.015 R (z 0.1–0.2). 'Sweep then displacement' hurts Silver Bullet (−0.147 R, z −1.5) and PD return (−0.070 R): requiring the sweep first makes the entry later, after part of the move. The gates remove 15–65% of trades but the removed trades are as good as the kept ones (win rates within a few points). Sharif's corrections (review log #11, #13: sweep + aggressive move; no chop) were right about those trades, but as mechanical rules they don't separate winners from losers → review batch 3 shows dropped vs kept trades to find what his eye sees that the gate misses.

## Futures (decides)

### ENTRY 2022_model futures

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 953 | 34% | -0.062 | 304 | 36% [30%–41%] | -0.044 ± 0.077 | +0.000 | +0.0 |
| entry: sweep then displacement | 588 | 35% | -0.038 | 185 | 36% [30%–43%] | -0.033 ± 0.097 | +0.010 | +0.1 |
| entry: no chop in the zone | 658 | 34% | -0.061 | 210 | 34% [28%–41%] | -0.071 ± 0.093 | -0.027 | -0.2 |
| entry: both | 371 | 37% | +0.037 | 113 | 35% [27%–45%] | -0.079 ± 0.125 | -0.036 | -0.2 |

### ENTRY mmxm futures

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 649 | 27% | -0.082 | 237 | 29% [24%–35%] | -0.015 ± 0.093 | +0.000 | +0.0 |
| entry: sweep then displacement | 566 | 27% | -0.118 | 211 | 29% [24%–36%] | -0.018 ± 0.100 | -0.003 | -0.0 |
| entry: no chop in the zone | 156 | 28% | +0.066 | 55 | 31% [20%–44%] | -0.020 ± 0.170 | -0.005 | -0.0 |
| entry: both | 112 | 27% | +0.027 | 43 | 33% [20%–47%] | -0.017 ± 0.189 | -0.002 | -0.0 |

### ENTRY silver_bullet futures

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 1328 | 29% | -0.016 | 511 | 31% [27%–35%] | +0.046 ± 0.065 | +0.000 | +0.0 |
| entry: sweep then displacement | 942 | 30% | -0.007 | 364 | 26% [22%–31%] | -0.101 ± 0.070 | -0.147 | -1.5 |
| entry: no chop in the zone | 1117 | 27% | -0.016 | 419 | 27% [23%–31%] | +0.042 ± 0.077 | -0.005 | -0.0 |
| entry: both | 723 | 27% | -0.053 | 280 | 22% [17%–27%] | -0.129 ± 0.086 | -0.175 | -1.6 |

### ENTRY cameron futures

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 1537 | 25% | -0.131 | 597 | 28% [24%–31%] | -0.018 ± 0.065 | +0.000 | +0.0 |
| entry: sweep then displacement | 1017 | 28% | -0.020 | 380 | 27% [23%–32%] | -0.054 ± 0.077 | -0.036 | -0.4 |
| entry: no chop in the zone | 1126 | 22% | -0.067 | 421 | 25% [21%–30%] | -0.003 ± 0.084 | +0.015 | +0.1 |
| entry: both | 629 | 24% | +0.009 | 224 | 26% [21%–32%] | -0.043 ± 0.110 | -0.025 | -0.2 |

### ENTRY pd_return futures

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 2625 | 28% | -0.040 | 976 | 28% [25%–31%] | +0.009 ± 0.058 | +0.000 | +0.0 |
| entry: sweep then displacement | 1364 | 30% | +0.006 | 500 | 28% [24%–32%] | -0.061 ± 0.075 | -0.070 | -0.7 |
| entry: no chop in the zone | 2206 | 28% | -0.044 | 843 | 29% [26%–32%] | +0.024 ± 0.063 | +0.015 | +0.2 |
| entry: both | 1176 | 30% | -0.000 | 450 | 28% [24%–32%] | -0.045 ± 0.081 | -0.054 | -0.5 |

## CFD (history only)

### ENTRY 2022_model cfd

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 339 | 35% | +0.012 | 88 | 39% [29%–49%] | +0.128 ± 0.144 | +0.000 | +0.0 |
| entry: sweep then displacement | 209 | 34% | -0.002 | 55 | 40% [28%–53%] | +0.111 ± 0.183 | -0.018 | -0.1 |
| entry: no chop in the zone | 225 | 36% | +0.046 | 63 | 35% [24%–47%] | -0.006 ± 0.168 | -0.135 | -0.6 |
| entry: both | 133 | 37% | +0.055 | 33 | 36% [22%–53%] | -0.060 ± 0.232 | -0.189 | -0.7 |

### ENTRY mmxm cfd

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 357 | 25% | -0.116 | 118 | 31% [23%–39%] | +0.078 ± 0.123 | +0.000 | +0.0 |
| entry: sweep then displacement | 305 | 25% | -0.157 | 99 | 32% [24%–42%] | +0.108 ± 0.138 | +0.030 | +0.2 |
| entry: no chop in the zone | 85 | 27% | +0.126 | 31 | 26% [14%–43%] | -0.141 ± 0.206 | -0.219 | -0.9 |
| entry: both | 59 | 24% | +0.056 | 23 | 30% [16%–51%] | -0.044 ± 0.258 | -0.122 | -0.4 |

### ENTRY silver_bullet cfd

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 893 | 27% | -0.070 | 333 | 30% [26%–35%] | +0.021 ± 0.079 | +0.000 | +0.0 |
| entry: sweep then displacement | 614 | 29% | -0.041 | 229 | 27% [22%–33%] | -0.082 ± 0.085 | -0.103 | -0.9 |
| entry: no chop in the zone | 720 | 25% | -0.089 | 258 | 28% [23%–34%] | +0.017 ± 0.094 | -0.004 | -0.0 |
| entry: both | 471 | 27% | -0.061 | 167 | 23% [18%–30%] | -0.143 ± 0.103 | -0.164 | -1.3 |

### ENTRY cameron cfd

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 775 | 29% | -0.020 | 243 | 33% [27%–39%] | +0.081 ± 0.103 | +0.000 | +0.0 |
| entry: sweep then displacement | 439 | 29% | -0.009 | 141 | 30% [23%–38%] | +0.054 ± 0.121 | -0.028 | -0.2 |
| entry: no chop in the zone | 492 | 25% | +0.026 | 146 | 31% [24%–39%] | +0.148 ± 0.148 | +0.067 | +0.4 |
| entry: both | 244 | 25% | +0.033 | 72 | 33% [24%–45%] | +0.223 ± 0.189 | +0.141 | +0.7 |

### ENTRY pd_return cfd

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 1019 | 26% | -0.124 | 328 | 31% [26%–36%] | +0.140 ± 0.102 | +0.000 | +0.0 |
| entry: sweep then displacement | 552 | 28% | -0.036 | 168 | 32% [25%–39%] | -0.009 ± 0.115 | -0.148 | -1.0 |
| entry: no chop in the zone | 882 | 26% | -0.118 | 291 | 32% [27%–38%] | +0.222 ± 0.112 | +0.082 | +0.5 |
| entry: both | 492 | 29% | -0.019 | 156 | 33% [26%–40%] | +0.038 ± 0.123 | -0.102 | -0.6 |

