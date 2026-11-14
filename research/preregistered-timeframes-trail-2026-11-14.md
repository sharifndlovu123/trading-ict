# Pre-registered: the two models on higher timeframes, and a trailed runner (written 2026-11-14, before any code or run)

Models: the 2022 model and MMxM only (`research/model-selection-2026-11-14.md`). Sharif: "the tps are very small, where
some have grand opportunities"; "2022 model and mmxm plays can work with a range of time frames"; "model is key".

## What motivated it (in-sample only: 2022-01-03 → 2023-09-28, futures; scratch diagnosis, not scored)
Winners ran a median **3.9 R** (2022 model, TP1 capped at 2 R) and **5.1 R** (MMxM, TP1 median 1.6 R) before the stop or
16:55; 38% / 51% of winners reached 5 R. Expectancy all out at TP1 −0.06 / −0.08 R; with today's runner (50% at TP1,
runner stop at entry, fixed final target) −0.02 / −0.06 R. Counting agreeing bias reads did not separate run size.
The out-of-sample 30% (2023-09-29 → 2024-06-28) was not looked at.

## Variants (everything else at the model's defaults)
| model | name | change |
|---|---|---|
| 2022 model | entry 5m | `entry_tf="5m"`, `sweep_lookback_min=180`, TP1 swings from `15m` |
| 2022 model | entry 15m | `entry_tf="15m"`, `sweep_lookback_min=360`, TP1 swings from `1h` |
| 2022 model | runner trailed on 5m | `runner_stop="trail_5m"` (below) |
| MMxM | frame 1h → entry 15m | `frame_tf="1h"`, `entry_tf="15m"`, `curve_max_h=48`, `low_lookback_min=480` |
| MMxM | frame 4h → entry 1h | `frame_tf="4h"`, `entry_tf="1h"`, `curve_max_h=192`, `low_lookback_min=1440` |
| MMxM | runner trailed on 5m | `runner_stop="trail_5m"` |

Lookbacks scale with the entry chart so the same model shape fits (the sweep/low must fall inside the leg that the
higher-timeframe MSS breaks). Time windows, bias, POI, cost gate and the 2022 model's 2 R TP1 cap are unchanged.

**Trailed runner** (`trail_5m`): 50% off at TP1 as today. The runner's stop starts at entry, then after every finished
5m candle it moves up (long; down for short) to the newest confirmed 5m swing low (a 5m low with a higher low on each
side, known when the third candle closes), never back. No fixed final target: the runner rides until trailed out or
the session close (16:55 NY futures). Only finished candles are used (no look-ahead).

## Test and decision rule
Futures basis only. US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, the variants tool's 70/30 split.
Measure: expectancy **with the runner** (`runner_r`), vote rate beside it. 6 cells: pass = OOS Δ vs that model's
baseline with **z ≥ 2.4** (6 one-sided tests, 5% family-wise) and **≥ 30 OOS trades**. Report every cell; a
higher-timeframe variant with fewer than 30 OOS trades fails by rule, whatever its mean. 2024-07+ unused.
A winner becomes a forward-v2 candidate; two winners on one model are not stacked without a new test.
