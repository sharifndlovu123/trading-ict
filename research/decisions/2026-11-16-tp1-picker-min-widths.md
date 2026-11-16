# Decision — TP1 picker (J1) and minimum area / gap widths (J3), 2026-11-16

**Source:** trade reviews #47–56 (TP1 skips nearer pools or sits past opposing arrays; sub-point FVGs; stops of 0.02–0.03 ADR).
**Check before building:** the facts already computed on every trade (`reports/recipe-mornings-facts-all.parquet`, 212 recipe trades 2020–26; `reports/trade-facts[-mmxm]-US100-2022-01-03-2024-06-28-futures.parquet`).

| Cut | Recipe, mornings (212) | 2022 model, US100 (573) | MMxM, US100 (221) |
|---|---|---|---|
| Pools before TP1: 0 / 1 / 2 / 3+ | −0.003 / −0.072 / +0.287 / +0.285 R | −0.061 / −0.199 / −0.237 / −0.033 | −0.039 / +0.260 / +0.051 / −0.394 |
| TP1 just past a pool: no / yes | +0.017 / +0.304 | −0.061 / −0.199 | −0.041 / +0.034 |
| Trigger gap size, quartiles small → large | +0.012 / −0.005 / +0.259 / +0.223 | −0.191 / −0.123 / −0.283 / +0.294 | +0.102 / +0.207 / −0.022 / −0.302 |
| Risk / ADR, quartiles small → large | +0.164 / −0.164 / +0.301 / +0.189 | −0.390 / −0.203 / −0.006 / +0.315 | +0.484 / −0.077 / −0.300 / −0.138 |

**Reading:** no cut points the same way on the three models. The 2022 model's size effect is the US100-only effect that failed the three-index check (review log #38–39); MMxM points the other way. Passing nearer pools is not worse for the recipe (it is better).

**Decision: not built.** The reviewers' flags are true of single trades and stay as review flags (the fact sheet already prints pools before TP1, the trigger gap and risk in ADR). No option is added, because nothing here would pass the change gate.
