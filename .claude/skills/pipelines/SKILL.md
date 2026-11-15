---
name: pipelines
description: The order in which the ICT engine's improvement skills run for each kind of job — a backtest, a codebase change, a full review, a single trade, a confirmation on unseen data — and the decision rules that turn scores into the next step (do X or Y) without asking. Use at the start of any backtest, sweep, review, "evaluate again", "what next", or engine-change request, and whenever results come back and the next action has to be chosen. It routes to trade-review, pattern-finder, pd-array-audit and change-gate.
---

# Pipelines

One job, one pipeline. Pick the pipeline that matches the request, run its steps in order, and use the decision rules at the bottom to choose what happens after the scores come in. The diagram is `viewer/pipelines.html` (copy in `out/pipelines.html`).

The goal every pipeline serves: **≥ 50% win rate (TP1 before the stop) with positive expectancy, day-only holds**, proven on unseen data.

## A. Backtest pipeline — after any backtest, sweep or simulation

1. **Run** on in-sample data only (2022-01-03 → 2024-06-28), futures cost, ≤ 10 workers. Keep the previous result (`reports/before-<date>/`) so the run can be compared.
2. **Score** each model: trades, win % with its Wilson range, mean R, z, R capped at 10 R, and the change vs the previous run. `uv run python -m ict_engine.eval.review <parquet>` gives the diagnosis and gate value.
3. **Trade-review facts for every trade:** `research/scripts/review_sample.py facts <parquet>` adds the checklist facts (side vs read, range half, sweep before, stop vs pools, pools before TP1, news) to each trade.
4. **Pattern-finder** on those facts, on both R and win rate (`--target win`): which checklist steps and traits separate wins from losses.
5. **Written trade-review on a subset** (`review_sample.py sheets … --n 12`: worst, typical losers, winners), using the trade-review skill. This is where the numbers get a reason.
6. **Array trigger** (rule R4): run pd-array-audit when the problems cluster on one array kind or TF, or when a reviewed trade can't be explained.
7. **Findings** → `research/sweeps/<date>-<name>.md` and a row in `research/review-log.md`. Each recommendation goes to pipeline B.

## B. Code-change pipeline — any recommendation that might touch the code

1. **change-gate** classifies it: no change / measure first / bug fix / option behind a flag / new default.
2. **Witnesses:** pattern-finder, pd-array-audit, trade reviews, the review log + FABLES_FINDINGS, Sharif's saves. A disagreement with evidence stops the change and goes to Sharif.
3. **Test first**, then the change (options keep the current default), then the full suite.
4. **Re-run the affected backtest** (pipeline A, steps 1–2 at least) and report before → after. A bug fix that moves results is reported with the size of the move.
5. **Decision record** in `research/decisions/`.

## C. Full review — "evaluate everything again"

1. **pd-array-audit first**: everything else rests on the arrays.
2. **Pipeline A for each model** (2022 model, MMxM, silver bullet, cameron, the engine plan).
3. **Ledger:** every model / variant / filter marked WORKS (survived unseen data), PROMISING (in-sample only), NO EDGE, CONSISTENT LOSER.
4. **Gap to the goal:** where the best honest variant sits vs 50% win rate with positive R, day-only.
5. **Ranked next actions**, each through pipeline B.

## D. Single trade — Sharif's, ICT's or one engine trade

1. **trade-review.**
2. If the array in the trade is in doubt, or the review can't explain the trade: **pd-array-audit** for that moment.
3. Log it. Every 10 logged reviews: **pattern-finder** on `research/trade-reviews/log.jsonl`.
4. Any "for the engine" idea → pipeline B.

## E. Confirmation — spending unseen data

1. A candidate from rule R1 gets a **pre-registration** (`research/preregistered-<date>-<name>.md`): the exact rule, the data, the pass bar (≥ 30 unseen trades, z ≥ 2.4).
2. **Sharif approves** it. Unseen data is spent once.
3. One run on 2024-07+. Pass → new default through pipeline B. Fail → logged as failed, not re-tuned on that data.

## Decision rules — scores → next step

| # | When the scores show | Do |
|---|---|---|
| R1 | win ≥ 50% and mean R > 0, z ≥ 2, holds capped at 10 R and in both halves | Candidate → pipeline E (pre-register). Don't tune it further in-sample |
| R2 | mean R < 0 with z ≤ −2, or negative in most cuts | Consistent loser. Stop tuning it. One pattern-finder pass for a DO LESS filter that removes the loss; if none holds, park the variant |
| R3 | No edge (\|z\| < 2) | Steps A3–A5. The checklist step that fails most on losers (and that pattern-finder confirms) becomes the next option to test |
| R4 | A pattern-finder DO LESS on an array kind/TF (n ≥ 30), or ≥ 3 of 12 reviewed trades fail step 4 (the array), or the reviewer can't find the engine's array on the chart | pd-array-audit **before** concluding anything about that array |
| R5 | One trade that the review can't explain, or where the engine's array disagrees with the chart | pd-array-audit for that moment; if the array is wrong → pipeline B as a bug fix |
| R6 | Any recommendation to change code | Pipeline B. Never edit the engine straight from a finding |
| R7 | A code change landed | Re-run the affected backtest and compare. No behaviour change intended → results must match; a difference is a bug |
| R8 | Win rate and R disagree (high win %, R ≤ 0 — or low win %, R carried by outliers) | Look at target and stop distance first: TP1 too far/near, stop on liquidity. Test smaller targets / structure stops as options |
| R9 | Day-only R much lower than held R (or the reverse) | Report both. Day-only is the goal; a rule that only works overnight is not a candidate |

## What stops for Sharif

Everything else proceeds without asking.
- Witnesses disagree with evidence on both sides.
- An ICT definition question (what counts as a breaker, an OB, a sweep). ictindex.io first, then him.
- Approving a pre-registration (unseen data is spent once).
- Dropping or parking a whole model.

## Ground rules
- `CLAUDE.md` rules apply.
- In-sample selection only.
- Never edit engine code while a run is in progress.
- Never write to `reports/reviews/`.
- ≤ 10 workers.
- Report outcomes as they are, including "nothing works yet".
