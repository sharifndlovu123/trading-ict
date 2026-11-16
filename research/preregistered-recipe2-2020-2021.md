# Pre-registration (DRAFT — waits for Sharif's go-ahead) — the improved recipe on 2020–2021

Drafted 2026-11-16, before any run of this model on any date before 2022. Nothing below has been run.

## The rule (fixed; commit of the code is recorded when the run is made)
PD-array-return model, variant `recipe2: full + not against 1h&4h + within 0.25 ADR + before 14:00` in `ict_engine/eval/variants.py`:
- the area: a 1h or 4h FVG, formed in the last 5 days, reached to its 50% (`return_level="ce"`);
- the trigger: a 15m FVG in the area's direction completing within 4 hours of that (`trigger_tf="15m"`, `trigger_wait_min=240`);
- entry: limit at that gap's near edge; stop beyond the reaction extreme; TP1 = the nearest untaken liquidity at least 1 R away, 50% off, runner at breakeven;
- no daily bias; windows `ny_am_kz` (08:30–11:00) and `ny_pm_kz` (13:30–16:00);
- **side not against both the 1h and the 4h structure** (`structure_gate="not_against"`);
- **entry within 0.25 ADR of the area** (`max_entry_dist_adr=0.25`);
- **no new setup after 14:00** (`last_entry="14:00"`).
Where it comes from: Sharif's notes on the engine's trades (`research/entry-trigger-from-saves-2026-11-16.md`); the last three gates were added after the 30-trade review of the first coding (`research/trade-reviews/2026-11-16-recipe/SUMMARY.md`).

## What was seen (selection data: three indices, 2022-01-03 → 2024-06-28)
130 trades, 36.2% win, +0.187 R (z 1.69); US100 +0.16 (46), US30 +0.26 (47), US500 +0.12 (37); halves +0.22 / +0.15. The model's baseline: −0.012 R (n 2,790). The three gates and their thresholds (0.25 ADR, 14:00) were chosen on this data, so this number is optimistic by construction.

## The hold-out
- **2020-01-02 → 2021-12-31, US100 / US500 / US30**, Dukascopy CFD 1m, futures cost. The PD-array-return model has never been run on any date before 2022. 2021 has not been used by anything; 2020 was used on 2026-11-16 for the other four models' baselines and the time/activity analysis, not for this model or for choosing these gates.
- Expected size: about 50 trades a year over the three indices, so roughly 100.

## Outcomes (decided now)
Primary measure: `r` (all out at TP1), pooled over the three indices and both years.
| Outcome | Condition | What follows |
|---|---|---|
| **Confirmed** | ≥ 60 trades, mean R > 0 with one-sided z ≥ 2.4 | The recipe becomes a model of its own in the registry and the reference for further work |
| **Consistent** | ≥ 60 trades, mean R > 0, positive on at least 2 of 3 indices and in both years, z < 2.4 | Kept as the lead candidate: it goes to the forward log and to the remaining clean assets (below); not a default, not called proven |
| **Fail** | mean R ≤ 0, or negative on 2 of 3 indices, or a year clearly negative (≤ −0.10 R) | Logged as failed. The gates were fitted to 2022–24. No re-tuning on 2020–2021 |
With about 100 trades and a true edge of the size seen in-sample (+0.19 R), z ≥ 2.4 is unlikely even if the edge is real (expected z ≈ 1.5). "Consistent" exists so that a real but modest edge is not thrown away, and so that it is not over-claimed either.

Reported beside it, not part of the outcome: win rate with its Wilson range; runner R; TP1 at 1 R and at 2 R; the stop × 1.5 with TP1 at 1 R what-if (48.5% win, +0.17 R in-sample); results by hour.

## Second check, only if the outcome is Confirmed or Consistent
The same variant, unchanged, on gold, silver, the dollar index and EUR/USD for 2022-01-03 → 2024-06-28 (this recipe has not been run on them). Reported per asset; no pass bar.

## After the run
A 30-trade written review of the hold-out trades (15 winners, 15 losers), as for every run.

## Result
_(not run)_
