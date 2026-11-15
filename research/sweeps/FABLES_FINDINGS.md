# FABLES_FINDINGS — what went wrong in the existing runs (2026-11-16)

Source write-up: `research/sweeps/2026-11-16-winrate-sweep.md` §7.

In-sample data only (trade dates ≤ 2024-06-28; no 2024-07+ rows were loaded for these). FF-01 … FF-09: the engine plans (`reports/plans-sim.parquet`, `reports/plans-sweep*.parquet`, 2022-03 → 2023-09).
FF-101 … FF-112: the model engine (trade store `reports/trades/*.parquet` at commit `c60c27f`, futures cost, 5 families × 5 assets, 2022-01-03 → 2024-06-28: 9,717 trades, −0.045 R, day-clustered z −2.2; no family positive after cost).
Every item carries the tag FABLES_FINDINGS. Effects are in-sample estimates; each fix needs its own test before it becomes a default.

### FF-01 — The plan sim's "win %" is "closed in profit", not "TP1 before the stop"  (FABLES_FINDINGS)
- **What is wrong**: `plan_build._stats` reports `win% = runner_r > 0` and `tp1_hit% = r_tp1 > 0`, and `manage` sets `r_tp1` to the open P&L when a trade is closed at the horizon. Review log #35–36 therefore quotes 38 % (touch) and 25 % (support). Strictly: touch 6.7 % (49 of 732), support 4.8 % (22 of 460), flip 29.4 % (62 of 211). 453 of 732 touch trades end "open at the horizon".
- **Suggested fix**: report strict `win` (TP1 traded before the stop) beside "closed in profit"; `plan_sweep.stats` does. Correct #35–36 and `out/plan-results.html`.
- **Expected effect**: none on R; the stated distance to 50 % becomes 43 points (touch), not 12.
- **How to test**: `tests/test_plan_day.py::test_manage_np_matches_manage_on_random_paths` pins the definition; add the column to `_stats`.

### FF-02 — The plan's stop and target are swing-trade sized (1.6 ADR and 2.6 ADR)  (FABLES_FINDINGS)
- **What is wrong**: median risk 1.61 ADR, median TP1 1.6 R away. Held for the day: 10 % stopped, 1.9 % reach TP1, 88 % closed at 16:55 (n 576, −0.041 R). Held 5–10 days: 34 % stopped, 6.7 % TP1, median hold 2.7 days. With the zone stop (0.44 ADR) the plan TP is 6.3 R away; with the reaction stop (0.17 ADR), 15.6 R.
- **Suggested fix**: intraday plans take the stop from the structure that confirmed (5m/15m swing) and TP1 from the nearest session pool ≥ 1 R; keep the swing extreme only as the runner's target.
- **Expected effect**: strict win from ≈ 5 % to 44–53 % (measured at 1 R with the tight stops); R ≈ 0 until the entry is selective (FF-04).
- **How to test**: `plan_sweep.py` cells `tp ∈ {1R, pool05}` × `stop ∈ {reaction, zone}` × `day_only`; next, an MSS-based stop (§3 #4).

### FF-03 — Fading into the chosen array is worse than a coin flip on the day  (FABLES_FINDINGS)
- **What is wrong**: after a touch fill, by 16:55 price has travelled further against the plan than for it on 58 % of 576 trades (median for 0.25 ADR, against 0.37 ADR); fast moves 65 % (n 150). Multi-day: median for 0.65 ADR, against 0.99 ADR. All 84 touch cells of the sweep are negative (−0.04 to −0.30 R).
- **Suggested fix**: stop opening on the touch. Arm at the zone and trade the outcome: the failure (flip) now, a structure-shift confirmation (§3 #4) when built.
- **Expected effect**: removes −106 R (732 trades) in-sample; the flip leg alone is +7 to +36 R day-only (148 trades).
- **How to test**: pre-registration in §1; random-entry baseline (§3 #6) to show the 58 % is not just drift.

### FF-04 — "Confirmation" (first lower-TF FVG) is not selective, and a displacement filter does not make it so  (FABLES_FINDINGS)
- **What is wrong**: support leg, zone stop: 71 % stopped (multi-day), 48 % of those never made 0.5 R. With `min_disp=1.5`, 431 of 460 trades remain (94 %) and the win rate at 1 R is unchanged (46.3 % vs 46.7 % day-only; 51.7 % vs 53.0 % multi-day). With the tight stop, 69 % of stopped trades later trade ≥ 1 R our way (39 % inside the day): the idea is often right, the entry early.
- **Suggested fix**: confirmation = lower-TF close beyond the last opposing swing made after the touch (MSS) with displacement; enter the FVG it leaves; stop behind the failed swing.
- **Expected effect**: unknown; the ceiling is the 45–53 % of fills that reach 1 R before the stop today.
- **How to test**: `replay_confirm(confirm="mss")` + hand-built tests, then the cached-pin sweep; target strict win ≥ 55 % at 1 R on ≥ 200 trades in-sample before a pre-registration.

### FF-05 — Overlapping and duplicated plan trades overstate n and z  (FABLES_FINDINGS)
- **What is wrong**: the plan is re-made every morning while the previous day's trade is still open (median hold 3,900 min). 37 of 732 touch trades, 23 of 460 support and 12 of 211 flip trades have an identical fill minute to another row; many more overlap in time. US100 / US500 / US30 take the same trade on the same day: per-trade z −4.35 becomes −3.68 on day totals.
- **Suggested fix**: one open position per asset; no new plan on a zone that already has a live trade; report z on day totals; consider one index per day.
- **Expected effect**: R per trade about unchanged (flip multi-day 1 R: +0.093 → +0.119 de-duplicated, n 199); intervals 10–20 % wider. Day-only removes the time overlap entirely.
- **How to test**: dedup rule in `simulate` with a unit test; `plan_sweep.stats` already prints `z_day`.

### FF-06 — One read at 08:30; fills before 09:30 lose  (FABLES_FINDINGS)
- **What is wrong**: flip leg fills before 09:30: −0.06 R day-only at 1 R (n 34), −0.28 R at pool targets, −0.21 R multi-day (n 50); 09:30–12:00: +0.13 R / +0.50 R (n 84). 286 of 909 plans (31 %) never reach their zone by 15:00. On NFP / CPI days the read is taken at the release minute.
- **Suggested fix**: no fills before 09:30; re-read at 09:30 / 10:00 / 11:00 / 13:30 with the 1H range.
- **Expected effect**: flip day-only 1 R +0.047 → +0.080 R (fills ≥ 09:30, n 114); weak (z < 1), post hoc.
- **How to test**: fixed rule in the pre-registration; multi-time pin cache for the re-read.

### FF-07 — The plan sim has no trading cost  (FABLES_FINDINGS)
- **What is wrong**: `plan_build.replay*` report gross R. Futures cost (1 tick + $4.50) is 0.002 R on range stops but 0.014–0.020 R per trade on flip / reaction stops: flip leg +57.9 R gross → +52.7 R net (211 trades); support · reaction · multi-day · 1 R +40.7 → +30.0 R (460). Flips with risk ≤ 0.1 ADR pay 0.03–0.05 R each and lose (−0.05 R day n 36; −0.24 R multi n 51).
- **Suggested fix**: subtract `instruments.futures_cost(asset) / risk` in `manage` (as `plan_sweep` does); add 1 tick of stop slippage (FF-101); minimum flip risk 0.1 ADR.
- **Expected effect**: −0.01 to −0.02 R per trade on tight-stop legs.
- **How to test**: unit test on a hand-built trade with a known cost.

### FF-08 — The multi-day results are a handful of outliers plus an arbitrary horizon  (FABLES_FINDINGS)
- **What is wrong**: flip multi-day plan TP +52.7 R → −2.7 R without its best 3; support · reaction · plan TP −6.6 R → −83.8 R without the best 3, −106.8 R capped at 10 R. The horizon (5 / 10 days) closes 62 % of touch trades at whatever price it lands on, so the horizon length is itself an untested parameter.
- **Suggested fix**: judge plan variants day-only (every trade closed by rule), always with "without best 3" and "capped at 10 R" beside the total.
- **Expected effect**: none on R; removes a source of false positives.
- **How to test**: already in `plan_sweep.stats`.

### FF-09 — Splits by read kind, range timeframe and move speed are not stable across legs  (FABLES_FINDINGS)
- **What is wrong**: "daily-range plans are better, 4H worse" holds on the flip leg (day 1 R: +0.146 vs −0.032 R) but the support leg wins more on 4H (50.9 % vs 36.0 % at 1 R). "Counter-weekly" plans are the best support trades (+0.121 R, n 174) and the worst flips (−0.100 R, n 92). Fast moves lose on touch and multi-day support, not on day-only legs (+0.05 to +0.06 R).
- **Suggested fix**: do not gate on these yet; carry them as tags; declare at most one as a secondary split in a pre-registration.
- **Expected effect**: avoids fitting noise (≈ 2,900 looks in this sweep).
- **How to test**: the selection hold-out 2023-09-29 → 2024-06-28 once the read cache is extended.

### FF-101 — Touch-only limit fills carry all the positive R  (FABLES_FINDINGS)
- **What is wrong**: `sim/simulate.py` fills a limit when the bar merely touches it, exits stops at exactly −1 R and fills TP1 on a touch. Re-reading each fill bar from the 1m data:

  | Price traded through the limit by | n | win | mean R | z |
  |---|---|---|---|---|
  | < 1 tick | 1,630 (16.8 %) | 31.8 % | +0.083 | +2.1 |
  | 1–2 ticks | 1,294 | 32.9 % | +0.085 | +1.8 |
  | 2–5 ticks | 2,493 | 30.2 % | −0.030 | −0.9 |
  | ≥ 5 ticks | 4,300 | 25.3 % | −0.141 | −4.7 |

  15.3 % of winners (426) exceeded TP1 by < 1 tick; 0.8 % of stops opened beyond the stop. Bars are bid-only, which further flatters long entries and short stops / TPs (inferred, not measured). The plan replays fill the same way.
- **Suggested fix**: require trade-through of ≥ 1 tick for limit entries and TP1, 1 tick slippage on stops, exit at the bar open on a gap through. Add a `fill_through_ticks` column.
- **Expected effect**: pooled expectancy −0.045 → −0.093 R (measured: touch fills dropped + stop slippage; TP touch not included); win rate ≈ −0.5 pt; every family negative (Silver Bullet +0.001 → −0.029).
- **How to test**: `fill_mode=through1` sim param, re-run the five in-sample backtests, compare with `store board --commit`; calibrate once on the Databento NQ TBBO data.

### FF-102 — Cost is larger than the whole gross edge; the 0.1 R cost gate is too loose for the 2022 model  (FABLES_FINDINGS)
- **What is wrong**: gross +91 R over 9,717 trades (+0.009 R / trade); cost 527 R (0.054 R / trade); net −436 R. Gross / cost by family: 2022 model −1 / 72, Cameron −84 / 129, MMxM −21 / 36, PD return +112 / 208, Silver Bullet +85 / 83. In the 2022 model R falls as cost / risk rises: ≤ 0.02 R +0.284 (n 92), 0.02–0.04 +0.086 (271), 0.04–0.06 −0.160 (308), 0.08–0.10 −0.242 (278). Split at 0.04 R: n 363, 39.4 % win, +0.136 R (z +1.7; halves +0.03 / +0.38) vs n 894, 32.3 %, −0.137 R (z −3.1). Driven by US100 (+0.176, n 266); US30 goes the other way (−0.26, n 51); Silver Bullet shows the opposite pattern.
- **Suggested fix**: test `max_cost_r=0.04` (and 0.05) for the 2022 model and MMxM only; add stop slippage to `cost_at` (1 tick averages 0.034 R per trade here).
- **Expected effect**: 2022 model −0.058 → about +0.1 R in-sample on 29 % of the trades; found post hoc on one asset, expect shrinkage towards 0. Win rate +5 pts on the kept trades.
- **How to test**: `eval.variants … --model 2022_model` with `max_cost_r` 0.04 / 0.05, pre-registered, one OOS confirmation.

### FF-103 — The ny_premarket window (07:00–08:29) loses in the 2022 model and Cameron  (FABLES_FINDINGS)
- **What is wrong**: 2022 model n 186, 27.4 % win, −0.303 R, z −3.3 (halves −0.27 / −0.35). Cameron n 279, 25.1 %, −0.325 R, z −4.2 (halves −0.43 / −0.18). Hour 7 pooled: n 663, −0.246 R, z −4.1. Worst cell US100 (2022 model −0.43, n 107; Cameron −0.61, n 92). MMxM (−0.02) and PD return (−0.06) are not affected. The window has no written ruling (§5).
- **Suggested fix**: drop `ny_premarket` from `windows` for the 2022 model and Cameron.
- **Expected effect**: 2022 model −0.058 → −0.015 R (n 1,071, win 35.6 %); Cameron −0.099 → −0.066 R. Removes a loss, creates no edge.
- **How to test**: variant "no premarket" (same shape as `NO_LONDON`), hold-out, one OOS check. 1 of 19 family × window cells; z −4.2 survives Bonferroni.

### FF-104 — The leaderboard CLI pools every commit, cost basis and duplicate run  (FABLES_FINDINGS)
- **What is wrong**: `store board` calls `load()` without `latest()`: in-sample it ranks 35,843 "trades" where the newest commit has 9,717 (n × 3.7; e.g. silver_bullet / sb_pm 1,120 vs 245). Commits `5996937` and `c60c27f` are byte-identical for 6,116 trades (the PD return futures run is stored three times). 49.5 % of rows have `cost_basis` NaN (so `--cost cfd` silently drops them). Without `--end` the board mixes in the unseen period. The store is 100 commits behind HEAD.
- **Suggested fix**: `latest()` by default in `board`; fill `cost_basis`; refuse a run whose rows hash the same as an existing one; default `--end 2024-06-28`; explicit `--unseen` flag.
- **Expected effect**: none on R; correct n and no accidental peeking.
- **How to test**: unit test in `tests/test_store.py` (two commits → board n equals latest n).

### FF-105 — The "confirm once" and "beats baseline OOS" protections are already used up  (FABLES_FINDINGS)
- **What is wrong**: 75 store files cover 2024-07-01 → 2026-11-12 at four commits per model and 10 more span 2022 → 2026 (file names and metadata only; rows not read). The `eval/variants.py` hold-out (last 30 % of the selection range) has been reused by 32 `reports/variants-*.parquet` sweeps. Defaults described as validated (`tp1_cap_r=2`, `max_cost_r=0.1`, `prev_day_dol`) rest on a slice tested dozens of times.
- **Suggested fix**: treat 2024-07 → 2026-11 as spent for any model already run on it; reserve future data via `research/forward-test-protocol.md`; log the cumulative variant count and require a deflated z for new defaults. (The engine plans have not been run on it: that confirmation is still unspent.)
- **Expected effect**: none on R; avoids promoting noise.
- **How to test**: process change.

### FF-106 — Absolute price-unit parameters break non-NQ assets  (FABLES_FINDINGS)
- **What is wrong**: `stop_buffer=0.25` and `min_potential=10.0` are price units for every asset. On XAGUSD the buffer is 87 % of the median risk (US100 2 %, US30 0.8 %, XAUUSD 12 %); 68 % of Cameron and 61 % of Silver Bullet XAG trades end at the time exit near 0 R with a 14–15 % win rate. The 2022 model has 0 XAGUSD trades (1,674 blocked at the target gate, median potential 0.5 vs 10 required); XAUUSD 1,369 target blocks vs 156 trades; US500 554 vs 229; US100 46 vs 571.
- **Suggested fix**: express both in ticks or ADR fractions per asset.
- **Expected effect**: XAG results become meaningful; more gold and US500 2022-model trades; direction of R not measured.
- **How to test**: re-run XAGUSD, XAUUSD, US500 in-sample with scaled parameters as a pre-registered variant; unit tests on hand-built candles.

### FF-107 — Half of all stops see TP1 trade later; a 1.5× wider stop does not fix it  (FABLES_FINDINGS)
- **What is wrong**: from `reports/gaps-futures.parquet`, 51 % of 6,185 stops had TP1 trade later the same session (2022 model 62 %, Cameron 56 %, PD return 50 %, Silver Bullet 44 %, MMxM 40 %); 27.6 % of stops had first reached ≥ +1 R. `cf_wide_stop` rescues only 9–12 % of stops and is worse in four of five families. 39 % of winners drew down past −0.5 R; 33–40 % of 2022 / Cameron / PD return stops come within 5 minutes. Same picture as the plans (FF-04): direction is right more often than the entry survives.
- **Suggested fix**: test "re-arm after the second sweep" and banking at +1 R MFE; do not widen the stop.
- **Expected effect**: uncertain; re-entry v1 / v2 already failed (#32, #33); the ceiling is the 28 % of stops that reached +1 R.
- **How to test**: one pre-registered variant per idea in `eval.variants` (metric `runner_r`), hold-out, one OOS run.

### FF-108 — Two review counterfactuals are mis-specified  (FABLES_FINDINGS)
- **What is wrong**: in `eval/backtest.counterfactuals`, `cf_flip` keeps `order="limit"` at the long's entry, so the short fills on the first bar at a worse-than-market price with the stop 1 R above (2022 model −0.817 R, 8.6 % wins). `cf_tp1_1r` keeps `arm`; TP1 at 1 R usually lies before the arm level, so the sim returns "missed": only 18.1 % of 2022-model trades have a `cf_tp1_1r_r`, and its 8 % "win rate" is an artefact. `gaps-futures.parquet` stores `tp1_after` as strings, so `bool()` reads every row as True. The review's "wrong_side" and "target_too_far" shares are unreliable.
- **Suggested fix**: flip at the real fill time and price; drop `arm` for `cf_tp1_1r`; store booleans.
- **Expected effect**: none on trading R; corrects the diagnosis shares.
- **How to test**: unit tests on hand-built candles (the flip of a stopped long with a symmetric target must win).

### FF-109 — The bias gate adds nothing in MMxM and Silver Bullet; MMxM's POI and risk gates block better setups than it trades  (FABLES_FINDINGS)
- **What is wrong**: shadow R of blocked vs traded setups, de-duplicated — MMxM bias −0.038 (n 1,310) vs traded −0.064; Silver Bullet bias +0.034 (n 8,469) vs +0.001; MMxM POI +0.074 (n 239); MMxM risk (cost > 0.1 R) +0.377 (n 88, z 1.7; tiny stops, likely touch-fill optimism, FF-101). In the 2022 model and PD return the bias gate helps (blocked −0.12 / −0.13). `review.gate_value` uses raw overlapping rows (Silver Bullet bias −0.036 raw vs +0.034 first-per-window).
- **Suggested fix**: test `use_bias=False` for MMxM and Silver Bullet and `use_poi=False` for MMxM; de-duplicate `gate_value` per asset-day-window-side.
- **Expected effect**: ≈ 2× more MMxM trades at about the same R; small.
- **How to test**: `eval.variants --model mmxm` / `silver_bullet` with the gates off, then OOS once.

### FF-110 — Trades are heavily duplicated across assets and models  (FABLES_FINDINGS)
- **What is wrong**: 62–85 % of index trades share day and side with another index in the same family (same outcome 65–87 % of the time when the window matches too); 81 % of all trades sit in an asset-day-side also traded by another family; within a run 2,486 of 3,601 PD return and 563 of 1,257 2022-model trades repeat asset + day + side. Clustered vs naive standard error 0.0207 vs 0.0160: effective n ≈ 5,800 of 9,717.
- **Suggested fix**: report clustered z only; a portfolio view (one position per day-side across indices); pick one index per model.
- **Expected effect**: none on R; intervals 1.1–1.3× wider.
- **How to test**: `--by day` portfolio table in `store board`.

### FF-111 — 08:30–09:29 is the weak part of the NY AM killzone for the 2022 model and MMxM  (FABLES_FINDINGS)
- **What is wrong**: within `ny_am_kz` the 2022 model makes −0.107 R (n 211) before 09:30 and +0.099 (n 231) after; MMxM −0.306 (n 109, z −2.2) before, +0.059 (n 100) after; Cameron is the reverse. Agrees with the plans (FF-06). Weekday and news buckets show nothing at |z| ≥ 2.1.
- **Suggested fix**: test "ny_am from 09:30" for the 2022 model and MMxM.
- **Expected effect**: about +0.05 R for those two; weak (differences z 1.5–2).
- **How to test**: window variant in `eval.variants` with the hold-out; OOS only if in-sample z > 2.

### FF-112 — Holiday and half-day sessions are traded; data otherwise clean; no look-ahead found  (FABLES_FINDINGS)
- **What is wrong**: `dukascopy.check` in-sample: 0 duplicates, 0 bad OHLC; 19–27 gaps ≥ 5 minutes inside 02:00–16:00 per asset, nearly all US holidays; 20–22 weekdays per asset have < 95 % of bars and 11–21 of them were traded (n 156, −0.078 R vs −0.044); the day after (PDH/PDL from a truncated session) n 393, −0.086 R, z −1.2. Look-ahead audit by code reading (`context.py`, `events.py`, `bars.py`, `model_2022.py`, `sim/`, news tags): clean — events use `close_ts`, daily bars are cut at 17:00 the day before, fills start on the bar after `placed_at`, news uses the schedule only. The plan replays use each confirmation candle only from its close (tested).
- **Suggested fix**: holiday / early-close calendar gate; skip PDH/PDL built from a session with < 95 % of bars.
- **Expected effect**: negligible (≈ 1.6 % of trades).
- **How to test**: unit test for the calendar; variant "skip holiday sessions".
