# Patterns — plans-sim.parquet · touch

Traits: asset, read_kind, rtf, side, array, src, fast, risk_adr

Base: 732 trades · win 6.7% · mean -0.145 R · period 2022-03-01 → 2023-09-28 · tests run: 193

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ R (capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO MORE | read_kind=counter_weekly & side=short | 72 | 7% [3%–15%] vs 7% | +0.346 vs -0.198 | +0.544 (+0.544 capped) | +5.8 | yes | 3/3 |
| DO MORE | src=gap & fast=False | 552 | 8% [6%–11%] vs 3% | -0.052 vs -0.429 | +0.377 (+0.377 capped) | +5.4 | yes | 3/3 |
| DO MORE | fast=False | 573 | 8% [6%–10%] vs 3% | -0.065 vs -0.432 | +0.367 (+0.367 capped) | +5.1 | yes | 3/3 |
| DO MORE | rtf=4h & fast=False | 370 | 9% [7%–13%] vs 4% | -0.020 vs -0.273 | +0.253 (+0.253 capped) | +3.8 | yes | 3/3 |
| DO MORE | rtf=4h & risk_adr=2.21–6.77 | 87 | 0% [0%–4%] vs 8% | +0.027 vs -0.168 | +0.195 (+0.195 capped) | +3.5 | yes | 3/3 |
| DO MORE | side=short & fast=False | 231 | 9% [6%–13%] vs 6% | +0.022 vs -0.222 | +0.244 (+0.244 capped) | +3.1 | yes | 3/3 |
| DO MORE | asset=US30 & risk_adr=2.21–6.77 | 65 | 0% [0%–6%] vs 7% | +0.028 vs -0.162 | +0.190 (+0.190 capped) | +2.8 | yes | 1/1 |
| DO MORE | fast=False & risk_adr=2.21–6.77 | 194 | 0% [0%–2%] vs 9% | -0.031 vs -0.186 | +0.155 (+0.155 capped) | +2.8 | yes | 3/3 |
| DO MORE | array=4h bearish IFVG & fast=False | 42 | 19% [10%–33%] vs 6% | +0.280 vs -0.171 | +0.451 (+0.451 capped) | +2.7 | yes | 3/3 |
| DO MORE | rtf=4h & src=gap | 440 | 9% [7%–12%] vs 3% | -0.076 vs -0.248 | +0.172 (+0.172 capped) | +2.6 | yes | 3/3 |
| DO MORE | rtf=4h | 453 | 9% [6%–12%] vs 4% | -0.083 vs -0.246 | +0.163 (+0.163 capped) | +2.5 | yes | 3/3 |
| LEAN MORE | read_kind=counter_weekly & rtf=4h | 292 | 9% [6%–13%] vs 5% | -0.045 vs -0.211 | +0.166 (+0.166 capped) | +2.4 | yes | 3/3 |
| LEAN MORE | side=short & array=4h bearish IFVG | 45 | 18% [9%–31%] vs 6% | +0.194 vs -0.167 | +0.362 (+0.362 capped) | +2.2 | yes | 3/3 |
| LEAN MORE | array=4h bearish IFVG & src=gap | 45 | 18% [9%–31%] vs 6% | +0.194 vs -0.167 | +0.362 (+0.362 capped) | +2.2 | yes | 3/3 |
| LEAN MORE | array=4h bearish IFVG | 45 | 18% [9%–31%] vs 6% | +0.194 vs -0.167 | +0.362 (+0.362 capped) | +2.2 | yes | 3/3 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ R (capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO LESS | fast=True | 159 | 3% [1%–7%] vs 8% | -0.432 vs -0.065 | -0.367 (-0.367 capped) | -5.1 | yes | 3/3 |
| DO LESS | side=short & fast=True | 79 | 3% [1%–9%] vs 7% | -0.560 vs -0.095 | -0.465 (-0.465 capped) | -5.0 | yes | 3/3 |
| DO LESS | read_kind=ltf_pullback & fast=True | 69 | 1% [0%–8%] vs 7% | -0.573 vs -0.100 | -0.473 (-0.473 capped) | -4.9 | yes | 3/3 |
| DO LESS | rtf=1d & array=1h bullish FVG | 34 | 0% [0%–10%] vs 7% | -0.546 vs -0.125 | -0.421 (-0.421 capped) | -4.8 | yes | 3/3 |
| DO LESS | rtf=1d & risk_adr=0.065–1.19 | 46 | 0% [0%–8%] vs 7% | -0.708 vs -0.107 | -0.601 (-0.601 capped) | -4.7 | yes | 2/3 |
| DO LESS | src=gap & fast=True | 155 | 3% [1%–7%] vs 8% | -0.418 vs -0.072 | -0.346 (-0.346 capped) | -4.7 | yes | 3/3 |
| DO LESS | rtf=1d & fast=True | 76 | 1% [0%–7%] vs 7% | -0.508 vs -0.103 | -0.405 (-0.405 capped) | -4.4 | yes | 3/3 |
| DO LESS | fast=True & risk_adr=1.19–2.21 | 43 | 2% [0%–12%] vs 7% | -0.547 vs -0.120 | -0.427 (-0.427 capped) | -4.2 | yes | 3/3 |
| DO LESS | asset=US500 & fast=True | 51 | 0% [0%–7%] vs 7% | -0.441 vs -0.123 | -0.318 (-0.318 capped) | -3.6 | yes | 1/1 |
| DO LESS | rtf=1d & side=long | 136 | 0% [0%–3%] vs 8% | -0.315 vs -0.106 | -0.209 (-0.209 capped) | -3.4 | yes | 3/3 |
| DO LESS | asset=US100 & read_kind=ltf_pullback | 82 | 4% [1%–10%] vs 7% | -0.403 vs -0.112 | -0.291 (-0.291 capped) | -3.1 | yes | 1/1 |
| DO LESS | asset=US100 & fast=True | 76 | 3% [1%–9%] vs 7% | -0.428 vs -0.112 | -0.316 (-0.316 capped) | -3.0 | yes | 1/1 |
| DO LESS | read_kind=ltf_pullback & array=4h bearish FVG | 71 | 1% [0%–8%] vs 7% | -0.392 vs -0.118 | -0.274 (-0.274 capped) | -2.9 | yes | 3/3 |
| DO LESS | fast=True & risk_adr=2.21–6.77 | 50 | 0% [0%–7%] vs 7% | -0.328 vs -0.132 | -0.196 (-0.196 capped) | -2.7 | yes | 2/2 |
| DO LESS | rtf=4h & fast=True | 83 | 5% [2%–12%] vs 7% | -0.363 vs -0.117 | -0.246 (-0.246 capped) | -2.6 | yes | 3/3 |
| DO LESS | fast=True & risk_adr=0.065–1.19 | 66 | 6% [2%–15%] vs 7% | -0.437 vs -0.116 | -0.321 (-0.321 capped) | -2.5 | yes | 3/3 |
| DO LESS | rtf=1d | 279 | 4% [2%–6%] vs 9% | -0.246 vs -0.083 | -0.163 (-0.163 capped) | -2.5 | yes | 3/3 |
| LEAN LESS | rtf=4h & array=4h bearish FVG | 55 | 0% [0%–7%] vs 7% | -0.339 vs -0.129 | -0.210 (-0.210 capped) | -2.1 | yes | 2/3 |
| LEAN LESS | read_kind=ltf_pullback & array=1h bearish FVG | 44 | 7% [2%–18%] vs 7% | -0.425 vs -0.127 | -0.298 (-0.298 capped) | -2.1 | yes | 3/3 |

## Strong but not stable (one half, one asset or one outlier carries it)

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ R (capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
|  | read_kind=counter_weekly & fast=False | 347 | 7% [5%–10%] vs 6% | -0.031 vs -0.248 | +0.217 (+0.217 capped) | +3.2 | no | 3/3 |
|  | read_kind=ltf_pullback & rtf=1d | 145 | 6% [3%–11%] vs 7% | -0.320 vs -0.102 | -0.219 (-0.219 capped) | -2.6 | no | 3/3 |
|  | read_kind=ltf_pullback | 228 | 7% [5%–12%] vs 6% | -0.280 vs -0.084 | -0.196 (-0.196 capped) | -2.5 | no | 2/3 |
|  | read_kind=counter_weekly & risk_adr=2.21–6.77 | 145 | 0% [0%–3%] vs 8% | -0.040 vs -0.171 | +0.131 (+0.131 capped) | +2.4 | no | 3/3 |
|  | read_kind=ltf_pullback & side=short | 179 | 8% [5%–13%] vs 6% | -0.299 vs -0.095 | -0.204 (-0.204 capped) | -2.2 | no | 2/3 |
|  | read_kind=counter_weekly & src=gap | 414 | 7% [5%–10%] vs 7% | -0.081 vs -0.229 | +0.148 (+0.148 capped) | +2.1 | no | 3/3 |
|  | read_kind=counter_weekly | 426 | 7% [5%–9%] vs 7% | -0.083 vs -0.231 | +0.148 (+0.148 capped) | +2.1 | no | 3/3 |
|  | asset=US30 & fast=True | 32 | 9% [3%–24%] vs 7% | -0.428 vs -0.132 | -0.296 (-0.296 capped) | -2.0 | no | 1/1 |
