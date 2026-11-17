# Pre-registered: nested FVG entries, no trades inside a daily FVG, first target at the range's 50% (written 2026-11-14, before any code or run)

Models: the 2022 model and MMxM. Source: Sharif's batch-3 review (review log #14–16):
- #14 (Cameron Mar 15, Aug 27 2024): "better entry … based off of a higher tf FVG, then we get a sub FVG on 15 min";
  "better sell entry off of a bigger FVG" → the entry FVG belongs **inside** a higher-timeframe FVG.
- #15 (MMxM Sep 27 2024, 2022 model Mar 13 2024): "the goal was a long into the daily FVG, not trading inside it".
- #16 (MMxM Mar 15 2024): "failed to reach the FVG, but we were at the 50% of this smaller range".

Disclosure: Mar 13/15 2024 lie inside this test's out-of-sample window (2023-09-29 → 2024-06-28). They are 3 trades
of ~540 OOS trades and inspired the rules; they are not removed (removing chosen days would be its own bias).

## Variants (everything else at the model's defaults)
| name | rule |
|---|---|
| loc: entry FVG inside a 4h FVG | the model's entry FVG has its midpoint inside a 4h FVG of the trade's direction (bullish for a long) that formed before the decision and is still valid then (no 1m body close beyond its far edge) |
| loc: not inside a daily FVG | no trade when the entry price lies inside any daily FVG (either direction) still valid at the decision |
| targets: 50% of the 4h range, runner to the HTF draw | dealing range = the newest confirmed 4h swing high and swing low (last 10 days, finished candles only); TP1 = its 50% when that lies ahead of entry by ≥ the model's minimum TP1 (1 R), else TP1 unchanged; 50% off at TP1; runner to the nearest higher-timeframe draw ≥ 3 R (as the `hold` mode), flat 16:55 |

Gates are judged with bars up to the decision only. FVGs from the engine's detector (`events.fvgs`, displacement not
required for the HTF gap); validity from `gap_lifecycle`.

## Test and decision rule
Futures basis only. US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, the variants tool's 70/30 split.
Measure: expectancy **with the runner** (`runner_r`, the engine's 50% partial), vote rate beside it. 3 variants ×
2 models = 6 cells: pass = OOS Δ vs that model's baseline with **z ≥ 2.4** and **≥ 30 OOS trades**. Report every
cell. A pass becomes a forward-v2 candidate; two passing rules on one model are not stacked without a new test.
