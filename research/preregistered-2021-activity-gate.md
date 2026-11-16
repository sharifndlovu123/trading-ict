# Pre-registration — activity gate (`min_activity` 0.6) on 2021 (never tested)

Written 2026-11-16 before any run on 2021. Sharif approved the run on 2026-11-16 ("Proceed"), on the condition stated to him: only if the gate holds on the data already used.

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

## In-sample variant run (2022-01-03 → 2024-06-28)
_(appended when the run finishes)_

## Hold-out result (2021)
_(appended after the single run)_
