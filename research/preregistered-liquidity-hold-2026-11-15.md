# Pre-registered: the turn that adds liquidity — a near-equal hold instead of a sweep (written 2026-11-15, before any code or run)

Models: the 2022 model and MMxM. Sources:
- Sharif, review log #21: at the key time price may **add** liquidity instead of taking it; #22 (NQ Sep 25 2023,
  in-sample): his 11:00 long turned at 14651.2, just above the earlier low 14649.6 — sellside built, not taken; the engine
  found the 11:05 shift but the 2022 model needs a sweep and MMxM a purge. #27 (NQ Nov 17 2023, OOS, illustration only):
  the top made equal highs instead of sweeping.
- ICT (ruling §18, engineered liquidity): liquidity is created and then taken — a turn that leaves equal lows behind
  is the "created" half.

Today both models need opposite liquidity **taken** before the shift (2022 model: a sweep or run of a context level or
swing within `sweep_lookback_min` = 90 min before the MSS; MMxM: the reversal low purges a context level, an older
framing swing or equal lows). This test adds a second way in: the turn **holds** just short of resting liquidity.

## Definition (bars before the decision only)
A **hold** for a long (mirror for a short), tolerance `tol` = 2 bp of price (the equal-levels tolerance used in the
liquidity-reach study):
- the turn = the lowest low in the trigger's search span (2022 model: the 90 min before the MSS candle; MMxM: the
  reversal low the model already finds);
- a resting sell-side level below it — 2022 model: a context level (PDL, PWL, Asia low, …) or a **5m** swing low
  (1m swings excluded: too fine); MMxM: a context level below the OC or an older framing swing low formed before the OC
  (the same candidates its purge rule uses) — known before the turn bar;
- the turn's low is **above** the level by at most `tol` (it did not trade through), and the level was untaken from
  when it formed up to the shift;
- 2022 model only: the turn bar is inside one of the model's time windows (the "key time").

When a setup has a real sweep/purge, nothing changes (the sweep is used). The hold only applies where the baseline
fails for lack of taken liquidity. Every later gate still applies: displacement FVG, time, bias, pricing, POI (2022
model: a held context level counts as HTF liquidity; otherwise a live 1h/4h FVG must contain the turn's low; MMxM: its
HTF-array rule unchanged), targets, cost, window cap. Stop beyond the turn's extreme, as today.

## Variants (everything else at the model's defaults)
| name | rule |
|---|---|
| trigger: hold within 2 bp (2022 model) | `liquidity_hold_bp = 2` |
| purge: hold within 2 bp (MMxM) | `liquidity_hold_bp = 2` |

## Measure and decision rule
The rule adds trades (and can displace one through the window cap), so — as in the counter-bias test — measure per
asset-day: **ΔR = Σ `runner_r` of the variant's trades − the same for the baseline**, over days where the trade list
differs. Futures basis; US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28; out-of-sample = days from 2023-09-29
(the variants tool's 70/30 split). 2 cells: **pass = OOS mean ΔR per changed day > 0, z ≥ 2.4, ≥ 30 changed days.**
Reported beside it: the admitted trades (n, win rate, expectancy with runner) and the displaced baseline trades, IS and
OOS. Every cell is reported. A pass becomes a forward-v2 candidate.

Regression check (not a selection input): the US100 Sep 25 2023 11:00 turn should be found as a hold by the 2022 model
(it may still fail bias — that is the expected outcome, ruling §17/#20).

## Amendment (2026-11-15, during the build, before any sweep or result)
Probing the regression day (US100 Sep 25 2023) showed the 2022 model's trigger is almost never the block: the 11:05
turn swept a trivial **1m** swing low (10:31) on its way down, so the trigger passed and the setup failed the **POI**
gate ("no HTF POI under the sweep"), plus bias. A trigger-only fallback would barely change trades. So, for the 2022
model, the hold also counts at the POI gate: when the setup has no POI, the manipulation extreme (the stop's anchor)
holding within 2 bp short of an untaken **context level** (PDL, PWL, Asia low; mirror for shorts — the same names that
count when swept) passes the POI as "held <name>". The trigger fallback above stays. MMxM is unchanged (its purge sits
inside the POI gate already). Still 2 cells, same measure and pass rule. The Sep 25 11:05 setup is a check of the code,
not of the idea; it is expected to still fail bias either way.
