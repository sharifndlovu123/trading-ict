# New datasets — what repeats, what's new, what we get wrong and right (2026-11-16)

Backtest pipeline A on data never backtested before, free Dukascopy CFDs, futures cost basis, four models (2022 model, MMxM, silver bullet, cameron):
- **New years:** 2020 on US100 / US500 / US30 (2021 stays untouched as the clean confirmation year).
- **New assets:** gold, silver, dollar index, EUR/USD on 2022-01-03 → 2024-06-28.
- Compared with the three indices on 2022–24. 7,364 trades in total, each with its entry hour and market activity (`reports/time-activity-2026-11-16.parquet`, scores in `reports/scores-new-datasets-2026-11-16.csv`).

Win = TP1 traded before the stop. Activity = the range of the 60 minutes before the fill ÷ the normal range for that clock time (previous 20 weekdays): quiet < 0.6, busy > 1.5.

## 1. What repeats on every dataset
| Finding | Evidence |
|---|---|
| **No model has an edge at its defaults** | 28 model × dataset results: win rate 23–40%, mean R between −0.23 and +0.26, none with z ≥ 2 except MMxM on gold (a loss) and cameron on US100/US500 (losses) |
| **TP1 at 1 R gives ~45–55% wins and ≈ 0 R** | Indices and gold, both periods: the coin-flip result. Win rate follows target distance |
| **Quiet markets lose** (Sharif: "be in the market when price is moving") | All models: quiet −0.170 R (n 675, z −3.2), normal −0.047, busy **+0.045** (n 1,640). Busy beats quiet in **6 of 7 datasets**, including 2020 and gold |
| …most of all for the 2022 model | Quiet: 26% win, −0.35 R (n 160, z −3.7). Not quiet: 35.7%, −0.015 R. Busy: 39%, +0.11 R (n 377). Quiet is worse than the rest in 6 of 7 datasets (z −3.3 for the difference) |
| **The 02:00 NY hour loses** | −0.115 R (n 586), negative in **7 of 7 datasets**; the 2022 model (−0.14) and cameron (−0.17); MMxM is flat there |
| **08:00 NY loses for the 2022 model and cameron** | −0.16 and −0.20 R (n 198, 279) |
| **MMxM's NY PM trades rarely reach TP1** | 10% win in 2022–24, 17% in 2020 (targets too far for the time left) |

## 2. What is new
| Finding | Evidence |
|---|---|
| **MMxM made money in 2020 on all three indices** | US100 +0.26 R, US500 +0.18, US30 +0.20; pooled 36.4% win, **+0.213 R, z 2.5 (n 308)**. In 2022–24 it was −0.06 R. The model works in a trending, volatile year and not in the choppier 2022–24: regime matters |
| **The stop-size rule is noise** | Risk ≥ 0.05 ADR helps on US100 2022–24 and US30 2020, hurts on US30 2022–24, US100 2020 and gold. No consistent sign. Dropped |
| **Cameron is not a loser everywhere** | Gold +0.03 R, 2020 indices −0.02 to −0.08. Its clear losses are US100 and US500 in 2022–24. Still no edge anywhere |
| **MMxM loses on gold** | 23% win, −0.23 R (n 230, z −2.9) |
| **The engine cannot trade silver, the dollar index or EUR/USD** | The 2022 model needs 10 points to its target and MMxM a minimum TP1 distance, both in index points. Silver (~23), DXY (~95) and EUR/USD (~1.08) never offer that: 0 trades, or 8–19% win rates from targets forced far away. A unit bug, not a market result |

## 3. What we normally get wrong
1. **Entering when the market is quiet.** The clearest repeated loss, on old and new data.
2. **Hunting at 02:00 and 08:00 NY** (2022 model, cameron).
3. **Targets too far for the time left** (MMxM in the NY PM: 10–17% reach TP1).
4. **Direction at the entry.** At an even 1 R target the entries win about half the time. The setups don't yet say which way price goes next.
5. **Trusting a pattern seen on one asset.** The stop-size rule looked like the best finding on US100 and failed on US30.

## 4. What we normally get right
1. **Losses are controlled:** the average loser is about −1 R on every dataset; nothing blows up, including March 2020.
2. **Busy conditions:** in an active market the models are at or slightly above breakeven (+0.045 R over 1,640 trades), the 2022 model at 39% wins.
3. **MMxM in London:** its best window in both periods (43% win in 2020, 37% in 2022–24).
4. **The sweep requirement works as designed:** almost every trade has liquidity taken first.

## 5. Decisions (pipeline rules)
| Item | Rule | Decision |
|---|---|---|
| Activity gate: no entry when the last hour is quiet | R3 → B | **Option behind a flag**, then one pre-registered run on 2021 (never touched). Needs Sharif's go-ahead for the 2021 run |
| Thresholds in index points (silver, DXY, EUR/USD) | R5 → B | **Bug fix** through the change gate: scale `min_potential`, `stop_buffer` and MMxM's minimum TP1 distance by the asset's ADR; indices must stay unchanged (R7) |
| 02:00 hour for the 2022 model and cameron | R2 | Measure as a window variant alongside the activity gate |
| Stop-size floor | — | Dropped (noise across datasets) |
| MMxM, 2020 vs 2022–24 | R3 | Lead: what made 2020 different (trend, volatility)? Measure with a regime trait before any rule |
| MMxM on gold; cameron | R2 | Parking either is Sharif's call |
