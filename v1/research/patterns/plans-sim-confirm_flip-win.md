# Patterns — plans-sim.parquet · confirm_flip

Judged on: win rate (TP1 before the stop) · Traits: asset, read_kind, rtf, side, array, src, fast, risk_adr

Base: 671 trades · win 12.5% · mean -0.006 R · period 2022-03-01 → 2023-09-28 · tests run: 182

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO MORE | rtf=1d & array=1h bearish FVG | 32 | 38% [23%–55%] vs 11% | +0.596 vs -0.036 | +0.262 (+0.262 capped) | +4.4 | yes | 3/3 |
| DO MORE | read_kind=ltf_pullback & array=1h bearish FVG | 39 | 33% [21%–49%] vs 11% | +0.739 vs -0.052 | +0.221 (+0.221 capped) | +4.0 | yes | 3/3 |
| LEAN MORE | read_kind=ltf_pullback & risk_adr=1.2–2.22 | 69 | 23% [15%–34%] vs 11% | +0.649 vs -0.081 | +0.119 (+0.119 capped) | +2.8 | yes | 3/3 |
| LEAN MORE | read_kind=ltf_pullback & side=short | 165 | 19% [14%–25%] vs 10% | +0.386 vs -0.133 | +0.083 (+0.083 capped) | +2.8 | yes | 3/3 |
| LEAN MORE | read_kind=ltf_pullback & risk_adr=0.076–1.2 | 66 | 23% [14%–34%] vs 11% | -0.002 vs -0.006 | +0.113 (+0.113 capped) | +2.6 | yes | 3/3 |
| LEAN MORE | array=1h bearish FVG & src=gap | 78 | 22% [14%–32%] vs 11% | +0.332 vs -0.050 | +0.105 (+0.105 capped) | +2.6 | yes | 3/3 |
| LEAN MORE | side=short & array=1h bearish FVG | 78 | 22% [14%–32%] vs 11% | +0.332 vs -0.050 | +0.105 (+0.105 capped) | +2.6 | yes | 3/3 |
| LEAN MORE | array=1h bearish FVG | 78 | 22% [14%–32%] vs 11% | +0.332 vs -0.050 | +0.105 (+0.105 capped) | +2.6 | yes | 3/3 |
| LEAN MORE | array=1h bearish FVG & fast=False | 55 | 24% [14%–36%] vs 12% | +0.586 vs -0.058 | +0.121 (+0.121 capped) | +2.6 | yes | 3/3 |
| LEAN MORE | read_kind=ltf_pullback & fast=False | 150 | 19% [13%–26%] vs 11% | +0.477 vs -0.145 | +0.079 (+0.079 capped) | +2.6 | yes | 3/3 |
| LEAN MORE | rtf=1d & risk_adr=1.2–2.22 | 68 | 22% [14%–33%] vs 11% | +0.552 vs -0.068 | +0.106 (+0.106 capped) | +2.5 | yes | 2/3 |
| LEAN MORE | read_kind=ltf_pullback & src=gap | 201 | 17% [13%–23%] vs 10% | +0.306 vs -0.139 | +0.070 (+0.070 capped) | +2.5 | yes | 3/3 |
| LEAN MORE | asset=US30 & risk_adr=0.076–1.2 | 70 | 21% [13%–32%] vs 11% | -0.030 vs -0.003 | +0.099 (+0.099 capped) | +2.4 | yes | 1/1 |
| LEAN MORE | src=gap & risk_adr=0.076–1.2 | 213 | 17% [12%–23%] vs 10% | -0.053 vs +0.017 | +0.064 (+0.064 capped) | +2.3 | yes | 2/3 |
| LEAN MORE | fast=False & risk_adr=0.076–1.2 | 163 | 18% [13%–24%] vs 11% | -0.031 vs +0.003 | +0.070 (+0.070 capped) | +2.3 | yes | 3/3 |
| LEAN MORE | read_kind=ltf_pullback & array=1h bearish IFVG | 31 | 26% [14%–43%] vs 12% | +0.033 vs -0.007 | +0.139 (+0.139 capped) | +2.3 | yes | 3/3 |
| LEAN MORE | rtf=1d & side=short | 131 | 18% [13%–26%] vs 11% | +0.472 vs -0.121 | +0.072 (+0.072 capped) | +2.2 | yes | 2/3 |
| LEAN MORE | asset=US100 & array=1h bearish FVG | 32 | 25% [13%–42%] vs 12% | +0.065 vs -0.009 | +0.131 (+0.131 capped) | +2.2 | yes | 1/1 |
| LEAN MORE | read_kind=ltf_pullback | 212 | 17% [12%–22%] vs 11% | +0.243 vs -0.120 | +0.058 (+0.058 capped) | +2.1 | yes | 3/3 |
| LEAN MORE | asset=US500 & read_kind=ltf_pullback | 82 | 20% [12%–29%] vs 12% | +0.379 vs -0.059 | +0.080 (+0.080 capped) | +2.0 | yes | 1/1 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| LEAN LESS | rtf=4h & risk_adr=2.22–6.77 | 84 | 4% [1%–10%] vs 14% | -0.152 vs +0.015 | -0.102 (-0.102 capped) | -2.6 | yes | 3/3 |
| LEAN LESS | array=4h bearish FVG & risk_adr=2.22–6.77 | 40 | 0% [0%–9%] vs 13% | +0.210 vs -0.019 | -0.133 (-0.133 capped) | -2.5 | yes | 3/3 |
| LEAN LESS | risk_adr=2.22–6.77 | 224 | 8% [5%–13%] vs 15% | -0.042 vs +0.013 | -0.061 (-0.061 capped) | -2.2 | yes | 3/3 |
| LEAN LESS | asset=US100 & read_kind=aligned | 31 | 0% [0%–11%] vs 13% | -0.701 vs +0.028 | -0.131 (-0.131 capped) | -2.2 | yes | 1/1 |
| LEAN LESS | asset=US100 & array=4h bearish FVG | 30 | 0% [0%–11%] vs 13% | -0.327 vs +0.010 | -0.131 (-0.131 capped) | -2.1 | yes | 1/1 |
| LEAN LESS | read_kind=counter_weekly & risk_adr=1.2–2.22 | 119 | 7% [3%–13%] vs 14% | -0.141 vs +0.024 | -0.070 (-0.070 capped) | -2.1 | yes | 3/3 |
| LEAN LESS | src=gap & risk_adr=2.22–6.77 | 219 | 9% [6%–13%] vs 14% | -0.033 vs +0.008 | -0.057 (-0.057 capped) | -2.1 | yes | 3/3 |
| LEAN LESS | read_kind=ltf_pullback & risk_adr=2.22–6.77 | 77 | 5% [2%–13%] vs 13% | +0.089 vs -0.018 | -0.083 (-0.083 capped) | -2.1 | yes | 3/3 |
