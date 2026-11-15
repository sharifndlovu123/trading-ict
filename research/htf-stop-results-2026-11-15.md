# Results: a stop on the timeframe of the draw (run 2026-11-15)

Pre-registration: `preregistered-htf-stop-2026-11-15.md` (4525996); build c8ca37f. Futures basis, 5 assets,
2022-01-03 → 2024-06-28, OOS from 2023-09-29, runner R in units of the **new** risk. Log: `reports/sweep-htf-stop-2026-11-15.log`.

| model | variant | IS n | IS win | IS exp R | OOS n | OOS win | OOS exp R ± se | Δ OOS | z |
|---|---|---|---|---|---|---|---|---|---|
| 2022 model | baseline | 953 | 34% | −0.023 | 304 | 36% | +0.023 ± 0.099 | – | – |
| 2022 model | stop: 15m swing + daily draw | 944 | 52% | −0.012 | 302 | 52% | −0.071 ± 0.059 | −0.095 | −0.8 |
| 2022 model | stop: 1h swing + daily draw | 931 | 59% | +0.013 | 299 | 59% | −0.049 ± 0.052 | −0.072 | −0.6 |
| MMxM | baseline | 649 | 27% | −0.060 | 237 | 29% | −0.077 ± 0.086 | – | – |
| MMxM | stop: 15m swing + daily draw | 632 | 36% | −0.006 | 232 | 42% | +0.009 ± 0.073 | +0.086 | +0.8 |
| MMxM | stop: 1h swing + daily draw | 620 | 40% | −0.005 | 229 | 47% | +0.012 ± 0.063 | +0.090 | +0.8 |

**Verdict: 0 of 4 pass.** The wider stops raise the win rate a lot (2022 model 36% → 52–59%; MMxM 29% → 42–47%).
They also lower the variance (se roughly halves). But because TP1 keeps its price, each win is worth fewer R, and
expectancy per unit risked barely moves. MMxM leans positive (+0.09 R, z 0.8, both timeframes, IS and OOS the same
sign); the 2022 model leans negative. Neither is evidence.

Reading: the wider stop is a trade-off, not an edge. Win rate and payoff trade against each other almost exactly.
For MMxM, whose own stop already sits at the reversal low, the structural stop is the more natural fit. It is worth
keeping as a review question for that model only, not as a default.
