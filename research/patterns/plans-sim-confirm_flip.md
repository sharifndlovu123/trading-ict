# Patterns — plans-sim.parquet · confirm_flip

Traits: asset, read_kind, rtf, side, array, src, fast, risk_adr

Base: 671 trades · win 12.5% · mean -0.006 R · period 2022-03-01 → 2023-09-28 · tests run: 182

In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data (≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.

## Do more

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ R (capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| LEAN MORE | src=gap & fast=False | 506 | 14% [11%–17%] vs 8% | +0.106 vs -0.348 | +0.454 (+0.380 capped) | +3.0 | yes | 3/3 |
| LEAN MORE | fast=False | 527 | 13% [11%–16%] vs 10% | +0.079 vs -0.316 | +0.396 (+0.324 capped) | +2.5 | yes | 3/3 |

## Do less

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ R (capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
| DO LESS | asset=US100 & read_kind=aligned | 31 | 0% [0%–11%] vs 13% | -0.701 vs +0.028 | -0.729 (-0.670 capped) | -3.5 | yes | 1/1 |
| LEAN LESS | array=1h bullish FVG & fast=False | 53 | 9% [4%–20%] vs 13% | -0.582 vs +0.044 | -0.626 (-0.565 capped) | -3.2 | yes | 3/3 |
| LEAN LESS | array=1h bullish FVG & src=gap | 64 | 9% [4%–19%] vs 13% | -0.517 vs +0.048 | -0.566 (-0.504 capped) | -2.9 | yes | 3/3 |
| LEAN LESS | side=long & array=1h bullish FVG | 64 | 9% [4%–19%] vs 13% | -0.517 vs +0.048 | -0.566 (-0.504 capped) | -2.9 | yes | 3/3 |
| LEAN LESS | array=1h bullish FVG | 64 | 9% [4%–19%] vs 13% | -0.517 vs +0.048 | -0.566 (-0.504 capped) | -2.9 | yes | 3/3 |
| LEAN LESS | fast=True & risk_adr=2.22–6.77 | 45 | 7% [2%–18%] vs 13% | -0.500 vs +0.030 | -0.530 (-0.470 capped) | -2.6 | yes | 2/2 |
| LEAN LESS | fast=True | 144 | 10% [6%–16%] vs 13% | -0.316 vs +0.079 | -0.396 (-0.324 capped) | -2.5 | yes | 3/3 |
| LEAN LESS | rtf=4h & array=1h bullish FVG | 44 | 7% [2%–18%] vs 13% | -0.515 vs +0.030 | -0.545 (-0.485 capped) | -2.4 | yes | 3/3 |
| LEAN LESS | src=gap & fast=True | 140 | 10% [6%–16%] vs 13% | -0.297 vs +0.071 | -0.368 (-0.297 capped) | -2.3 | yes | 3/3 |
| LEAN LESS | rtf=1d & fast=True | 65 | 12% [6%–22%] vs 13% | -0.381 vs +0.035 | -0.416 (-0.354 capped) | -2.1 | yes | 3/3 |

## Strong but not stable (one half, one asset or one outlier carries it)

| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ R (capped 10 R) | z | both halves | assets |
|---|---|---|---|---|---|---|---|---|
|  | read_kind=ltf_pullback & fast=False | 150 | 19% [13%–26%] vs 11% | +0.477 vs -0.145 | +0.622 (+0.554 capped) | +2.4 | no | 3/3 |
|  | rtf=1d & fast=False | 179 | 16% [12%–22%] vs 11% | +0.354 vs -0.136 | +0.490 (+0.442 capped) | +2.2 | no | 2/3 |
|  | read_kind=ltf_pullback & side=short | 165 | 19% [14%–25%] vs 10% | +0.386 vs -0.133 | +0.519 (+0.462 capped) | +2.1 | no | 3/3 |
|  | rtf=1d & side=short | 131 | 18% [13%–26%] vs 11% | +0.472 vs -0.121 | +0.593 (+0.508 capped) | +2.1 | no | 3/3 |
|  | read_kind=ltf_pullback & src=gap | 201 | 17% [13%–23%] vs 10% | +0.306 vs -0.139 | +0.444 (+0.409 capped) | +2.1 | no | 3/3 |
