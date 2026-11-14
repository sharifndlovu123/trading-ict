# Results: the turn that adds liquidity — near-equal hold (2 bp) (run 2026-11-15)

Pre-registration: `preregistered-liquidity-hold-2026-11-15.md` (88a3087, with an amendment made during the build and
before any run); build d31df0d. Futures basis; US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28; OOS from
2023-09-29. Scorer: `research/scripts/day_delta_eval.py --tag liquidity-hold` → `reports/liquidity-hold-results.md`.

| model | variant | sample | changed days | mean ΔR/day ± se | z | admitted n | win | exp R | displaced |
|---|---|---|---|---|---|---|---|---|---|
| 2022 model | trigger/POI: hold within 2 bp | IS | 7 | +1.48 ± 1.04 | +1.4 | 7 | 57% | +1.33 | 1 (−1.05) |
| 2022 model | trigger/POI: hold within 2 bp | OOS | 5 | +1.31 ± 0.48 | +2.8 | 5 | 100% | +1.31 | 0 |
| MMxM | purge: hold within 2 bp | IS | 1 | −1.01 | – | 1 | 0% | −1.01 | 0 |
| MMxM | purge: hold within 2 bp | OOS | 1 | −1.02 | – | 1 | 0% | −1.02 | 0 |

**Verdict: 0 of 2 pass.** Both cells fail the ≥ 30 changed-days rule: the rule is too rare to judge. The 2022 model's OOS
z of 2.8 comes from 5 trades, so it does not count. In 2½ years on 5 assets the hold changed only 12 days for the 2022
model (12 admitted trades, 9 won, +1.3 R each IS and OOS) and 2 for MMxM (both lost).

Reading:
- The direction is encouraging, and IS and OOS agree (+1.3 R per admitted trade, n = 12 in total). With a 2 bp
  tolerance against context levels only, though, the pattern is almost never the binding constraint. Most turns
  that "add liquidity" still sweep a trivial 1m swing (the trigger passes) and then fail on the POI, the bias or the
  time window, not on the missing sweep.
- Widening the tolerance or adding 1h/4h swing levels would make the rule fire more often. That would be a new
  pre-registration. Picking a tolerance after seeing this result is exactly the forking path the protocol forbids,
  so any re-test needs its own OOS budget, i.e. the forward test, not 2023-09-29+.
- Option: record the 12 trades as a **tracked pattern** (`hold` tag) in the forward test, and let them accumulate
  there rather than re-mining history.
