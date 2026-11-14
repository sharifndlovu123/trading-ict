# Order-flow results: CME NQ 2024 (pre-registered H1–H3)

Run 2026-11-14, once, exactly as in `research/preregistered-orderflow-NQ-2024-2025.md` (+ amendments 1–2).
Code: `ict_engine/eval/orderflow_tests.py`; model runs `research/scripts/nq_cme_runs.py` (futures costs, 2024,
CME 1m bars); data: 2024 NQ.v.0 `trades` (Databento, ~94M trades, side check 99.999 % B-at-ask).
Raw table: `reports/orderflow-tests.md`.

## Result: all three fail
| Test | n | Effect | z (one-sided, day-clustered) | Pass needs |
|---|---|---|---|---|
| H1: one-sided flow before the decision → 2022-model limit orders "missed" more | 404 | missed 54 % (top tercile) vs 47 % (bottom), +7.4 pts | +1.43 | 2.4 |
| H2: trades against the flow (I < 0) earn less | 1242 | I > 0: +0.012 R, I < 0: +0.079 R (Δ −0.067, wrong sign) | −0.54 | 2.4 |
| H3: absorbed stop-outs (heavy volume at the stop, < 0.5R overshoot) see TP1 before the mirror more often | 827 | 41 % (n 123) vs 40 % | +0.17 | 2.4 |

H1b (market vs limit entry in the top tercile) was not run: it was gated on H1 passing.
Halves (reported, not tested): H1 +0.63 / +1.37, H2 −0.75 / −0.14, H3 +1.14 / −0.93 (2024-H1 / H2). No half is
anywhere near 2.4, and H3 flips sign between halves.

## What it means
1. **The 5-minute flow at the trigger carries no usable information about these setups.** The decision follows
   a displacement, so flow at the trigger is almost always mildly with the trade (tercile cuts I = +0.05 / +0.11).
   Knowing how one-sided it was doesn't separate winners from losers (H2) and only weakly predicts that the
   limit order is left behind (H1, right sign, z 1.4).
2. **Stop-outs are not "absorbed hunts" in any way volume can see** (H3 ≈ 0). This agrees with the gap sweep's
   price-only control (§2: TP1-after ≈ mirror-after). A stop-out followed by TP1 is volatility, not a
   reversal that heavy volume at the stop could have flagged.
3. **The engine's feed is not the problem.** On real CME candles every model finds almost the same trades as on
   the Dukascopy CFD (2022 model 202 vs 202, Cameron 253 vs 255, PD return 530 vs 522) with similar R.

## So: how does order flow enter the models, and which models to keep?
- **No order-flow rule is adopted.** None of the pre-registered uses passed, so nothing becomes a gate, filter or
  entry switch. Anything found by looking further at 2024 is exploratory and can't justify a rule (the
  pre-registration says so). A new idea would need its own pre-registration and 2025 flow data (~$110, unbought).
- **Models:** the order-flow tests give no reason to prefer one model. The decision stays with the forward test
  (`forward-v1`, both cost bases). Order flow stays useful as a **review tool**: the delta bars are now on the
  trade review page, for reading single trades (Sharif's use for the microstructure books), not as an edge.
- If a later idea is worth testing, the better candidates are slower, structural uses of flow (e.g. cumulative
  delta divergence at the HTF POI over the whole approach, not 5 minutes at the trigger). Write it down before
  buying 2025.
