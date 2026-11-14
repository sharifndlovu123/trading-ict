# Candle Range Theory as a pattern: results (2026-11-14)

Pre-registration: `research/preregistered-crt-2026-11-14.md`. Script `research/scripts/crt_test.py`; rows `reports/crt-trades.parquet`. US100, US500, US30, XAUUSD, XAGUSD, 2022-01-03→2024-06-28; OOS from 2023-09-29. Exp = runner R after costs (50% at C1's 50%, runner to the far end); TP1% = C1's 50% (or far end) hit before C2's wick.

## cfd

| # | cell | filter | IS n | IS exp | OOS n | OOS TP1% | OOS exp (all out) | OOS exp | z | pass |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1h | all | 15869 | -0.364 | 6775 | 60% | -0.464 | -0.470 | -9.7 | no |
| 2 | 1h | bias agrees | 8012 | -0.384 | 3342 | 61% | -0.480 | -0.490 | -7.7 | no |
| 3 | 4h CME grid | all | 3502 | -0.151 | 1406 | 57% | -0.154 | -0.146 | -3.6 | no |
| 4 | 4h CME grid | bias agrees | 1751 | -0.203 | 720 | 59% | -0.162 | -0.151 | -2.4 | no |
| 5 | 4h FX grid | all | 3494 | -0.165 | 1383 | 58% | -0.200 | -0.217 | -7.6 | no |
| 6 | 4h FX grid | bias agrees | 1735 | -0.144 | 688 | 57% | -0.184 | -0.224 | -5.4 | no |
| 7 | 1d | all | 679 | -0.021 | 277 | 60% | -0.118 | -0.155 | -3.0 | no |
| 8 | 1d | bias agrees | 220 | -0.027 | 89 | 69% | +0.089 | +0.030 | +0.3 | no |
| 9 | 1-5-9 (4h 01:00 → 05:00) | all | 714 | -0.103 | 238 | 68% | -0.087 | -0.136 | -2.6 | no |
| 10 | 1-5-9 (4h 01:00 → 05:00) | bias agrees | 356 | -0.076 | 112 | 66% | -0.144 | -0.231 | -3.2 | no |
| 11 | 1H 08 → 09 | all | 583 | -0.107 | 256 | 62% | -0.137 | -0.131 | -2.2 | no |
| 12 | 1H 08 → 09 | bias agrees | 297 | -0.138 | 139 | 65% | -0.071 | -0.083 | -1.0 | no |

Descriptive (cfd, all periods): CRT (closed back inside) vs a one-sided sweep that closed outside, same trade (fade toward C1's 50%).

| cell | inside: n / TP1% / exp | outside: n / TP1% / exp |
|---|---|---|
| 1h | 22644 / 60% / -0.396 | 28887 / 20% / -1.494 |
| 4h CME grid | 4908 / 58% / -0.150 | 7074 / 20% / -0.611 |
| 4h FX grid | 4877 / 58% / -0.180 | 6942 / 20% / -0.654 |
| 1d | 956 / 61% / -0.060 | 1351 / 20% / -0.308 |
| 1-5-9 (4h 01:00 → 05:00) | 952 / 66% / -0.111 | 1381 / 24% / -0.673 |
| 1H 08 → 09 | 839 / 65% / -0.115 | 1343 / 20% / -0.750 |

## futures

| # | cell | filter | IS n | IS exp | OOS n | OOS TP1% | OOS exp (all out) | OOS exp | z | pass |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1h | all | 15869 | -0.103 | 6775 | 60% | -0.138 | -0.143 | -5.8 | no |
| 2 | 1h | bias agrees | 8012 | -0.118 | 3342 | 61% | -0.153 | -0.163 | -4.7 | no |
| 3 | 4h CME grid | all | 3502 | -0.017 | 1406 | 57% | -0.013 | -0.004 | -0.1 | no |
| 4 | 4h CME grid | bias agrees | 1751 | -0.059 | 720 | 59% | +0.007 | +0.018 | +0.4 | no |
| 5 | 4h FX grid | all | 3494 | -0.028 | 1383 | 58% | -0.054 | -0.071 | -2.5 | no |
| 6 | 4h FX grid | bias agrees | 1735 | -0.012 | 688 | 57% | -0.029 | -0.069 | -1.6 | no |
| 7 | 1d | all | 679 | +0.012 | 277 | 60% | -0.088 | -0.126 | -2.4 | no |
| 8 | 1d | bias agrees | 220 | +0.015 | 89 | 69% | +0.120 | +0.062 | +0.6 | no |
| 9 | 1-5-9 (4h 01:00 → 05:00) | all | 714 | -0.007 | 238 | 68% | +0.009 | -0.039 | -0.8 | no |
| 10 | 1-5-9 (4h 01:00 → 05:00) | bias agrees | 356 | +0.022 | 112 | 66% | -0.038 | -0.126 | -1.8 | no |
| 11 | 1H 08 → 09 | all | 583 | -0.025 | 256 | 62% | -0.046 | -0.040 | -0.7 | no |
| 12 | 1H 08 → 09 | bias agrees | 297 | -0.049 | 139 | 65% | +0.017 | +0.005 | +0.1 | no |

Descriptive (futures, all periods): CRT (closed back inside) vs a one-sided sweep that closed outside, same trade (fade toward C1's 50%).

| cell | inside: n / TP1% / exp | outside: n / TP1% / exp |
|---|---|---|
| 1h | 22644 / 60% / -0.115 | 28887 / 20% / -0.282 |
| 4h CME grid | 4908 / 58% / -0.013 | 7074 / 20% / -0.138 |
| 4h FX grid | 4877 / 58% / -0.040 | 6942 / 20% / -0.058 |
| 1d | 956 / 61% / -0.028 | 1351 / 20% / -0.166 |
| 1-5-9 (4h 01:00 → 05:00) | 952 / 66% / -0.015 | 1381 / 24% / -0.205 |
| 1H 08 → 09 | 839 / 65% / -0.030 | 1343 / 20% / -0.408 |

## Verdict

**No cell passes on either basis.** The best are the bias-filtered daily CRT (+0.03 R CFD, +0.06 R futures, z ≤ 0.6,
n 89 OOS) and the 4h CME grid with bias (+0.02 R futures, z 0.4). Every unfiltered cell is negative OOS on CFD; on
futures they sit at about 0 before the small costs and slightly below after.

Why a 57–69% hit rate still loses: the target (C1's 50%) is close and the stop (C2's wick) is far. The median win at
TP1 is only **0.34–0.40 R** (futures), so the pattern needs a ~72% hit rate to break even and gets ~60%. The runner to
C1's far end does not fix it (OOS exp with runner ≈ all-out).

What the pattern does show (descriptive): **closing back inside matters.** After a one-sided sweep that closed
*outside* C1, the same fade reaches C1's 50% only ~20% of the time (vs ~60% when it closed back inside). That is the
turtle-soup half of the idea (a failed breakout reverses, a held one runs), and it is ICT's own (rulings §16) — it says
"don't fade a candle that closed beyond", not "CRT is an edge".

Matches ICT's ruling: as a stand-alone recipe CRT has no edge after costs; what's real in it is already in Power of 3,
turtle soup and the bias. Keep it as a tag (prior-candle high/low swept and closed back inside, per TF) on model trades
if wanted; not a model. 2024-07+ unused.
