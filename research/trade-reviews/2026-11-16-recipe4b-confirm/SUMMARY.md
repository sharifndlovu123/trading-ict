# All 81 trades of the failed confirmation reviewed (2024-07 → 2026-11) — why it failed, with the market conditions

The run: `recipe4b` (Sharif's entry recipe, New York morning, stop 0.10 ADR beyond the reaction extreme, target kept) on the three indices: 81 trades, 33.3% win, −0.174 R: FAIL (`research/preregistered-recipe4b-2024H2-2026.md`). Five reviewers, one file a trade in this folder; each had the day's market conditions (`../sheets/recipe4b-confirm-conditions.csv`).

## What the reviewers found
**No look-ahead on any of the 81.** Every 15m gap was closed at the decision; stops and areas re-derive from the 1m bars.

**Why the trades lost** (about 49 losers, tallied over the five batches)
| Reason | Trades |
|---|---|
| Wrong side for the whole day: a long bought at 0.87–0.98 of the range in a bull grind, or a short against the weekly and daily near the highs | ≈ 16 |
| Stop run, then reversal (the 0.10 ADR buffer was run by another 0.03–0.27 ADR, at PDH/PDL, an opening gap, a 1h FVG) | ≈ 11 |
| Target too far for the day, behind an opposing array, or at a pool already taken; nearer pools skipped | ≈ 10 |
| Area ground through with no real displacement (trigger gaps of 1–3 points before the open) | ≈ 8 |
| News spike read as displacement (a CPI candle, Powell at Jackson Hole) | ≈ 4 |
| Holiday session (Juneteenth) | 1 |

**What was different from 2020–21**
- The winners look the same in both periods: price turned 0.00–0.2 ADR past the entry, at the 15m gap or the area's edge.
- The losers changed. In 2020–21 about a third were stop runs before the move; here most were **wrong for the whole day**, in a calm bull market where a small 15m gap against the drift means nothing.
- **The buffer hurt the payoff:** it widened the stop while the target stayed, so TP1 was worth 0.4–0.9 R on most trades (average win ≈ +0.84 R against −0.92 R a loss). It was fitted to 2020–24, where stops were run by a hair; in 2024–26 they were run by more.
- Fit to the recipe: about 11 trades fully, 44 partly, 19 not (areas a point or two wide, tick-size gaps).

## Market conditions of the 81 trades
| Known that morning | Trades | Win % | Mean R |
|---|---|---|---|
| High-impact news day | 21 | 33 | **+0.263** |
| No news day | 60 | 33 | −0.327 |
| High volatility | 22 | 32 | +0.031 |
| Normal volatility | 49 | 37 | −0.192 |
| Low volatility | 10 | 20 | −0.533 |
| Backdrop bull | 54 | 32 | −0.239 |
| Backdrop mixed / bear | 27 | 37 | −0.044 |
By batch this varies a lot (in the last batch news and high volatility did not help), so it is a tendency over many trades, not a rule for each day. The calendar also misses releases that moved these trades (Jackson Hole, the 10:00 ISM and consumer-confidence releases, some jobless claims), so "no news" is overstated.

## Leads checked on all 212 morning-recipe trades, each of the three periods on its own (`reports/recipe-mornings-facts-all.parquet`)
| Lead | 2020–21 | 2022–24 | 2024–26 | Verdict |
|---|---|---|---|---|
| Entry in the right half of the range (short in premium, long in discount) vs the wrong half | +0.289 vs +0.089 | +0.314 vs +0.245 | +0.076 vs −0.106 | **Same sign in all three** (78 trades right half: 41% win, +0.234 R; wrong half 134: 32%, +0.058) |
| Not Monday vs Monday | +0.239 vs −0.027 | +0.335 vs −0.001 | +0.058 vs −0.489 | **Same sign in all three** (Mondays: 43 trades, 26% win, −0.19 R) |
| News day vs not (2021 on; see the conditions study) | positive every year 2021–2026 | | | **Same sign in six of six years** |
| Liquidity taken against the trade first vs not | +0.258 vs +0.081 | +0.349 vs +0.193 | −0.057 vs −0.050 | Two of three |
| Trigger gap ≥ 0.02 ADR vs smaller | +0.39 vs −0.23 | +0.24 vs +0.33 | +0.05 vs −0.23 | Two of three |
| Decided before 09:30 vs after | +0.07 vs +0.29 | +0.39 vs +0.12 | −0.13 vs +0.05 | No |
| Side matches the weekly/daily read | −0.00 vs +0.38 | +0.33 vs +0.21 | −0.14 vs +0.05 | No |
| Last hour busy vs normal | +0.20 vs +0.24 | +0.43 vs +0.15 | −0.27 vs −0.02 | No |

Three things agree in every period: **trade from the right half of the range, skip Mondays, and prefer news days** (with high volatility). All three are in his own framework (premium/discount; time; displacement). They were found after the fact on every recipe trade, so no clean index data is left to test them on: they belong in the forward log.

## Problems found outside the recipe (to fix)
- **News calendar:** nothing before 2021-01-07; Jackson Hole and other Fed speeches, the 10:00 ISM and consumer-confidence releases and some claims dates are missing; JOLTS is tagged medium.
- **No holiday calendar:** trades on Juneteenth and the session after Memorial Day; the exit is booked on the 18:00 reopen.
- **Targets:** TP1 skips nearer qualifying pools (5–10 R targets), sits behind opposing arrays, or at a pool already taken by a fraction of a point.
- **Resting limits are never cancelled:** fills after a 0.4–1.65 R run on about ten trades.
- **Tiny areas and gaps pass every gate:** areas 0.2–5 points wide, trigger gaps of one to three ticks.
- **One event, several trades:** the same move on two or three indices is counted separately (81 trades ≈ 70 ideas).
- **Result column:** `r` books the whole position at TP1 (the vote measure); with partials the wins are smaller (`runner_r`). Both are reported; the review sheets use partials.
- **Fact sheet:** the 2-day "turn" line is another swing on roughly a third of the trades.
