# Pre-registered: re-entry v2 (no chase) + counter-trend = small grabs (written 2026-11-16, before any code or run)

Models: the 2022 model and MMxM. Assets: **US100 US500 US30 only** (Sharif 2026-11-16: "focus on US500, US100 and US30 —
avoid others"). Futures basis. 2022-01-03 → 2024-06-28, the variants tool's 70/30 split (OOS from 2023-09-29).
Metric: runner R (`runner_r`). 2024-07+ stays unseen.

## Sources
- Re-entry review (2026-11-16, 23 in-sample re-entries, `reports/reviews/reentry.jsonl`; outcomes were visible —
  hindsight, so these set what to test, not evidence): re-entries he would take (10) averaged +1.29 R on the engine,
  the ones he'd skip or call wrong side (12) −0.75 R. Reasons in his notes: **too late / chasing** ("short was missed,
  consider halting", "very late sell", "saw this trade too late"), **against the higher timeframe** (all 3 wrong-side
  calls), chop, no displacement in the POI.
- Sharif, 2026-11-16: "there's nothing wrong with buying in a weekly bearish bias, but you can't expect distanced areas to
  be reached — if so we are looking for small grabs." → the weekly trend sets the **target**, not permission.

## Definitions (bars before the decision only)
- **Weekly trend** = new bias rule `htf40`: the last completed daily close above the equilibrium (50%) of the last 40
  completed days (≈ 8 weeks) → bull, else bear. Same construction as the existing `htf20` (20 days), on the weekly scale.
  Read from the day context (completed days only).
- **Against the weekly** = a long when `htf40` is bear, a short when it is bull.
- **Small grab** = the whole position closes at TP1 (`partial_frac = 1.0`: no runner). TP1 is the model's existing
  earliest-close target (nearest liquidity); nothing else changes.
- **No chase** (re-entries only) = the re-entry's planned entry is at the same or a better price than the stopped first
  trade's entry (a short at ≥ the first entry, a long at ≤). Otherwise the re-entry is not taken.

## Params (`sim.run.run_day`)
- `counter_tp1`: `None` | `"reentry"` (only re-entries against the weekly take the small grab) | `"all"` (every trade
  against the weekly takes the small grab).
- `reentry_nochase`: bool.
Every setup records `weekly_trend` and `tp1_only` so the trades can be scored on their own.

## Variants (per model; plus the baseline and the plain `after_stop` re-entry from the first test, rerun on 3 assets)
| name | reentry | reentry_nochase | counter_tp1 |
|---|---|---|---|
| re-entry v2: no chase + counter-trend small grab | after_stop | True | reentry |
| re-entry: no chase | after_stop | True | – |
| re-entry: counter-trend small grab | after_stop | – | reentry |
| counter-trend small grab (all trades) | – | – | all |

## H1 — re-entry v2 (primary for re-entries)
Scored on the added trades (`reentry` = True) of "re-entry v2".
**Honest limit, stated before the run:** the plain re-entry had only 31 OOS added trades on these three indices
(2022 model 27, MMxM 4), so after any filter v2 **cannot reach the ≥ 30 OOS bar**. Therefore v2 cannot pass here.
The best possible verdict is **"candidate"** = (both models pooled) IS mean > 0 **and** OOS mean > 0 **and** OOS mean ≥
the plain `after_stop` added trades' OOS mean. A candidate goes to the 2024-07+ confirmation list only with Sharif's
go-ahead (that check is one-shot). Anything else = fail. The two single-condition variants are reported beside it.

## H2 — counter-trend = small grabs, every trade (primary, testable)
The change only touches trades against the weekly; it is scored **paired**: for each such trade, Δ = runner R with the
small grab − runner R with the default runner (same fill, same TP1). Trades with the weekly are identical by construction
(checked, reported).
**Pass (per model) = OOS paired mean Δ > 0 with z = mean / se ≥ 2.4 over ≥ 30 OOS counter-trend trades.** The whole-book
OOS Δ vs baseline from the variants tool is reported beside it. A pass becomes a forward-v2 candidate.
Also reported (descriptive): with-weekly vs against-weekly baseline expectancy, IS and OOS.
