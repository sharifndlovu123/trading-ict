# Pre-registration — the morning recipe with a stop buffer on 2024-07 → 2026-11

Written 2026-11-16. Nothing below had been run on any date after 2024-06-28 for this model with these settings when this was written. **Approved by Sharif on 2026-11-16: "yes proceed, that will help confirm if it works well".** He also accepts that it is an index rule: "what we have works best for the indices … that's okay, it's always better to have different approaches for specific groupings of assets as they move differently."

## The rule (fixed)
PD-array-return model, variant `recipe4b: mornings only, stop + 0.10 ADR, target kept` in `ict_engine/eval/variants.py`:
- the area: a 1h or 4h FVG formed in the last 5 days, read from its formation (`area_history="formation"`), reached to its 50% for the first time;
- the trigger: a 15m FVG in the area's direction completing within 4 hours; entry: limit at that gap's near edge;
- no daily bias; side not against both the 1h and 4h structure; entry within 0.25 ADR of the area;
- **window `ny_am_kz` only (08:30–11:00 New York)**;
- **stop 0.10 × the 20-day ADR beyond the reaction extreme; TP1 = the nearest untaken liquidity at least 1 R of the unbuffered risk away** (`stop_buffer_adr=0.10`, `buffer_keeps_target=True`), 50% off at TP1, runner at breakeven, flat at the session close.

## What was seen (selection data: three indices, 2020-01-02 → 2024-06-28)
| | 2020–21 | 2022–24 | Both |
|---|---|---|---|
| recipe4b | 47.1% win, +0.138 R (70) | 53.7%, +0.281 R (67) | **50.4% win [42–59], +0.208 R, z 2.39 (137)**; US100 +0.20, US30 +0.15, US500 +0.29; +0.132 R without the 5 best |
| same with a 0.05 buffer | 44.3%, +0.202 (70) | 47.8%, +0.232 (67) | 46.0%, +0.217, z 2.22 |
| mornings only, no buffer | 36.4%, +0.183 (66) | 41.8%, +0.270 (67) | 39.1%, +0.227, z 1.92 |
| the model's baseline | −0.057 (2,040) | −0.012 (2,790) | 27.9%, −0.031 |
The morning window and the buffer were chosen after the hold-out review of 2020–21 (`research/trade-reviews/2026-11-16-recipe3-holdout/SUMMARY.md`), so both periods are selection data for this variant and its numbers are optimistic. The recipe failed on gold, silver, the dollar index and EUR/USD (review log #48): this is a US-index, New York-morning rule.

## The clean data
**2024-07-01 → 2026-11-13, US100 / US500 / US30**, Dukascopy CFD 1m, futures cost. This period has been used many times for the other models' forward runs and for the model's baseline, never for the recipe or any of its gates. Expected size: about 30 trades a year, so roughly 70.

## Outcomes (decided now)
Primary measures: win rate (TP1 before the stop) and mean `r`, pooled.
| Outcome | Condition | What follows |
|---|---|---|
| **Confirmed** | ≥ 50 trades, mean R > 0 with one-sided z ≥ 2.0, win rate ≥ 45%, positive on at least 2 of 3 indices | The recipe becomes a model of its own in the registry (the engine's first with out-of-sample support) and goes to the live forward log |
| **Consistent** | ≥ 50 trades, mean R > 0 and positive on at least 2 of 3 indices, but z < 2.0 or win rate < 45% | Lead candidate; forward log only; no claim |
| **Fail** | mean R ≤ 0, or negative on 2 of 3 indices | Logged as failed; the 50% result was fitted |
The z bar is 2.0, not the project's usual 2.4: with ~70 trades a true edge of +0.2 R gives an expected z of about 1.4, so even 2.0 is demanding; the win-rate bar is added because the goal is a win rate.

Reported beside it: the 0.05-buffer and no-buffer variants; results when the entry must trade more than 2 and more than 4 ticks through; without the 5 best trades; per year; counted as ideas (same day and side once).

## After the run
A written review of every trade (Sharif: more than 60 is welcome), as for every run.

## Result — run once, 2026-11-16, code at 50e5694 (`reports/variants-pd_return-2024-07-01-2026-11-13-recipe4b-confirm.*`)

| | n | Win % [95%] | Mean R | z | US100 / US30 / US500 | 2024 / 2025 / 2026 |
|---|---|---|---|---|---|---|
| Model baseline | 2,882 | 27.1 [26–29] | −0.044 | −1.32 | −0.011 / −0.132 / +0.005 | −0.001 / −0.073 / −0.033 |
| mornings only, no buffer | 79 | 29.1 [20–40] | −0.053 | −0.36 | +0.049 / +0.029 / −0.169 | −0.225 / +0.057 / −0.078 |
| stop + 0.05 ADR, target kept | 81 | 32.1 [23–43] | −0.121 | −1.00 | −0.034 / −0.005 / −0.241 | −0.160 / −0.066 / −0.153 |
| **recipe4b (the rule): stop + 0.10 ADR, target kept** | **81** | **33.3 [24–44]** | **−0.174** | **−1.63** | −0.121 (23) / +0.010 (21) / −0.311 (37) | −0.099 (17) / −0.169 (31) / −0.217 (33) |

**Outcome: FAIL** (mean R ≤ 0; negative on two of three indices; every year negative; win rate 33%, not 45%).

Beside it: without the 5 best trades −0.292 R; counted as ideas (same day and side once) 70 ideas, −0.167 R; the entry trading more than 2 or 4 ticks through changes nothing (−0.174 / −0.173); longs −0.16 (45), shorts −0.20 (36); by decision hour: 08h −0.16 (25), 09h −0.28 (41), 10h +0.10 (15); exits 40 stops, 27 TP1, 14 time exits.

**Reading:** the 50.4% / +0.21 R on 2020-01 → 2024-06 was fitted. The two additions chosen after the hold-out review (mornings only, the stop buffer) did not carry forward: the buffered version is the worst of the three on the clean period, and the plain morning recipe is about −0.05 R, the same as the unfiltered model. Putting every period together, the plain morning recipe has 212 trades at about +0.12 R: indistinguishable from zero. The recipe as coded is not an edge.

No re-tuning on 2024-07 → 2026-11. Every trade of this run gets a written review (what was different from 2020–24), as for every run.
