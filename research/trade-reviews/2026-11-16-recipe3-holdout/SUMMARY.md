# All 77 hold-out trades reviewed (2020–2021) — and the leads checked on both periods

The run: `recipe3` on the PD-array-return model (Sharif's entry recipe; `research/preregistered-recipe2-2020-2021.md`), three indices, 2020-01-02 → 2021-12-31: 77 trades, 32.5% win, +0.121 R, outcome "consistent". Sharif: "if you want to check against more than 60 trades for reviewing feel welcome" — every trade was reviewed, five reviewers, one file a trade in this folder; fact sheets in `../sheets/2026-11-16-recipe3-holdout/`.

## What the reviewers found (five batches, independently)
**No look-ahead on any of the 77.** On every trade the 15m gap's third candle was closed at the decision, the fill came later, and the stop and TP1 levels were printed before the decision.

**Does it look like his recipe?** Of the 77: about a quarter fully, half partly, a quarter not. The "not" trades have an area that is not an area (under a point wide, or its far edge already wicked through), a trigger gap of one or two ticks, or an entry far from the area.

**Repeated in several batches**
| Lead | Batches | 
|---|---|
| The stop sits exactly on the reaction extreme with no buffer: run by 0.02–0.1 ADR, then price turns (TP1 the same day on about 10 trades) | 3, 4, 5 (and 2) |
| Afternoon setups (decided 13:30–14:00) lose | 2 |
| Entry further than ~0.12–0.15 ADR from the area loses | 2, 3, 4 |
| A real 15m displacement separates winners from losers | 1, 5 (not 2, 3) |
| Fills on a touch: winners whose entry traded only 2–3 ticks through | 1, 2, 4, 5 |
| The daily structure separates nothing | all five |

**Where price turned:** winners 0.01–0.25 ADR past the entry, inside the stop, at the 15m gap, the area's 50% or the area's edge. Losers: about a third turned just beyond the stop at a level known at the entry (the area's far edge, a session high or low, PDH/PDL, a 1h/4h swing); the rest were simply wrong and never came back that day.

## The leads on all 163 recipe trades, each period on its own (`reports/recipe3-all-2026-11-16.parquet`)
A lead counts only if the hold-out (2020–21) and the in-sample period (2022–24) agree.
| Lead | 2020–21 | 2022–24 | Verdict |
|---|---|---|---|
| Decided before 12:00 vs after | +0.183 (66) vs −0.251 (11) | +0.270 (67) vs +0.073 (19) | **Agree: mornings** |
| Stop + 0.10 ADR beyond the extreme, TP1 price kept | win 32.5 → 42.9%, R +0.12 → +0.12 | win 39.5 → 48.8%, R +0.23 → +0.23 | **Agree: about 10 points more wins at the same R** |
| Entry ≤ 0.15 ADR from the area vs further | +0.165 vs −0.062 | +0.181 vs +0.351 | Disagree |
| Displacement body ≥ 2× the mean vs smaller | −0.214 (10) vs +0.171 | +0.145 (10) vs +0.237 | No (and few trades) |
| Trigger gap ≥ 0.02 ADR vs smaller | +0.303 vs −0.217 | +0.215 vs +0.245 | One period only |
| Area ≥ 0.2 ADR wide vs narrower | +0.117 vs +0.124 | +0.251 vs +0.215 | No |
| Entry must trade > 2 ticks through | +0.082 (75) | +0.226 (86) | Barely changes it |
| Entry must trade > 4 ticks through | −0.040 (71; 6 winners out) | +0.196 (83) | The hold-out depends on six touch-filled winners |
| Counted as ideas (same day and side once) | +0.104 (66) | +0.252 (80) | Same picture |

**Both leads together, same trades replayed** (mornings only, stop + 0.10 ADR): 2020–21 48.5% win, +0.187 R (66); 2022–24 55.2%, +0.294 R (67); both 133 trades, **51.9% win [43–60], +0.241 R, z 2.7**; US100 +0.24, US30 +0.15, US500 +0.40. Chosen after looking at both periods, so this is optimistic and 2020–21 is no longer clean for it.

## Problems found outside the recipe
- **The news calendar starts on 2021-01-07**, so every 2020 fact sheet's "news: none" is a blank, not a fact. Several 2020 trades triggered on what look like release days.
- **Holidays:** two trades on Thanksgiving 2021 (the feed stops at 12:58; the exit was booked on the 18:00 reopen).
- **Flat time:** the engine closes at 16:00; the fact sheets replay to 16:55.
- **Resting limits are never cancelled:** five fills came after price had already run 1.2–2.3 R.
- **"Fresh" still lets through an area whose far edge was wicked** but not closed through (five trades, no winner among them).
- **TP1 skips nearer pools** on some trades (5–8 R targets with a pool at 1.2–1.5 R).
- **Fact sheet:** the 2-day "turn" line is a different swing on about a third of the trades; a 4h state was read from a candle closing a minute after the decision on one sheet.

## Next
`recipe4` = recipe3, mornings only (`ny_am_kz`), `stop_buffer_adr=0.10` (new option, off by default) as a real backtest on both periods, then a clean confirmation: the recipe has never been run on 2024-07 onward.
