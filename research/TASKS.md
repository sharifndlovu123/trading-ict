# Task list — session of 2026-11-16 (Sharif away; machine off when all done)

Goal: ≥ 50% win rate (TP1 before the stop) with positive R, day-only holds, proven on data never used for selection. Free data only. Every change through the change gate; every result through the pipelines (`.claude/skills/pipelines`).

Status: ☐ open · ◐ running · ☑ done · ✗ dropped

## A. Activity gate (hunt when price is moving)
- ☑ A1 Build `min_activity` as an option, off by default (tests first, suite 506 passed)
- ☑ A2 In-sample variant run (decision-time gate): weak — 2022 model −0.066 → −0.059 R (2 of 3 indices, removed trades −0.16 R, z −0.75); MMxM worse; silver bullet unchanged
- ☑ A3 Decision: the decision-time gate is NOT taken to 2021 (too weak; the clean year is kept)
- ☑ A3b Fill-time mode built (`min_activity_at="fill"`: the order is pulled when the market is quiet at the fill; suite 565 passed)
- ☑ A3c Fill-time gate in-sample (2022 model): −0.066 → −0.033 R pooled, 2 of 3 indices, removed 114 trades at −0.36 R (z −2.7); mostly US100
- ☑ A3d Re-check after the DST fix: pooled −0.066 → −0.044 but only 1 of 3 indices (a US100 effect) — the condition fails
- ✗ A4 2021 run: not run (condition failed); 2021 stays untouched
- ☑ A5 Logged (review log #43); the option stays in the code, off

## B. 30-trade review (15 winners / 15 losers), price focus
- ☑ B1 Fact sheets with the turn point (where price really turned + known levels there)
- ☑ B2 Written reviews, two reviewers × 15 trades (`research/trade-reviews/2026-11-16-30-trades/`)
- ☑ B3 Synthesis: `research/trade-reviews/2026-11-16-30-trades/SUMMARY.md`
- ☑ B4 Level-based tweaks on all 4,656 trades: none lifts mean R (stops beyond array/pool raise win rate to 44–50% at the same R; entry at the HTF array is worse, z −2.0)
- ☑ B5 Nothing qualifies for the change gate (rule R11). Weak lead only: skip when a pool sits within 0.15 ADR beyond the stop (+0.053 vs −0.027 R, z ≈ 1)
- ☑ B6 PD-array flags from the reviewers listed in the review summary and in the session summary (open item for the next array audit)

## C. Microstructure (the layer we had not used)
- ☑ C1 Break the references (`references/orderflow.md`, `references/microstructure/`) into components: measure, formula, data it needs, computable with our data or not
- ☑ C2 Compute each usable component as a fact known at the entry, with tests (bar-based on all 7 datasets; trade-flow based on NQ 2024)
- ☑ C3 Test each component on the backtest trades: does it separate wins from losses, on how many datasets?
- ☑ C4 Verdicts: 26 components, 52 tests, none passes the false-discovery check; volatility and real volume duplicate the activity measure (`research/microstructure/2026-11-16-study.md`)
- ☑ C5 Nothing positive → nothing to the change gate. One lead (flow against the trade in the last 30 min did better) needs Sharif's go-ahead: its test would use the 2024-H2 hold-out
- ☑ C6 DST fix: the activity baseline uses calendar days (test first; suite 570 passed)

## D. Engine fixes queued
- ☑ D1 Index-point thresholds scale by the futures tick outside the indices and gold (`instruments.unit` / `scaled`); futures cost for DXY and EUR/USD; indices untouched by construction
- ☑ D2 Backtests on silver, dollar index, EUR/USD: they trade now; no edge (review log #44)

## E. Wrap-up
- ☑ E1 Summary: `research/SESSION-2026-11-16.md`
- ☑ E2 Suite 570 passed after the last engine change; committed; review log #35–44; memory updated
- ☑ E3 Machine powered off (scheduled after the final commit)

## Done earlier this session
- ☑ Engine-plan confirmation entries, zone stop, results page
- ☑ Fable sweep + FABLES_FINDINGS
- ☑ Skills: trade-review, pattern-finder, pd-array-audit, change-gate, pipelines
- ☑ US100 full sweep; three-index check (stop-size rule failed, 2020–21 hold-out not spent)
- ☑ New datasets: 2020 indices, gold (silver / DXY / EUR/USD blocked by D1); cameron and MMxM-on-gold parked
- ☑ Tweak lab; order-flow facts in trade reviews
