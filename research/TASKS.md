# Task list — session of 2026-11-16 (Sharif away; machine off when all done)

Goal: ≥ 50% win rate (TP1 before the stop) with positive R, day-only holds, proven on data never used for selection. Free data only. Every change through the change gate; every result through the pipelines (`.claude/skills/pipelines`).

Status: ☐ open · ◐ running · ☑ done · ✗ dropped

## A. Activity gate (hunt when price is moving)
- ☑ A1 Build `min_activity` as an option, off by default (tests first, suite 506 passed)
- ☑ A2 In-sample variant run (decision-time gate): weak — 2022 model −0.066 → −0.059 R (2 of 3 indices, removed trades −0.16 R, z −0.75); MMxM worse; silver bullet unchanged
- ☑ A3 Decision: the decision-time gate is NOT taken to 2021 (too weak; the clean year is kept)
- ☑ A3b Fill-time mode built (`min_activity_at="fill"`: the order is pulled when the market is quiet at the fill; suite 565 passed)
- ◐ A3c In-sample run of the fill-time gate, 2022 model, three indices
- ☐ A4 If A3c holds (pooled and ≥ 2 of 3 indices, removed trades clearly worse): one run on 2021 (approved by Sharif); else stop here
- ☐ A5 Pass → new default through the change gate; fail / not confirmed → logged, option stays off

## B. 30-trade review (15 winners / 15 losers), price focus
- ☑ B1 Fact sheets with the turn point (where price really turned + known levels there)
- ☑ B2 Written reviews, two reviewers × 15 trades (`research/trade-reviews/2026-11-16-30-trades/`)
- ☐ B3 Synthesis: pricing mistakes that repeat, levels we should have priced
- ◐ B4 Level-based tweaks from the reviews (`tweak_levels.py`): stop beyond array / pool, TP1 front-run, entry at the HTF array, skip gates — running on all 4,656 trades
- ☐ B5 Tweaks that fix many more trades than they break and lift R on most datasets → change gate (option → backtest)

## C. Microstructure (the layer we had not used)
- ◐ C1 Break the references (`references/orderflow.md`, `references/microstructure/`) into components: measure, formula, data it needs, computable with our data or not
- ◐ C2 Compute each usable component as a fact known at the entry, with tests (bar-based on all 7 datasets; trade-flow based on NQ 2024)
- ◐ C3 Test each component on the backtest trades: does it separate wins from losses, on how many datasets?
- ☐ C4 Verdict per component: usable and positive / usable, no value / not usable with free data; write-up + review-log row
- ☐ C5 Positive components → change gate as options (and a pre-registration where a clean period exists)

## D. Engine fixes queued
- ☐ D1 Thresholds in index points: make silver, the dollar index and EUR/USD tradable; index results must not move (R7)
- ☐ D2 Backtest the newly tradable assets through pipeline A (scores, time/activity, tweak lab)

## E. Wrap-up
- ☐ E1 One summary document for Sharif: what was done, what holds, what failed, what needs his decision
- ☐ E2 Full test suite passes; everything committed; review-log and memory updated
- ☐ E3 Power the machine off

## Done earlier this session
- ☑ Engine-plan confirmation entries, zone stop, results page
- ☑ Fable sweep + FABLES_FINDINGS
- ☑ Skills: trade-review, pattern-finder, pd-array-audit, change-gate, pipelines
- ☑ US100 full sweep; three-index check (stop-size rule failed, 2020–21 hold-out not spent)
- ☑ New datasets: 2020 indices, gold (silver / DXY / EUR/USD blocked by D1); cameron and MMxM-on-gold parked
- ☑ Tweak lab; order-flow facts in trade reviews
