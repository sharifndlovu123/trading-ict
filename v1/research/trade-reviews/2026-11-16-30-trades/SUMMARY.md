# 30 trades reviewed for price (15 winners, 15 losers) — and the leads checked on all 4,656 trades

Three focus models (2022 model, MMxM, silver bullet) on US100 / US500 / US30, in-sample 2022–24. Two reviewers, 15 trades each; the per-trade files are in this folder, the fact sheets in `../sheets/2026-11-16-30-trades/`. 30 trades are leads; the table at the end is the check at scale.

## What the reviews saw
**Where price really turned**
- Winners: the turn was at a level known at the entry in 14 of 15 (a 1h/4h/1d FVG or IFVG edge, a swept session level). It was **0.02–0.05 ADR from the entry** (median), always inside the stop. Three winners survived by a point or two.
- Losers: the same-swing turn was typically **~0.4–0.5 ADR past the entry and ~0.44 ADR beyond the stop**, most often at the next HTF array or at / just past the previous day's high or low. On about half the losers the sheet's "turn" was a different swing many hours later.
- Loser risk was 0.03–0.06 ADR; winner risk about 0.11 ADR (median).

**Pricing mistakes that repeat on the losers**
1. The stop inside the array being traded, or just short of an untaken pool (14 of 15 losers).
2. The entry at the lower-timeframe gap while the same-side HTF array (or the OTE) sat 0.1–0.8 ADR further (9 of 15).
3. Targets on or beyond a pool, or through opposing arrays (5 of 15); three winners missed a TP by under a point because it sat exactly on a pool.

**What winners did differently:** entry on the edge of a 1h/4h/1d array, after liquidity was taken against the trade, near targets. Their stops also sat on pools, so that alone does not separate the groups.

## The leads as tweaks on every trade (`research/tweaks/2026-11-16-levels.md`)
| Tweak from the reviews | Trades touched | Win % | Mean R | Fixed / broken | Datasets better | Verdict |
|---|---|---|---|---|---|---|
| As traded | – | 33.5 | +0.006 | – | – | |
| Stop beyond the array the trade sits in | 3,254 | 50.4 | −0.004 | 784 / 0 | 12 of 20 | Win rate only: R unchanged (rule R11) |
| Stop beyond the pool within 0.15 ADR | 2,741 | 44.1 | +0.008 | 490 / 0 | 9 of 20 | Win rate only |
| Skip when a pool sits within 0.15 ADR beyond the stop | 2,741 skipped | 34.0 | **+0.053** on the 1,915 kept (skipped: −0.027) | – | 11 of 20 | Weak lead (z ≈ 1) |
| TP1 in front of the first pool | 583 | 34.3 | +0.004 | 35 / 0 | 6 of 20 | No value |
| Entry at the HTF array instead of the LTF gap | 3,905 | 31.3 | **−0.063** | 492 / 1,059 (1,475 missed) | 7 of 20 | Worse (z −2.0) |
| Skip when no HTF array is at the entry | 1,038 skipped | 33.9 | +0.011 | – | 9 of 20 | No value |

## Reading it
- The reviews were right about **what happened** on those 30 trades and wrong about **what to change**: moving the stop beyond the array or the pool fixes hundreds of trades, and each win is worth proportionally less. Mean R does not move.
- Waiting for the deeper HTF array loses: the trades that never come back to it are the good ones (1,475 missed), the same result as "entry deeper" in the geometric tweak lab and the engine plan's touch-vs-miss finding.
- So the loss is not in where the stop or the entry sits. The entries don't predict direction; the remaining places to look are **which setups to take and when** (market activity at the fill, time of day, regime: MMxM's 2020 vs 2022–24).

## PD-array flags raised by the reviewers (for the array audit)
- A model POI that the map labels the opposite way at the same prices (2022-06-06: bullish POI = the read's 4h bearish IFVG).
- Model POIs missing from the map's arrays near price (2022-03-14, 2023-05-12).
- Overlapping opposite arrays on one TF (2023-08-16 1h; 2024-04-04 US30 1d), near-duplicate daily arrays (2022-07-22, 2023-02-28), a merged-looking POI (2024-04-22), very wide arrays (4h IFVG 1.6 ADR, 2023-01-10), arrays still labelled bearish with price above them (2022-02-03, 2023-07-28).
