# Pre-registered: premium/discount of the range in play, and a deeper entry on the leg (written 2026-11-14, before any code or run)

Models: the 2022 model and MMxM. Sources:
- Sharif 2026-11-14: "what matters is the current trading range we are inside"; the range is "the zone we highlight or
  are expecting a retracement inside … top to center is expensive, middle to bottom is cheaper, we want to buy cheaper";
  "it doesn't invalidate the entry at the FVG … but we would like to buy cheaper"; any timeframe — "a range can be
  within a FVG itself, on the Daily". Sample 1 (TradingView 9xGZCPW1, gold 15m, Nov 2026 — outside the test period):
  buy at an OB in the 0.62–0.79 band of the leg low → new high rather than at the FVG in the expensive half.
- ICT (ruling §17): a dealing range is a high that took buyside and a low that took sellside, on the timeframe of the
  analysis; buy at 50% or lower.
- Blind triage (in-sample, review log #18): "entry too early" 16 notes, "premium" 8. Liquidity reach study
  (`liquidity-reach-2026-11-14.md`, in-sample): targets are hit at random-walk rates → the edge must come from the entry.

Both models already price the entry inside their own setup range (2022 model: discount of sweep extreme → leg high;
MMxM: discount of the curve). Sharif's "premium" calls were on trades that passed those gates, so the range here is the
**larger range price is inside at the decision**.

## Definitions (bars before the decision only)
**Range in play** at the decision, first that applies:
1. a live **4h FVG** (either direction; formed before the decision, no 1m body close beyond its far edge) that contains
   the entry price → that FVG (bottom, top);
2. else the **1h dealing range**: the newest confirmed 1h swing high that is above the 1h swing high before it (it took
   buyside) and the newest confirmed 1h swing low that is below the 1h swing low before it (it took sellside), both
   within the last 10 days and with the entry price between them → (low, high);
3. else no range → the trade is unchanged in every variant.

Cheap half for a long = at or below the range's 50%; for a short, at or above it.

**Leg** (variant 3): sweep extreme (the price the stop sits beyond) → the furthest price reached from it up to the
decision (high for a long, low for a short). OTE level = 70.5% retracement of the leg (middle of 0.62–0.79).

## Variants (everything else at the model's defaults)
| name | rule |
|---|---|
| range: entry in the cheap half | no trade when the entry lies in the expensive half of the range in play |
| range: limit at the 50% | when the entry lies in the expensive half, the limit moves to the range's 50% (stop, TP1, final unchanged); skip if that is beyond the stop; order expiry unchanged |
| leg: limit at OTE 70.5% | the limit moves to the leg's 70.5% retracement when that is deeper than the model's entry (stop, targets unchanged); skip if beyond the stop; order expiry unchanged |

The plan is frozen at the decision (no re-anchoring after it). A deeper limit means a smaller risk, so the same price
targets are more R and some trades never fill — that trade-off is what is tested. The model's cost gate (`max_cost_r`)
applies to the new risk.

## Test and decision rule
Futures basis only. US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, the variants tool's 70/30 split (OOS from
2023-09-29). Measure: expectancy with the runner (`runner_r`, 50% partial at TP1), vote rate and fill count beside it.
3 variants × 2 models = 6 cells: pass = OOS Δ vs that model's baseline with **z ≥ 2.4** and **≥ 30 OOS trades**.
Report every cell. A pass becomes a forward-v2 candidate; a TP ladder is tested only on top of a passing entry rule.
