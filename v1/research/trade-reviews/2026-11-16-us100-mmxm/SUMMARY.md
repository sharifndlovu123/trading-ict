# US100 MMxM — 12 engine trades reviewed (8 losers, 4 winners, in-sample)

Twelve trades are leads, not evidence. Each lead was then checked on all 221 MMxM and 573 2022-model US100 trades (see "At scale" below).

Verdicts: 8 lesson losses, 3 earned wins (2023-02-01, 2023-12-26, 2024-01-16), 1 lucky win (2022-05-27).

Step 6 (trigger) is graded on a proxy (risk in ADR = distance from the reversal extreme; price back inside the swept level), because the sheets don't print the model's MSS or entry FVG. Step 7: "at the liquidity" is by construction and not counted; partial/fail = the stop is short of a nearby pool or inside the array.

## 1. Tally (pass / partial / fail / n/a)

| # | Step | Losers (8) | Winners (4) |
|---|---|---|---|
| 1 | Time | 7 / 1 / 0 / 0 | 4 / 0 / 0 / 0 |
| 2 | Bias / narrative | 3 / 2 / 3 / 0 | 3 / 1 / 0 / 0 |
| 3 | Dealing range | 4 / 1 / 3 / 0 | 2 / 0 / 2 / 0 |
| 4 | POI / array | 1 / 4 / 3 / 0 | 4 / 0 / 0 / 0 |
| 5 | Liquidity before | 3 / 3 / 2 / 0 | 3 / 0 / 1 / 0 |
| 6 | Trigger (proxy) | 1 / 3 / 4 / 0 | 2 / 2 / 0 / 0 |
| 7 | Stop | 0 / 5 / 3 / 0 | 2 / 1 / 1 / 0 |
| 8 | Targets | 1 / 7 / 0 / 0 | 1 / 3 / 0 / 0 |
| 9 | Management | 0 / 4 / 0 / 4 | 1 / 3 / 0 / 0 |
| 10 | Attribution | 0 / 0 / 8 / 0 | 3 / 0 / 1 / 0 |

POI (4), trigger (6), stop (7) and bias (2) separate losers from winners in this sample. Dealing range (3) does not.

## 2. The failures that repeat on the losers
- **a. Side against the engine read:** 5 of 8 losers, 1 of 4 winners (2022-10-19, 2022-11-30, 2023-03-21, 2023-08-16, 2024-04-09).
- **b. Micro risk (≤ 0.031 ADR, 6–7 points; the entry sits on the reversal extreme):** 4 of 8 losers, 0 winners (2022-11-30, 2023-03-31, 2023-04-05, 2024-04-09). Winners risked 0.062–0.191 ADR.
- **c. Stop short of a nearby pool, or inside the array:** 7 of 8 losers, also 2 winners. Examples: 2022-11-30 London high 9 points beyond the stop; 2023-04-05 London low 12 points beyond; 2022-10-19 PDL 22 points beyond; 2023-08-16 PWL 15 points beyond.

## At scale (pattern-finder on every US100 trade, 2026-11-16)
| Lead | MMxM (221) | 2022 model (573) | Verdict |
|---|---|---|---|
| a. against the read | 29% win vs 34% with | 34% vs 33% | **Does not hold.** The read's side doesn't separate wins at scale |
| b. micro risk ≤ 0.031 ADR | 0 of 7 win | 24% win, −0.38 R (n 197); win rate rises with risk: 34% → 41% → 45% | **Holds in both models** → change gate |
| c. stop short of a pool | 24% (n 25) vs 33% | 32% vs 35% | Weak; not enough to act on |

## 3. Flags for a PD-array audit
| Trade | What looks wrong |
|---|---|
| 2022-10-19, 2024-04-09 | The model's POI (a 1h FVG) is not among the map's arrays near price: model and map disagree on whether it exists / is valid |
| 2023-04-05, 2024-01-16 | The read says "no buy array left" while the map lists one near price |
| 2022-11-30, 2023-04-05 | The reversal extreme used for the stop is not the session extreme |
| 2023-04-05, 2023-03-21 | "ran asia_low" / "ran pdh" has no matching sweep in the 6 h before |
| 2022-09-14, 2024-04-09 | "Asia high/low taken" during the Asia session itself: `swept_before` uses the running session extreme |
| six trades | Sliver arrays 0.05–0.35 points wide take slots near price (the < 0.01 filter lets them through) |

## 4. For the engine (testable rules)
1. `min_risk_adr`: skip (or widen) a plan whose risk is under ~0.03–0.05 ADR. **Supported at scale.**
2. `entry_gate="read_side"`: not supported at scale; drop.
3. Pool-aware stop: beyond any untaken pool within 0.1 ADR of the reversal extreme. Weak at scale; measure as an option.
4. `news_blackout=(45, 0)` for premarket entries before 08:30 releases. Two trades only.
5. `tp1_front_run` and a runner where TP1 = final (8 of 12 plans have one TP at 100%).
