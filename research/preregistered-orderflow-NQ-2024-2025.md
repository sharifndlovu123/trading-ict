# Pre-registered: order-flow tests on NQ, 2024-01 → 2025-12

Written 2026-11-14, **before any order-flow data was downloaded**. Data: Databento GLBX.MDP3, schema TBBO (every
trade with its aggressor side, plus the best bid/offer just before it). Continuous front month `NQ.v.0`. Paid
from the free $125 credit, quoted with `get_cost` first. Source of the hypotheses: `research/gap-sweep-2026-11-14.md`
§4. Book background: `references/orderflow.md` §1–2, §10–11.

## Why this period is still a fair test
Price-only results on 2024-07+ are burned (looked at repeatedly). **No order-flow feature has ever been computed
on any period**, so these tests are fresh. The engine's setups are fixed by code that existed before this file
(`forward-v1` + the 2022-model `entry_mode`). Only the order-flow split is new.

## Setup source
- The engine is run on **1m bars built from the NQ trades themselves** (OHLC from trade prices, volume from sizes).
  Setup prices and order-flow prices are then on the same instrument, with no CFD basis.
- Models at their defaults, futures cost basis:
  - `2022_model` (limit), plus its `entry_mode="market"` variant for H1;
  - `cameron`, `mmxm`, `silver_bullet`, `pd_return`.

## Measures (fixed now)
- Signed volume: aggressor buy = +size, aggressor sell = −size. Databento's trade `side` is the initiating side:
  **B = buy aggressor, A = sell aggressor**, N = dropped. (Corrected 2026-11-14, still before any data. The first
  draft had it reversed.) A data check runs before any test: buy-aggressor trades must print at the ask far more
  often than at the bid.
- **Aligned imbalance** over a window W: I = (buy − sell) / (buy + sell), with the sign flipped for shorts, so
  I > 0 means flow in the trade's direction.
- **Trigger window:** W = the 5 minutes ending at the decision (`decided_at`).
- **Absorption at the stop:** in the 5 minutes after a stop-out:
  - V = volume traded within ±4 ticks of the stop, divided by the median 5-minute volume for that half-hour of the
    day over the previous 20 trading days (no look-ahead);
  - F = how far price went beyond the stop, in R.
  - "Absorbed" = V in the top tercile **and** F < 0.5R.
- Terciles are cut on 2024 data and applied unchanged to 2025.

## Hypotheses (3 primary tests; pass = one-sided z ≥ 2.4, Bonferroni 0.05/3; standard errors clustered by day)
- **H1, missed entries (2022 model).** Setups in the top tercile of trigger I are "missed" (TP1 before the
  limit fill) more often than those in the bottom tercile.
  - Secondary, only if H1 passes: in the top tercile, market entry R > limit R.
  - Practical rule if it holds: enter at market only when flow is one-sided.
- **H2, fast losses (all five models pooled).** Trades with I < 0 at the trigger (flow against the trade) have a
  lower mean R than trades with I > 0.
- **H3, absorption at stops (all models pooled, stop-outs only).** For absorbed stop-outs, P(TP1 trades before the
  equal-distance mirror level, measured from the stop) exceeds the same probability for non-absorbed stop-outs.
  §2 of the gap sweep found the two to be equal overall.

## Reporting
- All three results are reported whatever they show: n, effect, z, and 2024 and 2025 separately.
- A passing result is a **candidate**, not a default. It goes into the forward test as a new version, with its
  own clock.
- Anything explored beyond H1–H3 is labelled exploratory and can't be used to justify a rule.
