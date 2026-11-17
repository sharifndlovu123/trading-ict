# Pre-registration — activity gate (`min_activity` 0.6) on 2021 (never tested)

Written 2026-11-16 before any run on 2021. **Status: not run — the in-sample condition failed after the DST fix (below); 2021 stays untouched.** Sharif approved the run on 2026-11-16 ("Proceed"), on the condition stated to him: only if the gate holds on the data already used.

## The rule
No new setup when the range of the 60 minutes before the decision is under 0.6 × the median range of the same clock window over the previous 20 weekdays (`ict_engine.concepts.activity`, variant `activity >= 0.6`). Threshold 0.6 was fixed from the fill-time analysis in review log #40 and is not tuned further.

## What was already seen (selection data)
2022-01-03 → 2024-06-28 on US100 / US500 / US30 / gold, and 2020 on the three indices: quiet entries −0.170 R (n 675, z −3.2) vs busy +0.045; busy > quiet on 6 of 7 datasets. That analysis filtered existing trades by activity at the fill; the gate acts at the decision and frees the window's trade slot, so its real effect is measured by the in-sample variant run below.

## Condition to spend 2021
For a model to go to 2021, its in-sample variant run (2022-01-03 → 2024-06-28, three indices) must show the variant's mean R above the baseline's **pooled and on at least 2 of the 3 indices**. Models that fail the condition are not run on 2021.

## The hold-out
- 2021-01-04 → 2021-12-31, US100 / US500 / US30, Dukascopy CFD 1m, futures cost. No backtest, sweep, read or review has used 2021.
- Models: those of the 2022 model, MMxM and silver bullet that met the condition. Baseline and `activity >= 0.6` only.

## Pass bar (pooled over the qualifying models and the three indices)
1. The trades the gate removes (baseline trades that the variant does not take) number ≥ 30.
2. Their mean R is below the mean R of the trades the variant takes, with Welch z ≥ 2.4.
3. The variant's mean R is at or above the baseline's on at least 2 of the 3 indices.
One year of quiet-market trades is a small sample (about 10% of trades are quiet): the bar may not be reachable even if the effect is real. A result with the right sign and z between 1 and 2.4 is recorded as "not confirmed", not as a pass.

## Outcomes
- **Pass:** `min_activity = 0.6` becomes the default for the qualifying models through the change gate.
- **Not confirmed / fail:** logged; the option stays off; 2021 is not reused for this rule.

## In-sample variant runs (2022-01-03 → 2024-06-28, three indices)
**Decision-time gate (`activity >= 0.6`), run 2026-11-16:** weak, not taken to 2021.
| Model | Baseline R | Gate R | Indices better | Trades removed |
|---|---|---|---|---|
| 2022 model | −0.066 (n 1,105) | −0.059 (n 1,017) | 2 of 3 | 106 at −0.157 R vs kept −0.057, z −0.75 |
| MMxM | −0.004 (n 618) | −0.023 (n 574) | 1 of 3 | 49 at +0.266 R |
| Silver bullet | +0.013 (n 1,216) | +0.014 (n 1,176) | 1 of 3 | 77 at +0.054 R |

## Amendment 1 (2026-11-16, before any run on 2021): the rule tested is the fill-time mode, 2022 model only
The evidence in review log #40 measured activity at the **fill**; the decision-time gate above acts at a different moment and the effect mostly disappears. The rule taken to 2021 is therefore:

> `activity at fill >= 0.6` (`min_activity=0.6, min_activity_at="fill"`): the resting order is pulled when the range of the 60 minutes before the fill is under 0.6 × normal for that clock time. **2022 model only** (MMxM and silver bullet showed no effect at either moment and are not run).

First in-sample run of this mode (before the DST fix to the baseline window):
| | Baseline | Fill-time gate |
|---|---|---|
| Pooled | −0.066 R, 33.8% win (n 1,105) | −0.033 R, 34.8% (n 998) |
| US100 / US500 / US30 | −0.076 / +0.009 / −0.104 | −0.011 / +0.017 / −0.110 |
| Removed trades | | 114 at −0.356 R (25% win) vs kept −0.033 R; Welch z −2.67; both halves better |
Caution written before the hold-out: almost all of the effect is US100 (68 removed at −0.565 R); on US30 and US500 the removed trades were no worse than the kept ones. The pass bar's "at least 2 of 3 indices" is the check on that.

The in-sample run is repeated after the DST fix (calendar-day baseline) and its table appended below; the condition (pooled better and ≥ 2 of 3 indices) must still hold for the 2021 run to go ahead. Pass bar, hold-out period and outcomes are unchanged from above, with "the qualifying models" = the 2022 model.

### In-sample, fill-time gate, after the DST fix (run 2026-11-16)
| | Baseline | Fill-time gate |
|---|---|---|
| Pooled | −0.066 R, 33.8% win (n 1,105) | −0.044 R, 34.4% (n 998) |
| US100 | −0.076 | −0.015 |
| US500 | +0.009 | +0.003 |
| US30 | −0.104 | −0.133 |
| Removed trades | | 112 at −0.273 R vs kept −0.043 R, z −1.83. By index: US100 64 at −0.584 R; US500 21 at **+0.125**; US30 27 at **+0.155** |

Better pooled, but on **1 of 3 indices**: the condition fails. The baseline is identical to the earlier run (the fixes moved no index result).

**Decision: no run on 2021.** The quiet-market effect is a US100 effect (as the stop-size rule was), not a property of the model. 2021 was not touched.

## Hold-out result (2021)
Not run.
