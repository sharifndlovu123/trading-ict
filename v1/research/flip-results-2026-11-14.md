# Results: the flip after a failed trade (pre-registered 2026-11-14, + amendment 1)

Run once, exactly as `research/preregistered-ifvg-flip-2026-11-14.md` (code 70a3319, `ict_engine.eval.flip`):
5 models, 2022-01-03→2024-06-28 (OOS ≥ 2023-09-29), US100 US500 US30 XAUUSD XAGUSD, both cost bases, both stop
rules. Pass (per cell) = flip OOS exp R > 0 with z ≥ 2.6 **and** model + flips beats the model alone in R per day.
Trades: `reports/flip-cfd.parquet`, `reports/flip-futures.parquet`.

## Result: no cell passes
- **One cell is over the bar on paper and is not counted:** 2022 model, far-edge stop, CFD: z +35.4 from **2**
  flips (both ≈ +1R). A standard error from two trades is not a test. The pre-registration set no minimum sample;
  that was an omission, flagged here rather than read as a pass. Future pre-registrations state a minimum (n ≥ 30
  OOS, as the trade-store board uses).
- Every other cell is below z 2.6. Closest: Cameron far-edge futures +0.871 R (z 2.3, n 26; CFD +0.644, z 1.8, n 7);
  PD return failed-extreme futures +0.240 R (z 1.9, n 327; but CFD +0.036, z 0.2, n 71).

| model | stop rule | CFD n / exp R / z | futures n / exp R / z |
|---|---|---|---|
| 2022_model | failed extreme | 24 / −0.013 / −0.0 | 94 / −0.006 / −0.0 |
| 2022_model | far edge | 2 / +0.986 / (+35.4, n=2) | 20 / −0.245 / −0.8 |
| mmxm | failed extreme | 13 / +0.642 / +1.5 | 53 / −0.064 / −0.3 |
| mmxm | far edge | 2 / +0.260 / +0.2 | 23 / −0.107 / −0.4 |
| silver_bullet | failed extreme | 58 / −0.009 / −0.1 | 136 / +0.150 / +1.1 |
| silver_bullet | far edge | 11 / −0.354 / −0.9 | 29 / −0.100 / −0.3 |
| cameron | failed extreme | 54 / +0.153 / +0.9 | 161 / +0.038 / +0.3 |
| cameron | far edge | 7 / +0.644 / +1.8 | 26 / +0.871 / +2.3 |
| pd_return | failed extreme | 71 / +0.036 / +0.2 | 327 / +0.240 / +1.9 |
| pd_return | far edge | 9 / −0.145 / −0.4 | 48 / −0.170 / −0.9 |

## What it means
1. **The failure is common, the flip is a coin-toss on average.** About 40–60% of stopped trades produce a flip
   with Sharif's stop (beyond the failed move); across models and bases the flips average ≈ 0 R. Taking every
   flip mechanically neither adds nor costs much.
2. **Sharif's stop makes the flip tradeable; the IFVG-edge stop doesn't.** The far-edge stop leaves 5–7× fewer
   flips (the cost gate), and those few are noisy both ways.
3. **Signs worth a forward look, not a rule:** PD return flips on futures (+0.24 R over 327 trades) and Cameron's
   few far-edge flips are positive on both bases. Neither is consistent enough across bases to adopt. Nothing is
   adopted; no default changes.
4. Sharif's flip in his examples was **selective** (an IFVG that was respected, inside an HTF array, with liquidity
   to run). The mechanical version takes every failure. Batch 2 of the review page shows flips with a
   "would you take it?" question, so his selection can be compared with the mechanical one before any new test.

## Raw output
# Flip after a failed trade (cfd costs), out-of-sample ≥ 2023-09-29

| model | flip stop | OOS trades | stopped | flips armed | filled | flip win | flip exp R ± se | z | R/day model | R/day + flips |
|---|---|---|---|---|---|---|---|---|---|---|
| 2022_model | failed_extreme | 88 | 46 | 25 | 24 | 25% | -0.013 ± 0.265 | -0.0 | +0.1639 | +0.1595 |
| 2022_model | far_edge | 88 | 46 | 2 | 2 | 100% | +0.986 ± 0.028 | +35.4 | +0.1639 | +0.1924 |
| mmxm | failed_extreme | 118 | 53 | 23 | 13 | 46% | +0.642 ± 0.428 | +1.5 | +0.1180 | +0.2249 |
| mmxm | far_edge | 118 | 53 | 4 | 2 | 50% | +0.260 ± 1.319 | +0.2 | +0.1180 | +0.1246 |
| silver_bullet | failed_extreme | 333 | 176 | 67 | 58 | 33% | -0.009 ± 0.168 | -0.1 | +0.0431 | +0.0399 |
| silver_bullet | far_edge | 333 | 176 | 11 | 11 | 27% | -0.354 ± 0.392 | -0.9 | +0.0431 | +0.0190 |
| cameron | failed_extreme | 243 | 141 | 64 | 54 | 44% | +0.153 ± 0.169 | +0.9 | +0.1462 | +0.2075 |
| cameron | far_edge | 243 | 141 | 8 | 7 | 71% | +0.644 ± 0.362 | +1.8 | +0.1462 | +0.1795 |
| pd_return | failed_extreme | 328 | 193 | 81 | 71 | 31% | +0.036 ± 0.175 | +0.2 | +0.2897 | +0.3061 |
| pd_return | far_edge | 328 | 193 | 9 | 9 | 44% | -0.145 ± 0.365 | -0.4 | +0.2897 | +0.2814 |
# Flip after a failed trade (futures costs), out-of-sample ≥ 2023-09-29

| model | flip stop | OOS trades | stopped | flips armed | filled | flip win | flip exp R ± se | z | R/day model | R/day + flips |
|---|---|---|---|---|---|---|---|---|---|---|
| 2022_model | failed_extreme | 304 | 189 | 114 | 94 | 37% | -0.006 ± 0.130 | -0.0 | -0.0880 | -0.0919 |
| 2022_model | far_edge | 304 | 189 | 23 | 20 | 30% | -0.245 ± 0.307 | -0.8 | -0.0880 | -0.1205 |
| mmxm | failed_extreme | 237 | 130 | 80 | 53 | 28% | -0.064 ± 0.200 | -0.3 | -0.0285 | -0.0557 |
| mmxm | far_edge | 237 | 130 | 35 | 23 | 35% | -0.107 ± 0.285 | -0.4 | -0.0285 | -0.0482 |
| silver_bullet | failed_extreme | 511 | 281 | 152 | 136 | 37% | +0.150 ± 0.139 | +1.1 | +0.1280 | +0.2386 |
| silver_bullet | far_edge | 511 | 281 | 36 | 29 | 28% | -0.100 ± 0.336 | -0.3 | +0.1280 | +0.1122 |
| cameron | failed_extreme | 597 | 371 | 193 | 161 | 39% | +0.038 ± 0.109 | +0.3 | -0.0559 | -0.0243 |
| cameron | far_edge | 597 | 371 | 31 | 26 | 65% | +0.871 ± 0.371 | +2.3 | -0.0559 | +0.0620 |
| pd_return | failed_extreme | 976 | 649 | 391 | 327 | 32% | +0.240 ± 0.125 | +1.9 | +0.0464 | +0.4617 |
| pd_return | far_edge | 976 | 649 | 57 | 48 | 35% | -0.170 ± 0.184 | -0.9 | +0.0464 | +0.0033 |

[exited with code 0]
