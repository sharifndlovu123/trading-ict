# Cost realism check: CME NQ 2024, futures basis

Run once on the five models' 2024 CME NQ trades (`reports/nqcme`, futures costs: 1 tick + $4.50 = 0.475 pt round trip, every fill at the exact price). Script: `research/scripts/cost_check.py`; rows: `reports/nqcme/cost-check.parquet`.

## A. Quoted spread (TBBO, 2024-03-05)

| NY hour | trades | mean spread (pts) | share at 1 tick |
|---|---|---|---|
| 01 | 1744.0 | 0.482 | 26.4% |
| 02 | 4733.0 | 0.467 | 31.1% |
| 03 | 7253.0 | 0.461 | 31.9% |
| 04 | 8225.0 | 0.505 | 23.0% |
| 05 | 6411.0 | 0.467 | 29.5% |
| 06 | 5289.0 | 0.471 | 28.1% |
| 07 | 9305.0 | 0.491 | 27.7% |
| 08 | 11340.0 | 0.47 | 29.0% |
| 09 | 73829.0 | 0.379 | 59.5% |
| 10 | 94941.0 | 0.382 | 56.6% |
| 11 | 49374.0 | 0.338 | 65.6% |
| 12 | 33771.0 | 0.338 | 65.5% |
| 13 | 39421.0 | 0.339 | 64.9% |
| 14 | 39489.0 | 0.339 | 65.6% |
| 15 | 58154.0 | 0.348 | 65.1% |
| 16 | 10393.0 | 0.38 | 50.6% |

## B–C. Stop slippage and touch fills, and what they do to expectancy

| model | trades | stops | stop slip median / p90 (pts) | slip in R (mean) | wins touch-only at entry | TP1 touch-only | exp R as simulated | + real stop slip | + worst case for touch fills |
|---|---|---|---|---|---|---|---|---|---|
| 2022_model | 202 | 126 | 0.00 / 1.00 | 0.054 | 4 of 70 | 7 of 70 | -0.051 | -0.084 | -0.135 |
| cameron | 253 | 180 | 0.00 / 0.25 | 0.029 | 0 of 67 | 11 of 67 | -0.080 | -0.101 | -0.101 |
| mmxm | 91 | 53 | 0.00 / 0.75 | 0.014 | 0 of 27 | 0 of 27 | +0.024 | +0.015 | +0.015 |
| silver_bullet | 171 | 112 | 0.00 / 0.98 | 0.016 | 2 of 54 | 4 of 54 | -0.050 | -0.060 | -0.090 |
| pd_return | 530 | 348 | 0.00 / 0.50 | 0.028 | 1 of 164 | 12 of 164 | +0.136 | +0.118 | +0.110 |

Stops without a matching opposite-aggressor trade within 2 minutes are left out (1 of 820). A touch-only TP1 that later
traded through by a tick counts as filled at its R (23 of 34 did); the rest run on to the stop or 16:00.

## Where the slippage comes from: release minutes

38 of 819 stop-outs happened in a release minute (08:29–08:32, 09:59–10:01, 13:59–14:01, 14:30–14:31). They carry most
of the cost: the worst were GDP 2024-04-25 (41 pts on an 18-pt stop), NFP 2024-06-07 (30 pts on 6.75), CPI 2024-03-12
(26 pts on 7), FOMC 2024-09-18 (21.5 on 9).

| model | other stops: n / mean slip R | release-minute stops: n / mean slip R |
|---|---|---|
| 2022_model | 120 / 0.018 | 6 / 0.784 |
| cameron | 172 / 0.008 | 8 / 0.482 |
| mmxm | 49 / 0.010 | 4 / 0.072 |
| pd_return | 328 / 0.009 | 20 / 0.340 |
| silver_bullet | 112 / 0.016 | 0 / – |

69% of all stops filled at the stop price exactly, 85% within one tick.

## Reading

1. **The futures cost model holds outside news.** Quoted spread is 1 tick 57–66% of the time in 09:00–16:00 (mean
   0.34–0.38 pt) and about 0.47 pt overnight. Away from release minutes a stop-out costs 0.01–0.02 R more than
   simulated. The model's 1 tick + $4.50 is about right in the day session and slightly optimistic overnight
   (Asia/London models: Cameron, SB London).
2. **Release minutes are the real hole.** A stop sitting through an 08:30 print can slip by several times the risk.
   That is a realism cost the simulator does not see (it fills stops at the price), and it is concentrated in a few
   trades. The `news_blackout` gate exists and is off; this is an argument to test it as a pre-registration (selection on
   2022–24 CFD/futures, ≥ 30 OOS trades), not to switch it on from this table (2024 NQ is out-of-sample/burned).
3. **Touch fills matter little.** 7 wins of 382 were entry touch-only; 34 TP1s were touch-only and 23 of those traded
   through later the same day. Worst case costs 0.00–0.05 R.
4. **Net:** realistic execution lowers expectancy by about 0.01–0.08 R per trade (2022 model the most: −0.051 →
   −0.135 R worst case). No model changes sign: the two positive ones stay positive (PD return
   +0.136 → +0.110, MMxM +0.024 → +0.015); the negative ones get more negative.
