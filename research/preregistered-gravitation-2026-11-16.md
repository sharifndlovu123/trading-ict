# Pre-registered: two-sided liquidity → let price show the side (written 2026-11-16, before any code or run)

Source: Sharif 2026-11-16 (liquidity map / top-down reviews): "sometimes we have 2 areas where we have EQHs or EQLs and
buyside or sellside showing on both sides — that's where we wait and let price show us something, to dictate what area
it's gravitating to, to follow." And: "we don't try to force price to go anywhere."
Context: the 2026-11-15 study found the models' side ≈ a coin (2R our way 73% vs against 74%); his reviewed areas did
not react more than mirror boxes (18 vs 15 touches) — the area says where to look, not which way. This tests whether
price's own move picks the side.

This is a concept/pattern test (a hit rate), not a model: no trades, no votes.

## Setup (bars before each step only)
- Assets US100 US500 US30 XAUUSD; every NY trading day 2022-01-03 → 2024-06-28; moment 08:30 NY.
- Map: `liquidity_map.build(bars, 08:30)` (commit 31f8348 rules). **Pools:** up = the nearest item in
  `key.topdown` buyside (1w ∪ 1d) above price; down = the nearest `key.topdown` sellside below.
- **Two-sided** day: both pools exist and both lie within 1.5 ADR of price. Other days are skipped (counted).

## Signal: "price shows something" (first one only, 08:30 → 12:00 NY, 15m bars)
The first 15m candle that is a displacement (`displacement_mask`, defaults k = 1.5, lookback 20, body ≥ 60% of
range) **and** closes above the high (→ up) / below the low (→ down) of everything traded from 00:00 NY to that
candle. No signal by 12:00 → no call (counted).
This is my first reading of "show us something"; Sharif's 1H-step answers in the top-down review will refine it. Any
refinement is a new pre-registration, tested on unseen data.

## Outcome
From the signal candle's close, which pool trades first on 1m bars within 5 trading days (pool = its price; touching
counts). Both in the same 1m bar or neither → excluded (counted).

## Baseline: distance, not a coin
After a move toward one pool, that pool is nearer; a nearer pool wins more often by geometry alone. Each call's
expected hit chance is the driftless gambler's-ruin value p = d_other / (d_side + d_other), distances measured from the
signal close. **Edge = hits − Σp.** z = (hits − Σp) / √Σp(1−p). Also reported: the subset where the signalled pool is
the farther one at the signal close (hit rate vs 50%).

## Decision rule
Split as the variants tool: in-sample 2022-01-03 → 2023-09-28, out-of-sample 2023-09-29 → 2024-06-28.
**Pass = OOS edge > 0 with z ≥ 2.4 and ≥ 30 OOS calls.** In-sample is reported beside it; per asset is reported, not
selected on. A pass makes "two-sided → follow the shown side" a building block for the models (bias/side step) and a
forward-test candidate; a fail is recorded in review-log and the definition goes back to Sharif's answers.
2024-07+ stays unseen.
