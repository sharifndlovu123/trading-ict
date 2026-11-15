# Pre-registered: counter-trend = small grabs, weekly trend = weekly structure (written 2026-11-16, before any code or run)

Follows `research/reentry-v2-results-2026-11-16.md` (H2 failed with `htf40` = close vs the 40-day 50%, which is a
premium/discount reading, not a trend). Sharif, 2026-11-16: "the weekly structure should be lower lows and lower highs etc."

**Honesty note:** this is the second definition of "weekly trend" tried on the same OOS period (2023-09-29 → 2024-06-28).
It is defined by Sharif's words, not chosen from results, and it is the only new definition tried; the pass bar stays
z ≥ 2.4. If this fails, no third definition is tried on this OOS.

## Definition: bias rule `weekly_structure` (completed weeks only)
- Weekly bars = completed trading days grouped by week (Monday); the current, unfinished week is dropped.
- Swing high = a week whose high is above the previous and the next week's highs; swing low likewise with lows. A swing
  exists only once the next week has closed.
- Last two swing highs and last two swing lows: both lower → **bear**; both higher → **bull**; anything else (mixed,
  equal, fewer than two of either) → **neutral**.

## Rule (unchanged from H2 except the trend source)
`counter_tp1="all"` with `weekly_rule="weekly_structure"`: a long when the weekly structure is bear, or a short when it
is bull, closes its whole position at TP1 (small grab). Neutral weeks: nothing changes.

## Test
2022 model and MMxM; US100 US500 US30; futures; runner R; 2022-01-03 → 2024-06-28; OOS from 2023-09-29.
Variant: "small grab: against the weekly structure". Paired per trade vs baseline (same asset, decision time, side).
**Pass (per model) = OOS paired mean Δ > 0, z ≥ 2.4, ≥ 30 OOS counter-structure trades.** Trades with the structure or
in neutral weeks must be unchanged (checked). Reported beside it: baseline expectancy with / against / neutral structure,
IS and OOS (descriptive). A pass becomes a forward-v2 candidate; 2024-07+ stays unseen.
