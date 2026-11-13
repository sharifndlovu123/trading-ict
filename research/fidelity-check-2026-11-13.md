# Fidelity check: does the engine take ICT's own trades? (2026-11-13)

Reference: the 14 live executions in `tests/cases/ict_live_exec.yaml`, scored with `python -m ict_engine.eval.report
--model <m>`. Similarity ≥ 0.80 = match, ≥ 0.60 = similar. These are winning trades ICT chose to show, so this tests
whether the engine **finds** his trades, not its win rate.

## Results
- **The engine trades 0 of 14 in every model and variant**, including the 2022 model with no bias gate.
- **It does detect them:**
  - 2022 model: 10 of 14 at "similar" or better, with near-exact matches at 0.96 (2023-12-11 NQ), 0.95
    (2023-11-28 ES Silver Bullet), 0.86 (2023-12-01 ES) and 0.80 (2024-01-09 NQ).
  - MMxM: sees both of its MMBM cases. Silver Bullet: sees its one case.
- **Half of ICT's trades belong to a model we haven't built.** The 14 cases are labelled: 7 PD array return,
  4 2022 model, 2 MMBM, 1 Silver Bullet, 1 macro.
- **What blocks the matches.** Defaults: bias gate first. With bias off:
  - **risk/cost gate** (≥ 4 cases);
  - **POI gate**, "no HTF POI under the sweep" (most cases);
  - target, cap and time (a few).

| ICT trade | Stop on our feed | CFD spread | Cost | Futures (≈1 tick + fee) |
|---|---|---|---|---|
| 2023-12-11 NQ, premarket | 8.15 pt | 3.45 pt | 0.42R | ≈0.06R |
| 2024-01-09 NQ, 10:50 macro | 13.3 pt | 1.47 pt | 0.11R | ≈0.04R |
| 2023-11-28 ES, SB | 3.74 pt | 0.52 pt | 0.14R | ≈0.09R |

## Reading
1. **Instrument mismatch.** ICT trades futures (NQ, ES) with tight stops. Dukascopy CFD spreads cost several
   times a futures tick, so the cost gate (max 0.1R) removes exactly his kind of trade, and the trades that
   remain are the wider-stop, lower-quality ones.
2. **Same trades, futures costs (rough re-cost):** cost falls from ≈0.065R to ≈0.03R per trade. That is still
   not enough: unseen period −0.03 (2022 model), −0.07 (Cameron), −0.02 (MMxM), −0.10 (SB).
   But a futures cost model would let a **different set** of trades through the cost gate, so a fair test needs
   a re-run.
3. **The POI gate is the next fidelity question.** It blocks ICT's 0.95 and 0.80 matches. Our "HTF POI under the
   sweep" rule may be stricter than how ICT picks his array.
4. **The biggest coverage gap is the PD array return model:** half of ICT's examples.

## Next
- Decide the cost basis (which instrument is actually traded) → re-run under that cost model, with 2022–24
  only for any choices.
- Audit the POI rule against the 4 near-exact cases.
- Build the PD array return model (references/models.md).

## POI audit (read-only, while the futures run was going)
- The POI gate's "blocks" of ICT's 0.95 (11-28 ES) and 0.80 (01-09 NQ) matches are **not 2022-model errors**.
  Those trades are labelled Silver Bullet, macro and PD array return, and those models don't require an HTF POI.
  The 2022 model rejecting them is correct. POI is not the main fidelity gap.
- **ICT's own 2022-model trades use very tight stops:** NQ 11-24 at 1.25 pt; ES 01-05 at 2.5 pt (wick CE);
  ES 01-10 at 1.5 pt.
  - Even on futures costs (NQ ≈ 0.47 pt, ES ≈ 0.34 pt per round trip) that is 0.2–0.4R, so our gate
    (`max_cost_r` = 0.1 of **risk**) would still reject them.
  - ICT accepts the cost because his targets are many R away.
- Candidate fixes (to test on 2022–24 only, after the futures run):
  1. **Cost gate relative to the reward:** cost ≤ 10% of the distance to TP1, instead of 10% of risk.
  2. **Stop variant:** stop at the CE of the sweep wick or of the FVG (ICT's placement), instead of beyond the
     swept extreme.
