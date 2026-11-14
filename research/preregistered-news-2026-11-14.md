# Pre-registered: scheduled news — stay out, or be flat through the release (written 2026-11-14, before any code or run)

From the cost check (`research/cost-check-NQ-2024.md`): of 819 model stop-outs on CME NQ 2024, the 38 in a release
minute (08:29–08:32, 09:59–10:01, 13:59–14:01, 14:30–14:31) slipped **0.41 R on average** (GDP 2024-04-25: 41 pts on an
18-pt stop); the other 781 slipped 0.01 R. The simulator books every stop at exactly −1 R, so today it cannot see this.

## Part A: realism setting (measurement, not a rule to select)
`release_slip`: a stop hit inside a release minute fills **a quarter of the way from the stop to that 1m bar's extreme**
(beyond the stop). Calibrated on those 38 NQ 2024 stops: rule 4.1 pts mean vs real 4.4 pts (a gap-at-the-open rule gave
only 1.1; the bar's close 8.3; the extreme 16.2). Other stops unchanged (real slip 0.01 R ≈ the 1-tick cost already
charged). Applied to the baseline **and** every variant below, so the comparison is like for like. Not a default yet:
the forward test (`forward-v1`) stays frozen; adopting it is a separate decision for Sharif.

## Part B: variants (all 5 models, everything else at defaults)
| name | rule |
|---|---|
| news: no new trades near a release | existing `news_blackout=(30, 15)`: no decision 30 min before to 15 min after a high-impact release |
| news: flat through the release | the above **and** any open trade is closed at the open of the 1m bar one minute before the release (`TradePlan.time_exit`) |
| news: FOMC wait for the statement | existing `fomc_day="after_statement"` |

High-impact = `ict_engine/news/calendar.py` "high" (NFP, CPI, PPI, retail sales, GDP, PCE, JOLTS, FOMC statement and
press). The schedule is known in advance; no released numbers are used.

## Test and decision rule
Futures basis only. US100 US500 US30 XAUUSD XAGUSD, 2022-01-03→2024-06-28, the variants tool's 70/30 split. Measure:
expectancy all out at TP1 (R), with `release_slip` on. 3 variants × 5 models = 15 cells: pass = OOS Δ vs baseline with
**z ≥ 2.6** and **≥ 30 OOS trades**. Also reported (not scored): the same with `release_slip` off, and Δ on only the
trades the rule changes. Expect small effects: only ~5% of stops sit in a release minute. 2024-07+ unused.

## Amendment 1 (2026-11-14 20:30 SAST, before any code or run): two models
Sharif narrowed development to the 2022 model and MMxM (`research/model-selection-2026-11-14.md`). Cells: 3 variants ×
2 models = 6; pass bar **z ≥ 2.4** (Bonferroni-style for 6 one-sided tests at 5% family-wise ≈ 2.39), ≥ 30 OOS trades. Silver Bullet, Cameron and PD return are not run.
