# New datasets (2026-11-16) through the change gate
Source: `research/sweeps/2026-11-16-new-datasets.md` (review log #40). Sharif 2026-11-16: "Proceed. You may park what you mentioned."

## 1. Parked (Sharif's decision)
- **Cameron** (all assets): 23–28% win, −0.23 R on US100 (z −3.6), −0.16 on US500, no edge on any dataset.
- **MMxM on gold:** 23% win, −0.23 R (n 230, z −2.9).
Parked = no more tuning, sweeps or review time. The code and its tests stay; old results stay in the store. Un-park only with a new idea that the pattern finder supports.

## 2. Activity gate — **option behind a flag (done), then in-sample, then one run on 2021**
- Witnesses: pattern-finder / time_activity (quiet −0.17 R, z −3.2, n 675; busy > quiet in 6 of 7 datasets; 2022 model quiet 26% / −0.35 R); Sharif's principle (be in the market when price is moving); trade-review checklist step 1. PD-array audit silent. No disagreement.
- Change: `ict_engine/concepts/activity.py` (`relative_activity`, `gate`), `min_activity` on the 2022 model, MMxM and silver bullet (default None = off), checked in `sim.run.run_day` at the decision time; variants `activity >= 0.6`. Tests first (`tests/test_activity.py`: busy/normal/quiet, no look-ahead, no block without history, off by default + label). Suite: 506 passed.
- Next: in-sample variant run on the three indices 2022–24, then `research/preregistered-2021-activity-gate.md`.

## 3. Thresholds in index points (silver, DXY, EUR/USD cannot be traded) — **bug fix, queued**
- Evidence: 0 trades for the 2022 model on XAGUSD / DXY and for every model on EURUSD; blocked@target with "potential 0.3" against `min_potential` 10.0; MMxM "no untaken curve level beyond the minimum TP1 distance". `FUTURES_POINT_VALUE` also has no entry for DXY / EURUSD.
- Fix to make (after the running test finishes; no engine edits during a run): express the absolute thresholds per asset (a scale from the instrument table), keeping the index values exactly as they are (R7: index backtests must not move).

## 4. Dropped
- Stop-size floor / `cost <= 0.05R` / no premarket as general rules (review log #39).
