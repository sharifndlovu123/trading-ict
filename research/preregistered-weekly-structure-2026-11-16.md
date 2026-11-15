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

## Amendment 1 (2026-11-16, before any run): the definition, fitted to Sharif's in-sample labels
The rule above (last two 3-week fractal swings) was never run in a test. Checked against Sharif's labels first:
20 bias charts (`reports/reviews/bias.jsonl`) and one W+D timeline per index, Oct 2021 → 2023-09-28
(`reports/reviews/bias-timeline.jsonl`, 243 labelled weeks). It agreed with his timeline on 33% of weeks and flipped
10–21× where he flips once. His answers (2026-11-16) fixed the definition:
- the last change line is the trend; higher highs built below the most recent weekly lower high are shifts, not a change
  ("still a downtrend, buyers' momentum growing"); only breaking that lower high turns it (= ICT: a market structure
  shift is short-term sentiment, a market structure **break** changes the tide; ruling §21);
- a break that only pokes through and then ranges is not the turn (US30 Nov 2022 → range until 17 Jul 2023);
- the protected level is an intermediate-term swing (ICT Core Content Month 12), not every 3-week fractal.

**Final definition (`ict_engine.concepts.context.weekly_structure_state`, tests `tests/test_weekly_structure.py`):**
completed weeks; short-term high = a week with lower highs either side; intermediate-term high (ITH) = a short-term high
with lower short-term highs either side, counted from the week the next short-term high is known (lows mirror). Bear:
the guard is the ITH the latest ITL came from; a weekly close > guard + 0.25 × weekly ATR(14) → bull; price above the
guard without such a close → the guard rises to that high. Bull mirrors. Neutral until the first break.
On his timeline (in-sample) its flips land on his: US500 2023-06-12 (same week), US30 2023-07-17 (the week he named),
US100 2023-05-22 (the close through the Aug-2022 lower high he described); no other flips after the warm-up. The margin
0.25 was chosen among {0, 0.25, 0.5} on these in-sample labels; 0.5 gives the same flips. Nothing OOS was looked at.

**Warm-up:** intermediate swings need ~1–2 years of weeks. Data before 2021-10 is fetched for US100 US500 US30
(Oct 2019 →), and the backtest loader's warm-up is raised from 70 to 800 days (more history before the start only;
the other rules use fixed tails — checked equal on a before/after backtest). Everything else in this pre-registration
(rule, variant, metric, pass bar z ≥ 2.4 paired, ≥ 30 OOS counter-structure trades, last definition on this OOS) stands.

## Amendment 2 (2026-11-16, before any run): wicks vs weak closes; margin 0.1; checked with history from Oct 2019
With the Oct 2019 → Sep 2021 history fetched, amendment 1's rule turned bear 2–4 months late in 2022: a wick through the
protected low with the close back inside moved the guard (US100 Jan 24 2022 wick to 13719, close 14414), and it kept
chasing wicks. Sharif turned bear on the first weekly close below it (US100 2022-02-07). Changed: **only a weak close**
(through the guard, short of the margin) is a range and moves the guard to that week's extreme (US30 Nov 2022: close 64
points above, then a range until 17 Jul 2023); **a wick with the close back inside changes nothing.** Margin chosen on
his 243 in-sample labelled weeks among {0, 0.1, 0.15, 0.25, 0.5} × weekly ATR(14): 87 / 95 / 94 / 93 / 78% agreement →
**0.1** (0.1–0.25 is a plateau). Flips at 0.1 since 2021-06: US100 bear 2022-02-07 (his: same week), bull 2023-05-15
(at the break he described); US500 bear 2022-03-07 (his 2022-04-18), bull 2023-06-12 (same); US30 bear 2022-03-07 (his
2022-02-21), bull 2023-07-17 (the week he named). Nothing OOS was looked at.
Backtest warm-up 70 → 800 days: before/after on 2022-06-01 → 2022-09-30 (both models, US100 + US30, 14.6k rows) differ
only in the first week of the run (bias on 232 rows, 7 trade results) — the old 70 calendar days were < the 60 trading
days `dol` needs. Every later row identical.
