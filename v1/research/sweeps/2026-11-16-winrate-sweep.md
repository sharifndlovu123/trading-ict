# Win-rate sweep on the engine plans — 2026-11-16

**In-sample search, not a test.** 1,194 cached reads at 08:30 NY (US100 / US500 / US30, 2022-03-01 → 2023-09-28), 909 plans, 285 waits.
No 2024-07+ data was opened for the sweep. Sections 6–7 quote existing results files and already-run store runs; where those
carry "unseen" (2024-07+) numbers they are confirmations that were already spent, shown for the ledger only and not used to pick anything.

Reproduce: `uv run python research/scripts/plan_sweep.py` (19 s, 9 workers) → `reports/plans-sweep.parquet` (one row per trade × TP rule × partial)
and `reports/plans-sweep-fills.parquet` (one row per plan × entry config, with MFE / MAE). Tests: `uv run pytest -q tests/test_plan_day.py tests/test_plan_confirm.py` (23 pass).
The sweep reproduces the existing sim exactly at its defaults (touch 732 trades −106.0 R; support 460 −61.7; flip 211 +57.9).

## 0. The short answer

- **Target (50 % win, positive expectancy): not reached by any variant.** At a 1 R target a coin flip already wins 50 %, so "50 %" only
  means something together with expectancy. The engine's entries win 44–53 % at 1 R with +0.02 to +0.11 R per trade and z ≤ 1.2: a coin flip, within error.
- **The win rate the project has been quoting for the plans (38 % touch, 25 % support) is "closed in profit", not "TP1 before the stop".**
  Strictly, the plan's TP1 trades before the stop on **6.7 %** of touch fills and **4.8 %** of support fills; 453 of 732 touch trades are simply closed at the horizon.
- **Best honest variant for "day only": the flip leg, held to 16:55.** 148 trades (7.8 a month), TP1 = 1 R: 43.9 % win [36–52], +0.05 R all-out, +0.11 R with half left to run (z 1.2).
  TP1 = nearest pool ≥ 0.5 R: 25.7 % win, +0.24 R (z 1.65, +12 R without the best 3). All 21 day-only cells of this leg are positive (+0.05 to +0.24 R) and the ones split by half-period are positive in both halves; none is significant.
- **Everything that fades into the zone loses** in every day-only and multi-day form with a structural stop: touch (all 84 cells, z on day totals −1.3 to −5.3) and the support leg with the zone stop (all 42 cells, −0.6 to −2.3).
- **Day-only with the current plan cannot work as designed:** the plan's stop is 1.6 ADR away and its TP1 2.6 ADR away (medians). Inside one session 88 % of touch trades hit neither.
- 294 variant cells × 10 filters were searched on one data set. The best filtered cells (z ≈ 2.5–2.9) are what a search of that size produces by chance. Nothing here is a default until it passes a pre-registration.

## 1. The sweep

### What was added (defaults unchanged)

| Option | Where | Meaning |
|---|---|---|
| `day_only=True` | `plan_build.replay`, `replay_confirm` | flat at the last 1m close before 16:55 NY on the decision day; no arm / fill after 15:00 (`day_window`) |
| `stop_at="zone"` (touch) | `plan_build.replay`, `zone_stop` | stop beyond the entry array (+0.05 ADR, ≥ 0.1 ADR); the range stop still cancels the plan before the fill |
| `partial=` | `plan_build.manage` | fraction off at TP1 (0.5 default; 1 = all out) |
| `min_disp=` | `plan_build.replay_confirm` | the support FVG counts only if its middle candle's body ≥ k × the mean body of the 14 before (displacement) |
| `min_rr=`, `manage_fn=` | `plan_build.replay_confirm` / `replay` | hooks for sweeps |
| TP1 rules | `plan_sweep.tp1_price` | plan (structural) · pool (nearest untaken pool ≥ 1 R) · pool05 (≥ 0.5 R) · 1R · 1.5R · 2R · 3R |
| stats | `plan_sweep.stats` | win % = TP1 before the stop, Wilson 95 %, mean / total R, without the best 3, capped at 10 R, z per trade, z on day totals |

All R are **net of the futures cost** (1 tick + $4.50; 0.002 R per trade on range stops, 0.014–0.020 R on the tight ones).
"z (day totals)" sums the three indices per day first: they trade the same move, so the per-trade z overstates.
Entry legs: `touch` = fill at the array's near edge; `support` = first lower-TF FVG our way after the touch; `support_disp` = that FVG from a displacement candle (1.5×);
`flip` = lower-TF close through the array → the other side on the retest (stop beyond the array, risk median 0.18 ADR).

### Headline rows (half off at TP1 unless stated)

| Variant | n | win % [Wilson 95] | mean R | total R | w/o best 3 | capped 10 | z | z (days) |
|---|---|---|---|---|---|---|---|---|
| **Baseline** touch · range stop · multi-day · plan TP | 732 | 6.7 [5–9] | −0.148 | −108.5 | −123.9 | −108.5 | −4.35 | −3.68 |
| touch · range stop · **day** · plan TP | 576 | 1.9 [1–3] | −0.041 | −23.4 | −39.5 | −23.4 | −1.41 | −1.27 |
| touch · range stop · day · 1R | 576 | 6.6 [5–9] | −0.046 | −26.6 | −37.3 | −26.6 | −1.98 | −1.73 |
| touch · zone stop · day · 1R | 576 | 30.2 [27–34] | −0.137 | −79.1 | −93.7 | −79.1 | −3.46 | −3.01 |
| touch · zone stop · multi · 1R | 732 | 39.8 [36–43] | −0.223 | −163.4 | −185.1 | −163.4 | −5.19 | −4.65 |
| support · zone stop · multi · plan TP (current default) | 460 | 4.8 [3–7] | −0.144 | −66.3 | −108.2 | −78.2 | −1.57 | −1.35 |
| support · zone stop · day · 1R | 304 | 24.3 [20–30] | −0.055 | −16.8 | −23.2 | −16.8 | −1.21 | −1.08 |
| support · reaction stop · multi · 1R | 460 | 53.0 [49–58] | +0.065 | +30.0 | −10.1 | +18.7 | +0.79 | +0.70 |
| support · reaction stop · day · 1R, all out | 304 | 46.7 [41–52] | +0.028 | +8.5 | +5.5 | +8.5 | +0.51 | +0.48 |
| support_disp · reaction stop · day · 1R, all out | 287 | 46.3 [41–52] | +0.049 | +14.0 | +11.0 | +14.0 | +0.88 | +0.82 |
| flip · multi · plan TP (as in log #35) | 211 | 29.4 [24–36] | +0.250 | +52.7 | −2.7 | +27.3 | +1.30 | +1.22 |
| flip · multi · 1R | 211 | 53.1 [46–60] | +0.093 | +19.6 | −4.4 | +16.9 | +0.89 | +0.84 |
| **flip · day · 1R, all out** | 148 | 43.9 [36–52] | +0.047 | +7.0 | +4.0 | +7.0 | +0.62 | +0.63 |
| **flip · day · 1R** | 148 | 43.9 [36–52] | +0.112 | +16.6 | +5.4 | +16.6 | +1.20 | +1.14 |
| flip · day · 1.5R | 148 | 30.4 [24–38] | +0.121 | +17.9 | +5.8 | +17.9 | +1.13 | +1.07 |
| flip · day · 2R | 148 | 23.6 [18–31] | +0.147 | +21.8 | +6.0 | +21.8 | +1.18 | +1.10 |
| **flip · day · pool ≥ 0.5 R** | 148 | 25.7 [19–33] | +0.242 | +35.8 | +12.2 | +34.0 | +1.65 | +1.52 |
| flip · day · plan TP / pool ≥ 1 R | 148 | 20.3 [15–28] | +0.225 | +33.3 | +9.7 | +31.5 | +1.52 | +1.40 |

Reading it:
- **Day-only removes the outliers and the overlap.** Multi-day gains are a few big trades (flip multi: +52.7 R → −2.7 without the best 3). Day-only flip keeps +5 to +12 R without its best 3.
- **Smaller TP1 raises the win rate and lowers R.** On the flip leg: plan TP 20 % / +0.23 R → 1 R 44 % / +0.11 R. There is no TP rule that gives both.
- **Partial size barely matters** (flip day pool05: 50 % +0.242, 75 % +0.241, all out +0.240). The runner adds R only on fixed-R targets (1 R: +0.047 all out → +0.112 with half left).
- **The displacement qualifier does nothing**: 431 of 460 support trades remain at 1.5×; results are the same within noise.
- **Reaction stop vs zone stop on the support leg**: the tight stop wins 47–53 % at 1 R (coin flip); the zone stop wins 24–45 % at 1 R because the stop is 0.44 ADR and 1 R is too far for a session.

### Filters the data pointed at (flip leg, day-only; H1 = 2022-03 → 2022-12-15, H2 = after; n / win % / mean R)

| Filter | 1R all out: n · win % [95] · mean R · z(days) | H1 | H2 | pool ≥ 0.5 R: mean R · z(days) |
|---|---|---|---|---|
| all | 148 · 43.9 [36–52] · +0.047 · 0.63 | 94 / 45 / +0.03 | 54 / 43 / +0.08 | +0.242 · 1.52 |
| fill 09:30 or later | 114 · 43.9 [35–53] · +0.080 · 0.93 | 73 / 47 / +0.09 | 41 / 39 / +0.07 | +0.398 · 2.06 |
| fill 09:30–12:00 | 84 · 46.4 [36–57] · +0.129 · 1.33 | 55 / 51 / +0.14 | 29 / 38 / +0.12 | +0.498 · 2.10 |
| daily range (not 4H) | 66 · 45.5 [34–57] · +0.146 · 1.31 | 42 / 45 / +0.07 | 24 / 46 / +0.28 | +0.465 · 2.26 |
| slow move | 106 · 43.4 [34–53] · +0.041 · 0.45 | 65 / 42 / +0.02 | 41 / 46 / +0.08 | +0.303 · 1.54 |
| daily range + fill ≥ 09:30 | 59 · 49.2 [37–62] · +0.231 · 2.01 | 37 / 51 / +0.18 | 22 / 45 / +0.31 | +0.621 · 2.81 |
| plan was not counter-weekly | 56 · 51.8 [39–64] · +0.290 · 2.55 | 36 / 44 / +0.11 | 20 / 65 / +0.61 | +0.528 · 2.45 |
| plan was an LTF pullback | 45 · 48.9 [35–63] · +0.301 · 2.53 | 30 / 43 / +0.13 | 15 / 60 / +0.63 | +0.489 · 2.37 |
| risk ≥ 0.1 ADR | 112 · 42.0 [33–51] · +0.079 · 0.89 | 70 / 46 / +0.11 | 42 / 36 / +0.03 | +0.363 · 1.96 |

Other cuts on the flip leg (day, 1R all out): US100 55 % / +0.25 R (n 49), US500 37 % / −0.06, US30 40 % / −0.04; fills before 09:30 −0.06 R (n 34) and, multi-day, −0.21 R (n 50);
Mondays −0.31 R (n 14); OB-sourced plans: n 1–3 on the flip leg, too few to say. On the support leg the same cuts point the other way (daily range 36 % win; counter-weekly best), i.e. the cuts are not stable across legs.

**Multiple comparisons.** 294 cells (7 TP rules × 3 partials × 14 entry/stop/hold legs) and 10 filters ≈ 2,900 looks at 148–732 correlated trades. The largest z by chance in a search like this is about 3.
The best cell here is 2.9. Treat the filter table as a list of hypotheses.

### What to pre-register (one candidate, fixed before any new data)

*Flip leg, day-only, fills 09:30–15:00, flat 16:55, TP1 = nearest untaken pool ≥ 0.5 R, 50 % off, stop to entry* (and its 1 R all-out twin as the win-rate version), US100 / US500 / US30.
1. Extend the read cache to 2023-09-29 → 2024-06-28 (still inside the selection window; `read_build.CUT` is hard-coded to 2023-09-29, so it needs a parameter) and run the candidate once there: expect ≈ 55–70 trades. Go on only if mean R > 0.
2. Then one confirmation on 2024-07+ under the project bar: ≥ 30 trades and z ≥ 2.4 on day totals. At +0.24 R and sd ≈ 1.8 R that needs ≈ 320 trades (≈ 3½ years at 7.8 a month): **the unseen period (28 months, ≈ 220 trades) can confirm it only if the true edge is ≥ 0.3 R.** Say so in the pre-registration.

## 2. Why the engine loses — where in the process

Numbers from `reports/plans-sweep-fills.parquet` (MFE = best run our way before the stop traded; MAE = worst against; in R of the trade's own risk, or ADR).

| Step | Finding | Evidence |
|---|---|---|
| **Side at the zone** | Fading into the array is slightly worse than a coin flip. | After a touch fill, by 16:55 price has gone further against than for on **58 %** of 576 trades (median for 0.25 ADR, against 0.37 ADR). Fast moves: 65 % against. Over the multi-day horizon: median for 0.65 ADR, against 0.99 ADR. The same arrays traded the other way after they fail (flip) are the only positive leg. |
| **Array choice** | The picked array is often not where price turns. | 97 of 909 plans (11 %) run to TP1 without filling, 80 are never reached; in day-only 286 (31 %) are not reached by 15:00. Of the fills, 211 + 40 (34 % of the 732) close through the array on the confirmation timeframe. |
| **Entry trigger** | The first 5m/15m FVG is not confirmation; neither is a 1.5× displacement candle. | Support leg, zone stop: 71 % stopped multi-day; 48 % of the stopped never made 0.5 R. `support_disp` = same win rate (46.3 vs 46.7 % at 1 R). |
| **Stop placement** | Two different failures. Range stop: far too wide for the hold. Tight stops: hit by noise, then the move happens. | Range stop median **1.61 ADR**; only 34 % are stopped in 5–10 days, 10 % in a day. Reaction stop (0.17 ADR): 88 % stopped, median 2 h after the fill, and **69 %** of those stopped trades later traded ≥ 1 R our way inside the horizon (39 % inside the day). Zone stop (0.44 ADR) is the in-between that fixes neither: 41 % later ≥ 1 R. |
| **Target placement** | TP1 is the multi-day swing extreme: almost never reached. | Plan TP1 median 1.6 R on a 1.6 ADR stop ≈ **2.6 ADR** away; strict TP1-first rate 6.7 % (touch), 4.8 % (support, zone stop, where it is 6.3 R away), 3.7 % (reaction stop, 15.6 R away). Of stopped support trades only 2 % reach the plan TP later. Meanwhile 45 % (zone) – 53 % (reaction) of support fills made ≥ 1 R before the stop. |
| **Holding period** | Results are decided by where the trade happens to sit at the horizon. | Touch baseline exits: 453 open at the horizon, 246 stopped, 33 at targets; median hold 3,900 minutes (2.7 days). Positions from consecutive days overlap on the same zone (37 identical fill minutes; far more overlapping in time), and across the three indices. |
| **Decision time** | One read at 08:30, then nothing. | Fills before 09:30 lose on the flip leg (−0.06 R day, −0.21 R multi); 09:30–12:00 is where the flip leg earns (+0.13 R at 1 R, +0.50 R at pool targets). |

Ranked by how many R it costs: **(1) side at the zone / fading instead of following (the −106 R touch result is mostly this), (2) target distance, (3) stop scale vs holding period, (4) entry trigger, (5) array choice, (6) decision time.**

### Against Sharif's saves (`reports/reviews/plans.jsonl` 6 saves, 3 plans + 1 duplicate pair; `trades.jsonl` 5 saves — read only; n = 8, anecdotal)

| Engine | Sharif | Save |
|---|---|---|
| Stop beyond the 4H/1D fake-out: 143 pts (US500), 486 pts (US100) | Stop behind the 5m/15m structure at his entry: ≈ 10 pts and ≈ 15 pts — 1/14 and 1/30 of the engine's risk | trades: US500 2022-06-10, US100 2022-09-13 |
| TP1 = the move's extreme (US100 2023-06-08: 14,664, 6 R away) | TP1 = the nearest 1H FVG / minor buyside (14,402, ≈ 2 R), 50 % off; "on hourly this is a very long holding trade" | plans: US100 2023-06-08 |
| One target + final | Scales 50 / 25 / 25 at successive swing lows | trades: US30 2023-01-04; plans: US500 2022-04-29 |
| Enters at the near edge of a deep HTF array chosen at 08:30 | "The no. 1 focus is where we currently are"; "we need current structures to support it first … you took the bias overall too controlled"; "you're shorting quite late" | plans: US100 2023-06-08; trades: US500 2022-08-24, 2022-06-10 |
| Trades the fade; flip only as a mode | States the flip before it happens: "if price breaks below the OB and retests it below, we are looking to sell to reach our stop" — the old stop becomes the target | plans: US500 2022-04-29 (the engine's flip leg uses exactly that target) |
| Always has a plan if a side exists | "Wait" on 2 of 3 plans: wants the sweep of the high and a displacement first; "choppy markets trading inside a single range" | plans: US500 2022-10-25, US30 2022-06-22; trades: US30 2023-01-04 |
| — | His own tight stop is not safe either: on US100 2022-09-13 his 15-pt stop was hit one minute after the fill (−1 R) where the engine's wide stop made +2.1 R | trades: US100 2022-09-13 |

The saves and the numbers agree on three points: the stop and target scale is an order of magnitude too large for a day trade, the entry should come from structure forming now (not an array picked hours earlier), and a failed zone is a trade in the other direction.

## 3. Gaps and missing additions (ranked by expected impact × effort)

| # | Addition | Why it plausibly moves the win rate | Effort | How to test |
|---|---|---|---|---|
| 1 | **Follow the failure: make the flip (zone closed through → retest → other side) the intraday model**, day-only, session-pool TP1 | The only leg positive in every TP rule and both halves; matches his "if it breaks and retests, sell to the stop" | low (built) | Pre-registration above: selection hold-out 2023-09-29 → 2024-06-28 first, then 2024-07+ once |
| 2 | **Read during the session, not once at 08:30** (09:30, 10:00, 11:00, 13:30) with the 1H/15m range as the trade range | 31 % of plans are never reached in the day; fills before 09:30 lose; his "where we currently are" | medium (read cache per time; `HORIZON`/`CTF` already carry `1h`) | Cache pins at 4 times for the in-sample days; same sweep; compare day-only R and strict win % with the 08:30 read |
| 3 | **Intraday stop and target scale**: stop behind the 5m/15m swing that confirmed, TP1 the nearest session pool (Asia / London high-low, PDH/PDL, 1H swing) ≥ 1 R | Engine risk 1.6 ADR vs his ≈ 0.05–0.1 ADR; 45–53 % of fills make ≥ 1 R before the stop but the target is 6–15 R away | low–medium | Already partly in the sweep (`pool`, `pool05`, reaction stop): 47–53 % at 1 R, ≈ 0 R. The missing half is the structural stop (#4) |
| 4 | **Confirmation = a structure shift, not a gap**: lower-TF close beyond the last opposing swing made after the touch (MSS) with displacement, enter the FVG it leaves, stop behind the swing that failed | First-FVG and 1.5× body are both non-selective (94 % pass); 69 % of tight-stop losers later go ≥ 1 R our way = right idea, early entry | medium (`concepts/events` has MSS; wire into `replay_confirm` as `confirm="mss"`) | Unit tests on hand-built candles; sweep on the cached pins; success = strict win % at 1 R ≥ 55 % or at 1.5 R ≥ 45 % with n ≥ 200 |
| 5 | **Time gate on plan entries**: fills 09:30–12:00 (and 13:30–15:00), nothing before 09:30 | Flip leg <09:30 −0.06 / −0.21 R; "time is much more important" (log #21) | trivial (filter on `fill_min`) | Part of the pre-registration as a fixed rule, not a tuned window |
| 6 | **Random-entry baseline for the plans** (same fill minute, same stop size, random side; and same side at a random minute) | Without it a 53 % win at 1 R cannot be told from the 50 % a random walk gives; the spec requires it | low | 200 random draws per trade from the same 1m bars → edge = win % − baseline, with its interval |
| 7 | **One position per asset, no re-planning of the same zone, one index per day** | Removes overlap that inflates n and z; the three indices are one bet | low | Dedup rule in `simulate`; report z on day totals only (done in `plan_sweep.stats`) |
| 8 | **News tags on plan trades** (`ict_engine/news/calendar.py` is built) and the 08:30 release problem: the read is taken at the release minute on NFP/CPI days | Free information; 08:30 decisions on release days are made into the spike | low | Join `news_today` / `news_mins` to the sweep rows; split R; then a fixed "no fill within 15 min of a red release" rule in a pre-registration |
| 9 | **SMT divergence at the zone** as confirmation (US100 vs US500 vs US30 swings at the same time) | Ruling §20: confirmation, not a signal; the three indices are already loaded; no detector exists | medium | Detector in `concepts/` with hand-built tests; tag every fill; compare win % with / without (it is a pattern: scored by hit rate first) |
| 10 | **Daily bias agreement as a tag, not a gate**: flips from counter-weekly plans lose (−0.10 R, n 92), flips from aligned / pullback plans win (+0.29 R, n 56) | Largest split in the sweep, but it points the *opposite* way on the support leg → unstable | trivial | Carry it as a pre-declared secondary split in the pre-registration; do not gate on it yet |
| 11 | **Fix HTF array validity** (arrays closed through on earlier days still count; see §5 item 1) | Affects every baseline of the model engine; unknown size | low–medium | Lifecycle from the array's formation; rerun the default backtests in-sample; compare n and R |
| 12 | **Minimum size for a flip array** (risk ≥ 0.1 ADR) | Flips with risk ≤ 0.1 ADR: −0.05 R day (n 36), −0.24 R multi (n 51); cost alone is 0.03–0.05 R there | trivial | Fixed rule in the pre-registration |

Already tried elsewhere and failed, so not proposed again: sweep-then-displacement as a *gate* (#11), nested FVG (#14), higher-timeframe entries (#14), re-entry v1/v2 (#32–33), counter-trend small grabs (#33–34), OC retest (#30), cheap-half entries (#19), pool / hold runners on the models (#12).

## 4. The gap to 50 %

| Question | Answer |
|---|---|
| Strict win rate today (plan as built, TP1 before stop) | 6.7 % touch · 4.8 % confirm (support, zone stop) · 29 % flip |
| Best day-only variant with positive expectancy | flip · 1 R: **43.9 % [36–52]**, +0.05 R all out / +0.11 R with a runner; z 0.6–1.2 |
| Best ≥ 50 % variant | flip multi-day 1 R: 53.1 % [46–60], +0.09 R, z 0.9, second half of the period −0.11 R; support · reaction stop · multi-day 1 R: 53.0 % [49–58], +0.065 R, z 0.8. Both hold overnight and both are coin flips within error |
| Best filtered cell (chosen after looking) | flip · day · 1 R · plan not counter-weekly: 51.8 % [39–64], +0.29 R, n 56, z 2.6 — one of ≈ 2,900 looks |
| What 50 % needs to mean | At 1 R: ≥ 55 % for +0.10 R. At 1.5 R: 50 % = +0.25 R. At 2 R: 50 % = +0.50 R |
| Distance | Day-only, honest: **6 points short at 1 R (44 % vs 50 %), 20 points short at 1.5 R (30 % vs 50 %)**, and the interval is ±8 points wide |

What it would take: (a) an entry that is selective — today 45–53 % of fills make 1 R before the stop, which is what a random entry does; a real trigger (#4) has to lift that to 55 %+ on ≥ 200 trades; (b) decisions made where price is during the session (#2), so the stop is 0.1–0.2 ADR behind real structure and the 1–1.5 R target is a session pool inside the day's range; (c) following failed zones rather than fading into them (#1); (d) proof on data the search has not seen. None of (a)–(c) is shown to work yet; (c) is the only one with a positive sign so far.

## 5. Reference integrity check

Sections 5–7 were compiled from the reference files, the code and existing result files (read only). Column (b) comes from reading the code; a few claims were spot-checked
(`store board` never calls `latest()`; `ny_premarket` 07:00–09:30 in `clock.py`; `stop_buffer=0.25` / `min_potential=10.0` in `model_2022.py`; POI lifecycle on `day_1m`). The rest has not been re-verified line by line: check an item before acting on it.

- Page numbers on the cards are printed pages: for `pdftotext -f` add 4 for the ICT Bible and 1 for the Market Maker PDF.
- 2022 Content slides are images: p.5, p.6, p.13 were rendered and read; p.8 and p.25 by title only.
- ictindex transcripts have no local copy: "not verified" unless a ruling quotes them.
- Baselines (futures, 5 assets, 2022-01-03 → 2024-06-28, hold-out = last 30 %, all-out R) are from `research/entry-quality-results-2026-11-14.md`; none is distinguishable from 0.

### `references/models.md`

| Card | Valid (a) | Implemented (b) | Evidence (c) |
|---|---|---|---|
| 1 Silver Bullet | Matches rulings §1, §2, §7, §8. Transcripts not verified. | `models/model_sb.py:find_setups/_evaluate`. Windows, 15:00–16:00 option, one trade per day as written. **Drift:** no `sb_fixed_stop` (20 / 12 handles), no `half_size_after_loss`, no NQ 20/15 variant; stop is the 30-minute leg extreme, not the FVG candle ± 1 tick of §7; US30 minimum 40 points; tracked patterns not logged. | Hold-out n 511, 31 % win, +0.046 ± 0.065 R. Sweep-first gate −0.147 R, z −1.5 (#11). Flip: no pass. |
| 2 2022 Model | Source is third-party, as the card says; sequence agrees with the Notion addition. | `models/model_2022.py:_evaluate`. **Drift:** TP1 = nearest 5m swing / context level ≥ 1 R capped at 2 R (card: "minimum R 2 or 3", HTF FVG / OB targets); `use_htf_pricing=False`; "liquidity taken" accepts a run with no close back; `min_potential=10.0` price units for every asset; SMT and Unicorn not tracked. | Hold-out n 304, 36 %, −0.044 R; with runner +0.023 ± 0.099. Leg OTE 70.5 %: +0.40 R, z 1.1, n 84 (#19). Every other variant failed (#4, #11, #12, #14, #15, #29, #32–34). |
| 3 MMBM / MMSM | Phases match MM PDF printed p.2–6. The MM ruling overturns the card's "Engine" block (1m entry, "deepest" FVG, POI alone). | `models/model_mmxm.py:find_curve/smr_array/smr_purge/_evaluate`. Code follows the ruling, not the card (5m entry, `fvg_pick="first"`, purge + array required, stage 2 as `reacc1/reacc2`). "Invalid if" rules not built; only the stop applies. | Hold-out n 237, 29 %, −0.015 R; with runner −0.077 ± 0.086. OC retest −0.11 R, n 104 (#30). HTF stop +0.09, z 0.8. |
| 4 PO3 day | Bible printed p.13–14 confirms buying below the 00:00 open and the Judas swing. Stop / target / invalidation are engine defaults. | **Not implemented** (only a `po3_day` label in `eval/similarity.py`). | Untested (#8 open). |
| 5 OTE | 2022 Content p.13 confirms 0.62 / 0.705 / 0.79 and projections −1, −2, −2.5, −4. The card's −1.5 target is not on the slide. The "still to transcribe" note is stale. | No model. `models/range_entry.py:apply("leg_ote")` is an entry variant only. | 2022 model +0.40 R, z 1.1 (n 84); MMxM +0.06, z 0.3 (`range-in-play-results`). |
| 6 PD array return | Bible printed p.16–26 confirmed. Rulings §11 (body, not wicks) and §23 (the OB exists once its open is crossed) overturn the Bible's close-beyond-high rule. | `models/model_pd_return.py`; `concepts/events.py:order_blocks, breaker_blocks`. **Drift:** defaults `ob_confirm="extreme"`, `ob_measure="range"` = the Bible, not the rulings; entry is always a 1m FVG, not the "OB high"; validity looks at today's bars only. | Hold-out n 976, 28 %, +0.009 ± 0.058 R. OB arrays failed, best z +0.3 (#5). IFVG arrays failed (#7). |
| 7 TGIF | Not verified. | **Not implemented.** | Untested. |
| Cameron | Matches ruling §1. Transcript not verified. | `models/model_cameron.py`. Engine choices: 8h draw look-back, "running" = last 1h close above the one before, bias off. | Hold-out n 597, 28 %, −0.018 ± 0.065 R. Far-edge flip +0.87 R, z 2.3, n 26 (not a pass). |
| SMT reversal model ("to research") | Ruling §20: SMT is a confirmation, not a signal. | – | – |

### `references/framework.md`

| Rule | Valid (a) | Implemented (b) | Evidence (c) |
|---|---|---|---|
| §0 Style | Engine defaults. | Every setup hard-coded "day" with a 16:00 exit (`sim/run.py:run_day`). No scalp / swing. | Untested. |
| §1 Bias | Sources not verified. | `concepts/context.py:BIAS_RULES`; `model_2022.bias_gate`. **Doc drift:** `DEFAULT_BIAS_RULE` is `prev_day` but every model uses `prev_day_dol`. No monthly bias, no M/W/D alignment tag (only `weekly_trend`). | Trades against `htf40` did better on the hold-out (#33). Weekly structure failed, z +0.41 / +1.06 (#34). |
| §2 Timeframes | MM PDF printed p.4 confirmed. | `concepts/bars.py:resample`; POI on 1h/4h. | Higher timeframes 0 of 6 (`timeframes-trail-results`). |
| §3 Pricing | Bible printed p.27–29 confirmed. Ruling §17 adds: the range must have taken both sides. | `context.pricing`; ranges are plain 20/40/60-day high/low. HTF gate off → "discount of both" not enforced. `body_beyond_ce` computed, unused. | Cheap half ≈ 0 on both models, 0 of 6 (#19). |
| §4 POI | Bible printed p.15 and MM PDF p.5 confirmed. | `model_2022._poi`, `model_sb._poi`, `model_mmxm.smr_array`. A POI is a swept PDL/PWL/Asia level or a 1h/4h FVG only; no OB, breaker, rejection block. | Nested 4h FVG Δ 0.00 / −0.09 R (#14). Outside daily FVG z ≤ 0.4 (#15). |
| §5 Quarterly theory | Third-party, as stated. | Calendar quarter only (`eval/backtest.py:setup_row`) and `clock.midnight_open`. No AMDX labels. | Week 4 range 0.97× vs week 2 1.07×: no Q4 expansion (#10). |
| §6 Killzones | 2022 Content p.6 confirmed (02–05, 08:30–11, 13:30–16). Ruling §4 confirmed. | `concepts/clock.py:WINDOWS`. **Drift:** `ny_premarket` 07:00–09:30 is in four models' defaults and cites a ruling that is not in the file. No lunch gate, no `skip_am_after_big_london`, CBDR a label only. Gold and silver trade the index windows. | Untested as a rule; the window itself loses (FF-103). |
| §7 Where to close | Projection levels confirmed (p.13). | `model_2022._targets`, `models/targets.py`, `sim/simulate.py` (vote at TP1). No wick-CE, half-gap or SD-projection targets. | Target modes 0 of 8, within ± 0.09 R (#4, #9, #12). `eq_hold` +0.19 R, z 1.2 (#16). |
| §8 Entry / stop | 2022 Content p.5 and p.13 confirmed. | `model_2022.stop_anchor` (swing, ob, imbalance). Wick-CE stop not built. Trail = `runner_stop="trail_5m"`. | `ob` / `imbalance` stops untested. Trail −0.09 / +0.04 R. HTF stop 0 of 4. |
| §9 Validity | Ruling §6 confirmed. | `events.gap_lifecycle`, `inversions`, `quadrants`. **Drift:** a VI is retired on one body close; only the primary NDOG and the NWOG exist; no rebalanced → ITH rule. | Own-TF close vs 1m close: not significant (#7). |
| §10 Filters | Rulings §1, §5, §8, §9 confirmed. | `news/calendar.py:news_block` (off). `cap_scope="day"` for SB and Cameron. Missing: `nfp_week` tags, half-size rule, 3R column, low/high-resistance filter. | Untested (no news results file). |

### `references/patterns.md`

| Card | Valid (a) | Implemented (b) | Evidence (c) |
|---|---|---|---|
| Turtle Soup | Not verified. | `events.sweeps` (close back within 3 bars). No hit-rate log. | Sweep-first gate 0 of 15 (#11). Hold alternative n 12, too rare (#29). |
| Judas Swing | Bible printed p.14 confirmed. | Not implemented. | Untested. |
| Unicorn | Not verified. | Not implemented (breaker detector exists, no overlap check). | Untested (#23 open). |
| SMT divergence | Bible printed p.11–12 confirmed. Ruling §20: confirmation only. | Not implemented. | Untested (#26 open). |
| Macros | Not verified. | Trade windows only (`macro_0950`, `macro_1050`). | Untested. |
| Opening range | Not verified. | Only `model_2022.opening_range_bias` for neutral days. | Untested. |
| London high/low, Friday retracement, Notion patterns | Not verified. | Not implemented. | Untested. |
| CRT | Ruling §16 confirmed; card matches. | `research/scripts/crt_test.py`. | No edge: 12 of 12 cells fail (`crt-results`). |

### `references/pipeline.md`

| Stage | Valid (a) | Implemented (b) |
|---|---|---|
| 0–1 Data, context | "4-candle swings" contradicts Bible printed p.10 (3-bar swing). | `data/`, `context.build_context`. Swings use `strength=1` (3 bars). Context has no EQH/EQL or London levels (those live in `concepts/liquidity_map.py`). |
| 2–5 Clock, events, state, gates | Consistent. | `clock.py`, `events.py`, `models/base.py:GATE_ORDER`. Models evaluate each MSS; no step state machine. Would-be setups are logged. |
| 6–7 Mark, simulate | Consistent. | `base.TradePlan` (frozen); `simulate` counts the stop first and flags ambiguity. No high-resistance reject. |
| 8–9 Record, measure | Consistent. | `eval/backtest.py`, `eval/store.py:leaderboard` (Wilson, n ≥ 30), `eval/variants.py` (70/30). **Missing: patterns-present column, event ids, random-entry baseline.** |
| 10 Review | Consistent. | `eval/review.py`. The code table still lists only the 2022 model. |

### Drift and contradictions that matter most

1. **HTF array validity only looks at today's bars.** `model_2022._poi`, `model_sb._poi`, `model_pd_return.returns` run `gap_lifecycle` on `day_1m` (from 00:00): a 1h/4h FVG closed through on an earlier day still counts as a valid POI. MMxM looks back ≈ 1.25 days. Touches every baseline; size not measured.
2. **The patterns layer is unbuilt.** No detector for SMT, Unicorn, Judas, macros-as-pattern, opening range, London high/low; no trade records "patterns present", so no with / without comparison is possible.
3. **Three of seven model cards have no model:** PO3 day, OTE, TGIF.
4. **`ny_premarket` 07:00–09:30 has no written ruling** (ruling §4 gives 08:30–11:00) and it is the worst window (FF-103).
5. **"Discount of both ranges" is not enforced**; the HTF range is an N-day high/low, not the both-sides-taken dealing range of the Bible and ruling §17.
6. **Order-block defaults follow the Bible, not rulings §11 and §23** (tested both ways, no reliable difference, #5).
7. **The MMxM card's "Engine" block is stale** (code follows the ruling).
8. **The 2022 model card is stale on targets** (card: 2–3 R minimum and HTF targets; code: nearest 5m swing capped at 2 R).
9. **Ruling variants never built:** fixed Silver Bullet stop, half size after a loss, NQ 20/15 framework, NFP-week tags, 3R column, secondary NDOG, opening range gap. Ruling §10's "flip is planned, not built" is stale (`eval/flip.py` exists and failed).
10. **No random-entry baseline and no per-style reporting**, both required by the spec. Every trade is tagged "day".

## 6. Works / doesn't-work ledger

**Nothing has passed the bar.** No model, gate or variant is positive with ≥ 30 out-of-sample trades and z ≥ 2.4.

Periods: **SEL** = 2022-01-03 → 2024-06-28 (selection); **HO** = its last 30 % (2023-09-29 → 2024-06-28, the sweeps' hold-out); **UN** = 2024-07-01 → 2026-11-12
(already-run confirmations, quoted from existing store runs and results files; not used here to choose anything); **PLAN** = 2022-03 → 2023-09, in-sample, descriptive.
Futures cost basis unless marked. Δ = difference against the model's baseline, in R. Store figures: `store board --commit 5996937` (PD return `3bb9530`); the un-pinned board pools commits and inflates n ≈ 3–4× (FF-104).
Plan rows use the strict win (TP1 before the stop) and net R from this sweep; the older "38 % / 25 %" figures were "closed in profit" (FF-01).

| Item | Class | n | win % | mean R | z | period | source |
|---|---|---|---|---|---|---|---|
| **Models (pooled, 5 assets)** | | | | | | | |
| 2022 model | CONSISTENT LOSER | 1,257 / 1,562 | 34.4 / 31.7 | −0.058 / −0.122 | −1.4 / −3.5 | SEL / UN | store |
| Cameron | CONSISTENT LOSER | 2,134 / 2,540 | 26.0 / 27.5 | −0.099 / −0.069 | −2.9 / −2.1 | SEL / UN | store |
| Silver Bullet | NO EDGE (loses UN) | 1,839 / 1,902 | 29.3 / 27.1 | +0.001 / −0.102 | 0.0 / −2.8 | SEL / UN | store |
| MMxM | NO EDGE | 886 / 1,092 | 27.5 / 28.0 | −0.064 / −0.028 | −1.2 / −0.6 | SEL / UN | store |
| PD array return | NO EDGE | 3,601 / 4,596 | 28.2 / 27.5 | −0.027 / −0.046 | −0.8 / −1.7 | SEL / UN | store |
| **Per asset / window** | | | | | | | |
| 2022 model US30 | CONSISTENT LOSER | 301 / 373 | 32.2 / 28.4 | −0.108 / −0.201 | −1.4 / −3.1 | SEL / UN | store |
| 2022 model US100 | CONSISTENT LOSER | 571 / 514 | 33.6 / 31.9 | −0.073 / −0.116 | −1.3 / −2.0 | SEL / UN | store |
| 2022 model US500 | NO EDGE | 229 / 299 | 36.7 / 35.1 | +0.009 / −0.042 | 0.1 / −0.6 | SEL / UN | store |
| Cameron US500 | CONSISTENT LOSER | 398 / 437 | 27.6 / 27.5 | −0.163 / −0.154 | −2.2 / −2.1 | SEL / UN | store |
| Cameron US100 | NO EDGE (loser in SEL only) | 614 / 598 | 23.3 / 27.4 | −0.231 / −0.023 | −3.6 / −0.3 | SEL / UN | store |
| MMxM XAUUSD | NO EDGE (loser in SEL only) | 229 / 273 | 22.7 / 27.5 | −0.234 / +0.016 | −3.0 / 0.2 | SEL / UN | store |
| MMxM US100 | NO EDGE (loses UN) | 221 / 248 | 31.7 / 25.0 | −0.003 / −0.170 | 0.0 / −2.1 | SEL / UN | store |
| MMxM US30 | NO EDGE | 212 / 215 | 31.1 / 31.6 | +0.060 / +0.010 | 0.6 / 0.1 | SEL / UN | store |
| Silver Bullet US30 | NO EDGE | 384 / 405 | 31.8 / 28.4 | +0.074 / −0.105 | 0.8 / −1.3 | SEL / UN | store |
| PD return XAGUSD | NO EDGE (loser in SEL only; see FF-106) | 255 / 694 | 27.1 / 29.1 | −0.259 / +0.001 | −3.2 / 0.0 | SEL / UN | store |
| 2022 model, NY premarket window | CONSISTENT LOSER | 186 / 247 | 27.4 / 30.4 | −0.303 / −0.195 | −3.3 / −2.2 | SEL / UN | store |
| Cameron, NY premarket window | CONSISTENT LOSER | 279 / 396 | 25.1 / 25.5 | −0.325 / −0.189 | −4.2 / −2.3 | SEL / UN | store |
| Silver Bullet, London | NO EDGE (loses UN) | 937 / 1,031 | 31.4 / 29.8 | −0.029 / −0.134 | −0.5 / −2.7 | SEL / UN | store |
| MMxM, NY premarket | NO EDGE | 197 / 220 | 31.5 / 38.6 | −0.023 / +0.076 | −0.2 / 0.7 | SEL / UN | store |
| Window selection #1 (3 kept buckets) | NO EDGE | 876 | – | −0.134 (all buckets −0.102) | – | UN | `preregistered-selection-1.md` |
| Window × asset selection #2 | NO EDGE | 341 | – | −0.115 (all −0.098) | −1.4 | UN, CFD | `preregistered-selection-2.md` |
| CRT 1h (stand-alone) | CONSISTENT LOSER | 6,775 | 60 (TP1) | −0.143 | −5.8 | HO | `crt-results` |
| CRT other cells | NO EDGE | 89–1,406 | 57–69 | −0.126 to +0.062 | −2.5 to +0.6 | HO | `crt-results` |
| **Bias** | | | | | | | |
| prev_day_dol as a day forecast | PROMISING | – | 62–67 hit vs 51–55 always-bull | – | – | SEL | `direction-diagnosis` |
| prev_day_dol as a trade filter (default) | NO EDGE | 4,475 | – | −0.030 | −1.2 | SEL | `direction-diagnosis` |
| htf20 | NO EDGE | 5,468 | – | −0.044 | −1.8 | SEL | `direction-diagnosis` |
| htf40 (with / against) | NO EDGE | 156 / 98; 93 / 69 | – | −0.17 / +0.17; −0.12 / +0.28 | – | HO | #33 |
| weekly_structure (with / against) | NO EDGE | 139 / 115; 79 / 83 | – | +0.11 / −0.23; −0.09 / +0.19 | opposite signs | HO | #34 |
| No bias, draw_dol strict, dol_weekly | NO EDGE | 96–450 | – | Δ −0.127 to +0.159 | ≤ 1.1 | HO, CFD | `reports/variants-*.md` |
| Opposite side of every trade (cf_flip) | CONSISTENT LOSER (but mis-specified, FF-108) | – | – | −0.89 / −0.39 / −0.19 / −0.12 | – | SEL, CFD | `direction-diagnosis` |
| **Gates** | | | | | | | |
| Cost gate ≤ 0.1 R (default) | PROMISING (protective) | 976 base | – | removing it Δ −0.160 | −2.4 | HO | `pd-return-variants` |
| news_blackout, flat through release, fomc_day | UNTESTED | – | – | – | – | – | pre-registered, no results file |
| PO3 daily / weekly opening price | UNTESTED | – | – | – | – | – | #8 |
| Entry quality (sweep-first, no chop, both) | NO EDGE | 43–843 | 22–36 | Δ −0.175 to +0.015 | −1.6 to +0.2 | HO | #11, 0 of 15 |
| Sweep-then-displacement on Silver Bullet | NO EDGE (hurts) | 364 | 26 | Δ −0.147 | −1.5 | HO | `entry-quality-results` |
| outside_daily_fvg | NO EDGE | 272 / 204 | 36 / 30 | Δ +0.052 / +0.012 | 0.4 / 0.1 | HO | #15 |
| Range in play: cheap half, 50 % limit | NO EDGE | 177–194 | 29–36 | Δ −0.038 to +0.057 | ≤ 0.4 | HO | #19 |
| invalidate_tf | NO EDGE | – | – | +0.008 / +0.029 / +0.015 | – | UN | sources disagree (below) |
| **Entries** | | | | | | | |
| 2022 model leg OTE 70.5 % | PROMISING | 84 of 304 | 30 | +0.419 (Δ +0.395) | 1.1 | HO | #19 |
| MMxM leg OTE 70.5 % | NO EDGE | 88 | 14 | −0.016 | 0.3 | HO | `range-in-play-results` |
| MMxM 5m entry (default) | PROMISING | 122 | 32 | Δ +0.256 | 1.4 | HO, CFD | `variants-mmxm` |
| Liquidity hold (near-equal), 2022 model | PROMISING (too rare) | 5 (12 in all, 9 won) | 100 | +1.31 | 2.8 | HO | #29 |
| IFVG flip after a failed model trade | NO EDGE | 20–327 | 28–39 | −0.245 to +0.240 | −0.9 to +1.9 | HO | #2 |
| Cameron far-edge flip | PROMISING (n < 30) | 26 | 65 | +0.871 | 2.3 | HO | `flip-results` |
| PD return failed-extreme flip | PROMISING | 327 | 32 | +0.240 | 1.9 | HO | `flip-results` |
| Market entry, 2022 model | NO EDGE | – | – | +0.024 | 0.8 | HO | `gap-sweep` §5 (the z 5.2 was retracted) |
| Nested FVG | NO EDGE | 102 / 51 | 37 / 29 | Δ 0.000 / −0.094 | 0.0 / −0.5 | HO | #14 |
| Timeframe ladder | NO EDGE | 126 / 28 / 22 | – | Δ −0.092 / −0.112 / +0.180 | ≤ 0.6 | HO | `timeframes-trail-results` |
| HTF OB as PD-return array | NO EDGE | 165–1,303 | 21–28 | Δ −0.130 to +0.003 | ≤ 0.0 | HO | #5 |
| HTF IFVG as PD-return array | NO EDGE (all negative) | 143–1,268 | 19–27 | Δ −0.235 to −0.097 | −1.8 to −0.7 | HO | #7 |
| OC retest (MMxM) | NO EDGE | 104 | 32 | −0.110 | −0.2 | HO | #30 |
| Counter-bias after the daily draw | NO EDGE | 60 / 122 days | 45 / 26 | +0.12 / +0.05 per day | 0.5 / 0.3 | HO | #22 |
| Re-entry v1, 2022 model | CONSISTENT LOSER (hold-out) | 33 | – | −0.44 (in-sample +0.10, n 93) | −2.56 | HO | #32 |
| Re-entry v2 | CONSISTENT LOSER | 22 | – | −0.56 | −2.44 | HO | #33 |
| Gravitation | NO EDGE | 401 calls | 77 vs 79 expected | – | −0.99 | HO | #31 |
| Order flow on NQ (H1 / H2 / H3) | NO EDGE | 404 / 1,242 / 827 | – | +7.4 pts / Δ −0.067 R / +1 pt | 1.43 / −0.54 / 0.17 | 2024 CME | `orderflow-results-NQ-2024` |
| Breaker entry, SMT, trendline liquidity, tapped POI, Judas, Unicorn, PO3 day, TGIF | UNTESTED | – | – | – | – | – | #13, #17, #23, #26; §5 |
| **Targets / stops** | | | | | | | |
| Pool runner, fvg_tp1, both, hold | NO EDGE | 292–976 | 28–37 | Δ −0.088 to +0.024 | ≤ 0.7 | HO | #4, #6, #9, #12 |
| eq_hold (TP1 at 50 % of the 4h range) | PROMISING (2022) / NO EDGE (MMxM) | 356 / 238 | 28 / 27 | Δ +0.191 / +0.025 | 1.2 / 0.2 | HO | #16 |
| 5m trailed runner | NO EDGE | 304 / 237 | – | Δ −0.093 / +0.036 | ≤ 0.7 | HO | `timeframes-trail-results` |
| HTF stop (15m / 1h swing) | NO EDGE | ≈ 300 / ≈ 230 | 52–59 / 42–47 | Δ −0.095, −0.072 / +0.086, +0.090 | ≤ 0.8 | HO | `htf-stop-results` |
| 1.5× wider stop | NO EDGE | – | – | −0.03 to 0.00 | – | SEL | `direction-diagnosis`, FF-107 |
| TP1 cap 2 R (default) | NO EDGE | – | – | −0.123 vs −0.139 uncapped | – | UN | `preregistered-2024H2-2026.md` |
| Small grab against htf40 / weekly structure | NO EDGE | 98 / 69; 115 / 83 | – | Δ −0.17 / +0.07; +0.03 / +0.07 | ≤ 1.4 | HO | #33, #34 |
| Named liquidity as targets (reach study) | NO EDGE | 886 + 562 | random-walk rates | – | – | SEL | `liquidity-reach` |
| **Engine plan (this sweep; strict win, net R, z on day totals)** | | | | | | | |
| Touch, range stop, multi-day, plan TP (baseline) | CONSISTENT LOSER | 732 | 6.7 | −0.148 | −3.7 | PLAN | §1 |
| Touch, any stop / TP / hold (28 cells × 3 partials) | CONSISTENT LOSER | 576–732 | 1–40 | −0.04 to −0.30 | −1.3 to −5.3 | PLAN | appendix |
| Support leg, stop beyond the zone (current default) | CONSISTENT LOSER | 460 | 4.8 | −0.144 | −1.4 | PLAN | §1 |
| Support leg, zone stop, day-only, any TP | CONSISTENT LOSER (small, every cell negative) | 304 | 1–24 | −0.038 to −0.070 | −0.6 to −1.2 | PLAN | appendix |
| Support leg, reaction stop, 1 R | NO EDGE | 460 / 304 | 53.0 / 46.7 | +0.065 / +0.028 | 0.7 / 0.5 | PLAN (multi / day) | §1 |
| Support leg, reaction stop, plan TP | NO EDGE (outlier-driven) | 460 | 3.7 | −0.014 (capped at 10 R −0.23) | −0.1 | PLAN | appendix |
| Displacement-qualified support (1.5× body) | NO EDGE (no different from plain) | 431 / 287 | 51.7 / 46.3 | +0.039 / +0.049 | 0.4 / 0.8 | PLAN | §1 |
| Flip leg, multi-day, plan TP | PROMISING (outlier-driven: −2.7 R without best 3) | 211 | 29.4 | +0.250 | 1.2 | PLAN | §1 |
| **Flip leg, day-only, 1 R** | PROMISING | 148 | 43.9 | +0.047 all out / +0.112 half | 0.6 / 1.1 | PLAN | §1 |
| **Flip leg, day-only, pool ≥ 0.5 R** | PROMISING | 148 | 25.7 | +0.242 | 1.5 | PLAN | §1 |
| Fast moves (touch / confirm / confirm+flip, old sim) | CONSISTENT LOSER | 159 / 95 / 144 | – | −0.432 / −0.453 / −0.316 | −7.1 / −3.9 / −2.7 | PLAN | `plans-sim.parquet` |
| 4H-range plans (confirm+flip / support, old sim) | CONSISTENT LOSER | 427 / 315 | – | −0.099 / −0.198 | −1.0 / −2.2 | PLAN | `plans-sim.parquet` |
| OB-sourced plans (all modes) | CONSISTENT LOSER (n 22–25) | 22–25 | – | −0.50 to −0.71 | −3.4 to −4.2 | PLAN | `plans-sim.parquet` |
| Daily-range plans, confirm+flip | PROMISING (weak) | 244 | – | +0.158 (capped +0.091) | 1.0 | PLAN | `plans-sim.parquet` |

### CONSISTENT LOSERS — stop using / drop

1. **Plan: touch fill at the array** — −0.148 R, n 732, strict win 6.7 %, z −3.7 (2022-03 → 2023-09); negative on all three indices and in all 84 touch cells of the sweep (best −0.04 R day-only, worst −0.30 R with the zone stop).
2. **Plan: support leg with the stop beyond the zone (the current default)** — −0.144 R, n 460, strict win 4.8 %; day-only −0.04 to −0.07 R in every TP rule (n 304).
3. **Plans on fast moves** — −0.32 to −0.45 R (n 95–159, z −2.7 to −7.1); **4H-range plans** −0.10 to −0.20 R (n 315–427); **OB-sourced plans** −0.50 to −0.71 R (n 22–25, small).
4. **2022 model, pooled** — −0.058 R (n 1,257, 34.4 % win, z −1.4) SEL and −0.122 R (n 1,562, 31.7 %, z −3.5) UN; US30 worst (−0.108 / −0.201, z −3.1), US100 negative in both.
5. **Cameron, pooled** — −0.099 R (n 2,134, 26.0 %, z −2.9) SEL and −0.069 R (n 2,540, 27.5 %, z −2.1) UN; US500 −0.163 / −0.154.
6. **The NY premarket window (07:00–09:30) for the 2022 model and Cameron** — −0.303 / −0.325 R SEL (n 186 / 279, z −3.3 / −4.2), −0.195 / −0.189 R UN (z −2.2 / −2.3).
7. **CRT 1h as a stand-alone trade** — −0.143 R, n 6,775, z −5.8 (HO).
8. **Re-entry after a stop-out, v1 and v2** — −0.44 R (n 33, z −2.56) and −0.56 R (n 22, z −2.44) on the hold-out.
9. **Flipping every model trade** — −0.12 to −0.89 R by model (note FF-108: this counterfactual is mis-specified; the direction of the result stands for the 2022 model only loosely).

Not consistent, so not on the list: Silver Bullet (flat SEL, −0.102 R UN), Cameron US100, MMxM XAUUSD, PD return XAGUSD (each significant in one period only).

### WORKS

**Empty.** Nearest, all below the bar: the cost gate ≤ 0.1 R (reduces losses, creates no edge); MMxM 5m entry (z 1.4 three times); 2022 model leg OTE 70.5 % (+0.42 R, z 1.1, n 84);
liquidity hold (+1.3 R, 12 trades in 2½ years); the plan flip leg (+0.05 to +0.24 R day-only, z ≤ 1.5, in-sample only, never run out of sample).

### Where sources disagree

- **invalidate_tf:** CLAUDE.md says it "was tested and hurt"; on UN it was slightly better in all three models (+0.008 / +0.029 / +0.015 R) and the pre-registered claim that it hurts failed.
- **Baselines differ by metric:** 2022 model hold-out −0.044 R all-out at TP1, +0.023 R with the runner; MMxM −0.015 and −0.077.
- **Review log #35 vs the parquet:** the log's "confirm 460 trades, 11 % win, +4 R" is now mode `confirm_reaction`; `confirm` holds the zone stop (−61.6 R), as #36 says. Both "win" figures are "closed in profit" (FF-01).
- **Market entry:** `gap-sweep` §3 reported +0.095 R at z 5.2; §5 of the same file retracts it.
- **CFD vs futures:** the 2022 model in SEL is +0.036 R on CFD (n 427) and −0.058 R on futures; futures decides.

## 7. FABLES_FINDINGS — what went wrong in the existing runs

Also in `research/sweeps/FABLES_FINDINGS.md` (one item per heading; `grep -rn FABLES_FINDINGS research/sweeps`).

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

## Appendix — full grid (half off / all out at TP1; 75 % rows in `reports/plans-sweep.parquet`)

Net R. `flip` does not depend on the support stop, so it is listed once (under `zone`).

| entry leg | stop | hold | TP1 | off at TP1 | n | win % [Wilson 95] | mean R | total R | w/o best 3 | capped 10 | z | z (day totals) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| touch | range | multi | 1.5R | 0.5 | 732 | 11.3 [9–14] | -0.135 | -98.6 | -107.2 | -98.6 | -4.38 | -3.67 |
| touch | range | multi | 1.5R | 1 | 732 | 11.3 [9–14] | -0.127 | -92.9 | -97.4 | -92.9 | -4.16 | -3.55 |
| touch | range | multi | 1R | 0.5 | 732 | 18.6 [16–22] | -0.142 | -104.2 | -112.1 | -104.2 | -4.99 | -4.15 |
| touch | range | multi | 1R | 1 | 732 | 18.6 [16–22] | -0.143 | -104.8 | -107.8 | -104.8 | -5.24 | -4.39 |
| touch | range | multi | 2R | 0.5 | 732 | 7.4 [6–10] | -0.129 | -94.6 | -106.7 | -94.6 | -3.88 | -3.24 |
| touch | range | multi | 2R | 1 | 732 | 7.4 [6–10] | -0.128 | -93.8 | -99.8 | -93.8 | -3.93 | -3.31 |
| touch | range | multi | 3R | 0.5 | 732 | 3.4 [2–5] | -0.127 | -93.0 | -106.6 | -93.0 | -3.58 | -3.03 |
| touch | range | multi | 3R | 1 | 732 | 3.4 [2–5] | -0.120 | -88.2 | -97.2 | -88.2 | -3.38 | -2.87 |
| touch | range | multi | plan | 0.5 | 732 | 6.7 [5–9] | -0.148 | -108.5 | -123.9 | -108.5 | -4.35 | -3.68 |
| touch | range | multi | plan | 1 | 732 | 6.7 [5–9] | -0.154 | -112.8 | -127.8 | -112.8 | -4.60 | -3.92 |
| touch | range | multi | pool | 0.5 | 732 | 9.2 [7–12] | -0.134 | -97.8 | -111.5 | -97.8 | -4.06 | -3.38 |
| touch | range | multi | pool | 1 | 732 | 9.2 [7–12] | -0.134 | -98.0 | -108.4 | -98.0 | -4.16 | -3.47 |
| touch | range | multi | pool05 | 0.5 | 732 | 19.7 [17–23] | -0.136 | -99.8 | -112.1 | -99.8 | -4.46 | -3.76 |
| touch | range | multi | pool05 | 1 | 732 | 19.7 [17–23] | -0.140 | -102.5 | -111.3 | -102.5 | -4.78 | -4.05 |
| touch | range | day | 1.5R | 0.5 | 576 | 3.6 [2–6] | -0.041 | -23.4 | -34.9 | -23.4 | -1.65 | -1.42 |
| touch | range | day | 1.5R | 1 | 576 | 3.6 [2–6] | -0.050 | -28.7 | -33.2 | -28.7 | -2.27 | -1.93 |
| touch | range | day | 1R | 0.5 | 576 | 6.6 [5–9] | -0.046 | -26.6 | -37.3 | -26.6 | -1.98 | -1.73 |
| touch | range | day | 1R | 1 | 576 | 6.6 [5–9] | -0.059 | -34.3 | -37.3 | -34.3 | -2.97 | -2.54 |
| touch | range | day | 2R | 0.5 | 576 | 2.1 [1–4] | -0.044 | -25.4 | -37.7 | -25.4 | -1.73 | -1.48 |
| touch | range | day | 2R | 1 | 576 | 2.1 [1–4] | -0.054 | -31.1 | -37.1 | -31.1 | -2.37 | -1.98 |
| touch | range | day | 3R | 0.5 | 576 | 1.2 [1–2] | -0.040 | -23.3 | -37.0 | -23.3 | -1.49 | -1.27 |
| touch | range | day | 3R | 1 | 576 | 1.2 [1–2] | -0.047 | -27.2 | -36.1 | -27.2 | -1.89 | -1.57 |
| touch | range | day | plan | 0.5 | 576 | 1.9 [1–3] | -0.041 | -23.4 | -39.5 | -23.4 | -1.41 | -1.27 |
| touch | range | day | plan | 1 | 576 | 1.9 [1–3] | -0.044 | -25.4 | -41.3 | -25.4 | -1.55 | -1.43 |
| touch | range | day | pool | 0.5 | 576 | 3.0 [2–5] | -0.041 | -23.7 | -37.5 | -23.7 | -1.56 | -1.35 |
| touch | range | day | pool | 1 | 576 | 3.0 [2–5] | -0.047 | -27.0 | -36.8 | -27.0 | -1.92 | -1.62 |
| touch | range | day | pool05 | 0.5 | 576 | 6.1 [4–8] | -0.043 | -25.0 | -37.5 | -25.0 | -1.74 | -1.52 |
| touch | range | day | pool05 | 1 | 576 | 6.1 [4–8] | -0.053 | -30.5 | -38.9 | -30.5 | -2.37 | -2.06 |
| touch | zone | multi | 1.5R | 0.5 | 732 | 28.8 [26–32] | -0.258 | -188.6 | -211.0 | -188.6 | -5.35 | -4.74 |
| touch | zone | multi | 1.5R | 1 | 732 | 28.8 [26–32] | -0.227 | -166.5 | -171.0 | -166.5 | -5.45 | -4.67 |
| touch | zone | multi | 1R | 0.5 | 732 | 39.8 [36–43] | -0.223 | -163.4 | -185.1 | -163.4 | -5.19 | -4.65 |
| touch | zone | multi | 1R | 1 | 732 | 39.8 [36–43] | -0.189 | -138.4 | -141.4 | -138.4 | -5.27 | -4.57 |
| touch | zone | multi | 2R | 0.5 | 732 | 21.3 [18–24] | -0.296 | -216.8 | -240.0 | -216.8 | -5.81 | -5.18 |
| touch | zone | multi | 2R | 1 | 732 | 21.3 [18–24] | -0.269 | -196.7 | -202.7 | -196.7 | -5.88 | -5.13 |
| touch | zone | multi | 3R | 0.5 | 732 | 14.5 [12–17] | -0.255 | -186.4 | -215.9 | -188.8 | -4.24 | -3.72 |
| touch | zone | multi | 3R | 1 | 732 | 14.5 [12–17] | -0.240 | -176.0 | -185.0 | -176.0 | -4.47 | -3.96 |
| touch | zone | multi | plan | 0.5 | 732 | 4.0 [3–6] | -0.253 | -185.0 | -244.2 | -228.0 | -2.94 | -2.49 |
| touch | zone | multi | plan | 1 | 732 | 4.0 [3–6] | -0.267 | -195.5 | -252.2 | -232.1 | -3.21 | -2.74 |
| touch | zone | multi | pool | 0.5 | 732 | 16.9 [14–20] | -0.295 | -216.2 | -254.6 | -224.6 | -4.78 | -4.18 |
| touch | zone | multi | pool | 1 | 732 | 16.9 [14–20] | -0.283 | -207.1 | -242.6 | -213.1 | -4.82 | -4.30 |
| touch | zone | multi | pool05 | 0.5 | 732 | 24.5 [22–28] | -0.266 | -195.0 | -233.3 | -203.3 | -4.39 | -3.87 |
| touch | zone | multi | pool05 | 1 | 732 | 24.5 [22–28] | -0.255 | -186.8 | -222.3 | -192.8 | -4.47 | -4.04 |
| touch | zone | day | 1.5R | 0.5 | 576 | 17.7 [15–21] | -0.178 | -102.7 | -118.1 | -102.7 | -4.11 | -3.59 |
| touch | zone | day | 1.5R | 1 | 576 | 17.7 [15–21] | -0.173 | -99.4 | -103.9 | -99.4 | -4.28 | -3.76 |
| touch | zone | day | 1R | 0.5 | 576 | 30.2 [27–34] | -0.137 | -79.1 | -93.7 | -79.1 | -3.46 | -3.01 |
| touch | zone | day | 1R | 1 | 576 | 30.2 [27–34] | -0.124 | -71.5 | -74.5 | -71.5 | -3.45 | -3.05 |
| touch | zone | day | 2R | 0.5 | 576 | 12.3 [10–15] | -0.180 | -103.7 | -119.9 | -103.7 | -3.90 | -3.47 |
| touch | zone | day | 2R | 1 | 576 | 12.3 [10–15] | -0.180 | -103.6 | -109.6 | -103.6 | -4.14 | -3.71 |
| touch | zone | day | 3R | 0.5 | 576 | 6.6 [5–9] | -0.176 | -101.3 | -118.9 | -101.3 | -3.54 | -3.20 |
| touch | zone | day | 3R | 1 | 576 | 6.6 [5–9] | -0.165 | -95.3 | -104.2 | -95.3 | -3.39 | -3.14 |
| touch | zone | day | plan | 0.5 | 576 | 1.2 [1–2] | -0.193 | -111.2 | -136.2 | -112.6 | -3.54 | -3.16 |
| touch | zone | day | plan | 1 | 576 | 1.2 [1–2] | -0.195 | -112.4 | -137.3 | -113.7 | -3.60 | -3.25 |
| touch | zone | day | pool | 0.5 | 576 | 9.9 [8–13] | -0.194 | -111.7 | -129.2 | -111.7 | -3.98 | -3.55 |
| touch | zone | day | pool | 1 | 576 | 9.9 [8–13] | -0.196 | -112.7 | -129.6 | -112.7 | -4.14 | -3.72 |
| touch | zone | day | pool05 | 0.5 | 576 | 19.1 [16–22] | -0.191 | -109.9 | -127.4 | -109.9 | -4.03 | -3.56 |
| touch | zone | day | pool05 | 1 | 576 | 19.1 [16–22] | -0.195 | -112.0 | -128.9 | -112.0 | -4.27 | -3.81 |
| support | reaction | multi | 1.5R | 0.5 | 460 | 41.7 [37–46] | +0.075 | +34.5 | -7.2 | +18.4 | +0.78 | +0.69 |
| support | reaction | multi | 1.5R | 1 | 460 | 41.7 [37–46] | +0.024 | +10.8 | +6.3 | +10.8 | +0.41 | +0.39 |
| support | reaction | multi | 1R | 0.5 | 460 | 53.0 [48–58] | +0.065 | +30.0 | -10.1 | +18.7 | +0.79 | +0.70 |
| support | reaction | multi | 1R | 1 | 460 | 53.0 [48–58] | +0.039 | +18.0 | +15.0 | +18.0 | +0.84 | +0.79 |
| support | reaction | multi | 2R | 0.5 | 460 | 33.3 [29–38] | +0.043 | +20.0 | -22.5 | +2.4 | +0.42 | +0.38 |
| support | reaction | multi | 2R | 1 | 460 | 33.3 [29–38] | -0.014 | -6.6 | -12.6 | -6.6 | -0.22 | -0.20 |
| support | reaction | multi | 3R | 0.5 | 460 | 23.7 [20–28] | +0.022 | +10.2 | -33.7 | -10.9 | +0.20 | +0.18 |
| support | reaction | multi | 3R | 1 | 460 | 23.7 [20–28] | -0.046 | -21.2 | -30.2 | -21.2 | -0.58 | -0.52 |
| support | reaction | multi | plan | 0.5 | 460 | 3.7 [2–6] | -0.014 | -6.6 | -83.8 | -106.8 | -0.09 | -0.08 |
| support | reaction | multi | plan | 1 | 460 | 3.7 [2–6] | -0.034 | -15.7 | -92.0 | -112.0 | -0.21 | -0.19 |
| support | reaction | multi | pool | 0.5 | 460 | 20.4 [17–24] | -0.005 | -2.4 | -68.3 | -54.0 | -0.04 | -0.04 |
| support | reaction | multi | pool | 1 | 460 | 20.4 [17–24] | -0.032 | -14.6 | -79.0 | -49.0 | -0.27 | -0.26 |
| support | reaction | multi | pool05 | 0.5 | 460 | 23.3 [20–27] | +0.004 | +1.6 | -64.2 | -49.9 | +0.03 | +0.02 |
| support | reaction | multi | pool05 | 1 | 460 | 23.3 [20–27] | -0.026 | -11.9 | -76.3 | -46.3 | -0.22 | -0.22 |
| support | reaction | day | 1.5R | 0.5 | 304 | 34.2 [29–40] | -0.031 | -9.5 | -26.7 | -9.5 | -0.43 | -0.39 |
| support | reaction | day | 1.5R | 1 | 304 | 34.2 [29–40] | -0.002 | -0.7 | -5.2 | -0.7 | -0.03 | -0.03 |
| support | reaction | day | 1R | 0.5 | 304 | 46.7 [41–52] | -0.022 | -6.6 | -19.6 | -6.6 | -0.36 | -0.33 |
| support | reaction | day | 1R | 1 | 304 | 46.7 [41–52] | +0.028 | +8.5 | +5.5 | +8.5 | +0.51 | +0.48 |
| support | reaction | day | 2R | 0.5 | 304 | 23.7 [19–29] | -0.061 | -18.5 | -36.4 | -18.5 | -0.76 | -0.69 |
| support | reaction | day | 2R | 1 | 304 | 23.7 [19–29] | -0.057 | -17.4 | -23.4 | -17.4 | -0.79 | -0.72 |
| support | reaction | day | 3R | 0.5 | 304 | 14.5 [11–19] | -0.035 | -10.8 | -30.2 | -10.8 | -0.40 | -0.36 |
| support | reaction | day | 3R | 1 | 304 | 14.5 [11–19] | -0.030 | -9.0 | -18.0 | -9.0 | -0.35 | -0.32 |
| support | reaction | day | plan | 0.5 | 304 | 0.3 [0–2] | -0.062 | -18.7 | -48.7 | -21.6 | -0.59 | -0.54 |
| support | reaction | day | plan | 1 | 304 | 0.3 [0–2] | -0.066 | -20.2 | -50.2 | -23.1 | -0.64 | -0.59 |
| support | reaction | day | pool | 0.5 | 304 | 17.1 [13–22] | -0.027 | -8.3 | -31.9 | -8.3 | -0.30 | -0.28 |
| support | reaction | day | pool | 1 | 304 | 17.1 [13–22] | -0.016 | -4.7 | -25.1 | -4.7 | -0.18 | -0.17 |
| support | reaction | day | pool05 | 0.5 | 304 | 21.1 [17–26] | -0.035 | -10.6 | -33.9 | -10.6 | -0.40 | -0.36 |
| support | reaction | day | pool05 | 1 | 304 | 21.1 [17–26] | -0.022 | -6.8 | -25.8 | -6.8 | -0.27 | -0.25 |
| support | zone | multi | 1.5R | 0.5 | 460 | 31.5 [27–36] | -0.110 | -50.6 | -75.5 | -50.7 | -1.70 | -1.50 |
| support | zone | multi | 1.5R | 1 | 460 | 31.5 [27–36] | -0.110 | -50.4 | -54.9 | -50.4 | -2.05 | -1.88 |
| support | zone | multi | 1R | 0.5 | 460 | 45.2 [41–50] | -0.056 | -25.7 | -49.9 | -25.7 | -0.95 | -0.82 |
| support | zone | multi | 1R | 1 | 460 | 45.2 [41–50] | -0.052 | -24.0 | -27.0 | -24.0 | -1.15 | -1.07 |
| support | zone | multi | 2R | 0.5 | 460 | 22.4 [19–26] | -0.123 | -56.6 | -82.3 | -56.9 | -1.75 | -1.54 |
| support | zone | multi | 2R | 1 | 460 | 22.4 [19–26] | -0.147 | -67.5 | -73.5 | -67.5 | -2.49 | -2.25 |
| support | zone | multi | 3R | 0.5 | 460 | 13.9 [11–17] | -0.127 | -58.6 | -85.8 | -59.4 | -1.66 | -1.47 |
| support | zone | multi | 3R | 1 | 460 | 13.9 [11–17] | -0.144 | -66.2 | -75.2 | -66.2 | -2.11 | -1.94 |
| support | zone | multi | plan | 0.5 | 460 | 4.8 [3–7] | -0.144 | -66.3 | -108.2 | -78.2 | -1.57 | -1.35 |
| support | zone | multi | plan | 1 | 460 | 4.8 [3–7] | -0.163 | -74.8 | -113.2 | -83.2 | -1.85 | -1.59 |
| support | zone | multi | pool | 0.5 | 460 | 20.9 [17–25] | -0.096 | -44.1 | -72.9 | -45.0 | -1.23 | -1.09 |
| support | zone | multi | pool | 1 | 460 | 20.9 [17–25] | -0.089 | -40.8 | -65.6 | -40.8 | -1.25 | -1.15 |
| support | zone | multi | pool05 | 0.5 | 460 | 29.1 [25–33] | -0.089 | -41.1 | -69.7 | -41.9 | -1.22 | -1.07 |
| support | zone | multi | pool05 | 1 | 460 | 29.1 [25–33] | -0.104 | -47.7 | -71.3 | -47.7 | -1.61 | -1.48 |
| support | zone | day | 1.5R | 0.5 | 304 | 13.2 [10–17] | -0.045 | -13.7 | -20.9 | -13.7 | -0.91 | -0.83 |
| support | zone | day | 1.5R | 1 | 304 | 13.2 [10–17] | -0.038 | -11.5 | -16.0 | -11.5 | -0.77 | -0.70 |
| support | zone | day | 1R | 0.5 | 304 | 24.3 [20–30] | -0.055 | -16.8 | -23.2 | -16.8 | -1.21 | -1.08 |
| support | zone | day | 1R | 1 | 304 | 24.3 [20–30] | -0.046 | -13.9 | -16.9 | -13.9 | -1.03 | -0.91 |
| support | zone | day | 2R | 0.5 | 304 | 7.9 [5–12] | -0.052 | -15.9 | -23.8 | -15.9 | -1.01 | -0.92 |
| support | zone | day | 2R | 1 | 304 | 7.9 [5–12] | -0.046 | -14.0 | -20.0 | -14.0 | -0.89 | -0.82 |
| support | zone | day | 3R | 0.5 | 304 | 3.3 [2–6] | -0.050 | -15.2 | -24.6 | -15.2 | -0.93 | -0.85 |
| support | zone | day | 3R | 1 | 304 | 3.3 [2–6] | -0.038 | -11.6 | -20.6 | -11.6 | -0.69 | -0.63 |
| support | zone | day | plan | 0.5 | 304 | 1.0 [0–3] | -0.066 | -20.1 | -29.5 | -20.1 | -1.26 | -1.16 |
| support | zone | day | plan | 1 | 304 | 1.0 [0–3] | -0.070 | -21.2 | -30.6 | -21.2 | -1.34 | -1.24 |
| support | zone | day | pool | 0.5 | 304 | 8.6 [6–12] | -0.049 | -15.0 | -24.1 | -15.0 | -0.96 | -0.87 |
| support | zone | day | pool | 1 | 304 | 8.6 [6–12] | -0.046 | -13.9 | -22.8 | -13.9 | -0.90 | -0.81 |
| support | zone | day | pool05 | 0.5 | 304 | 20.4 [16–25] | -0.045 | -13.8 | -22.9 | -13.8 | -0.95 | -0.84 |
| support | zone | day | pool05 | 1 | 304 | 20.4 [16–25] | -0.042 | -12.6 | -21.2 | -12.6 | -0.89 | -0.79 |
| support_disp | reaction | multi | 1.5R | 0.5 | 431 | 40.4 [36–45] | +0.009 | +3.8 | -31.9 | -2.5 | +0.10 | +0.09 |
| support_disp | reaction | multi | 1.5R | 1 | 431 | 40.4 [36–45] | -0.009 | -3.7 | -8.2 | -3.7 | -0.15 | -0.14 |
| support_disp | reaction | multi | 1R | 0.5 | 431 | 51.7 [47–56] | +0.039 | +16.8 | -18.2 | +11.5 | +0.48 | +0.44 |
| support_disp | reaction | multi | 1R | 1 | 431 | 51.7 [47–56] | +0.017 | +7.3 | +4.3 | +7.3 | +0.35 | +0.33 |
| support_disp | reaction | multi | 2R | 0.5 | 431 | 31.1 [27–36] | -0.056 | -24.0 | -60.5 | -31.5 | -0.59 | -0.55 |
| support_disp | reaction | multi | 2R | 1 | 431 | 31.1 [27–36] | -0.081 | -34.8 | -40.8 | -34.8 | -1.21 | -1.12 |
| support_disp | reaction | multi | 3R | 0.5 | 431 | 23.2 [20–27] | -0.048 | -20.5 | -58.5 | -30.5 | -0.46 | -0.42 |
| support_disp | reaction | multi | 3R | 1 | 431 | 23.2 [20–27] | -0.066 | -28.4 | -37.4 | -28.4 | -0.81 | -0.74 |
| support_disp | reaction | multi | plan | 0.5 | 431 | 3.5 [2–6] | -0.113 | -48.8 | -113.6 | -111.5 | -0.75 | -0.70 |
| support_disp | reaction | multi | plan | 1 | 431 | 3.5 [2–6] | -0.129 | -55.5 | -118.8 | -116.7 | -0.87 | -0.81 |
| support_disp | reaction | multi | pool | 0.5 | 431 | 20.9 [17–25] | -0.068 | -29.3 | -89.8 | -64.1 | -0.55 | -0.52 |
| support_disp | reaction | multi | pool | 1 | 431 | 20.9 [17–25] | -0.050 | -21.7 | -82.3 | -52.3 | -0.44 | -0.42 |
| support_disp | reaction | multi | pool05 | 0.5 | 431 | 24.4 [20–29] | -0.045 | -19.5 | -80.0 | -54.3 | -0.37 | -0.35 |
| support_disp | reaction | multi | pool05 | 1 | 431 | 24.4 [20–29] | -0.031 | -13.4 | -73.9 | -43.9 | -0.27 | -0.26 |
| support_disp | reaction | day | 1.5R | 0.5 | 287 | 32.1 [27–38] | -0.011 | -3.3 | -18.8 | -3.3 | -0.16 | -0.14 |
| support_disp | reaction | day | 1.5R | 1 | 287 | 32.1 [27–38] | +0.012 | +3.6 | -0.9 | +3.6 | +0.19 | +0.17 |
| support_disp | reaction | day | 1R | 0.5 | 287 | 46.3 [41–52] | +0.023 | +6.7 | -8.1 | +6.7 | +0.36 | +0.33 |
| support_disp | reaction | day | 1R | 1 | 287 | 46.3 [41–52] | +0.049 | +14.0 | +11.0 | +14.0 | +0.88 | +0.82 |
| support_disp | reaction | day | 2R | 0.5 | 287 | 21.6 [17–27] | -0.034 | -9.7 | -26.0 | -9.7 | -0.43 | -0.38 |
| support_disp | reaction | day | 2R | 1 | 287 | 21.6 [17–27] | -0.036 | -10.2 | -16.2 | -10.2 | -0.49 | -0.44 |
| support_disp | reaction | day | 3R | 0.5 | 287 | 12.9 [10–17] | -0.017 | -4.9 | -22.6 | -4.9 | -0.20 | -0.18 |
| support_disp | reaction | day | 3R | 1 | 287 | 12.9 [10–17] | -0.007 | -2.1 | -11.1 | -2.1 | -0.09 | -0.08 |
| support_disp | reaction | day | plan | 0.5 | 287 | 0.3 [0–2] | -0.038 | -10.9 | -37.4 | -10.9 | -0.38 | -0.34 |
| support_disp | reaction | day | plan | 1 | 287 | 0.3 [0–2] | -0.043 | -12.3 | -38.9 | -12.3 | -0.44 | -0.39 |
| support_disp | reaction | day | pool | 0.5 | 287 | 16.0 [12–21] | -0.019 | -5.4 | -26.2 | -5.4 | -0.22 | -0.20 |
| support_disp | reaction | day | pool | 1 | 287 | 16.0 [12–21] | -0.016 | -4.5 | -23.0 | -4.5 | -0.19 | -0.18 |
| support_disp | reaction | day | pool05 | 0.5 | 287 | 21.3 [17–26] | -0.004 | -1.2 | -22.0 | -1.2 | -0.05 | -0.04 |
| support_disp | reaction | day | pool05 | 1 | 287 | 21.3 [17–26] | -0.001 | -0.4 | -18.9 | -0.4 | -0.02 | -0.02 |
| support_disp | zone | multi | 1.5R | 0.5 | 431 | 31.6 [27–36] | -0.116 | -50.0 | -72.2 | -50.1 | -1.82 | -1.62 |
| support_disp | zone | multi | 1.5R | 1 | 431 | 31.6 [27–36] | -0.095 | -41.1 | -45.6 | -41.1 | -1.73 | -1.58 |
| support_disp | zone | multi | 1R | 0.5 | 431 | 45.2 [41–50] | -0.068 | -29.5 | -51.0 | -29.5 | -1.20 | -1.07 |
| support_disp | zone | multi | 1R | 1 | 431 | 45.2 [41–50] | -0.044 | -19.0 | -22.0 | -19.0 | -0.94 | -0.87 |
| support_disp | zone | multi | 2R | 0.5 | 431 | 22.0 [18–26] | -0.154 | -66.5 | -89.5 | -66.9 | -2.26 | -1.98 |
| support_disp | zone | multi | 2R | 1 | 431 | 22.0 [18–26] | -0.155 | -66.8 | -72.8 | -66.8 | -2.57 | -2.28 |
| support_disp | zone | multi | 3R | 0.5 | 431 | 13.5 [11–17] | -0.155 | -66.8 | -91.4 | -67.7 | -2.08 | -1.84 |
| support_disp | zone | multi | 3R | 1 | 431 | 13.5 [11–17] | -0.146 | -63.1 | -72.0 | -63.1 | -2.10 | -1.91 |
| support_disp | zone | multi | plan | 0.5 | 431 | 4.6 [3–7] | -0.183 | -78.8 | -115.4 | -87.1 | -2.13 | -1.84 |
| support_disp | zone | multi | plan | 1 | 431 | 4.6 [3–7] | -0.200 | -86.0 | -119.2 | -91.1 | -2.44 | -2.11 |
| support_disp | zone | multi | pool | 0.5 | 431 | 20.9 [17–25] | -0.136 | -58.5 | -82.6 | -59.4 | -1.89 | -1.66 |
| support_disp | zone | multi | pool | 1 | 431 | 20.9 [17–25] | -0.120 | -51.7 | -67.6 | -51.7 | -1.82 | -1.63 |
| support_disp | zone | multi | pool05 | 0.5 | 431 | 29.9 [26–34] | -0.126 | -54.3 | -78.3 | -55.1 | -1.85 | -1.64 |
| support_disp | zone | multi | pool05 | 1 | 431 | 29.9 [26–34] | -0.125 | -53.9 | -69.8 | -53.9 | -2.07 | -1.88 |
| support_disp | zone | day | 1.5R | 0.5 | 287 | 11.8 [9–16] | -0.026 | -7.6 | -14.7 | -7.6 | -0.54 | -0.49 |
| support_disp | zone | day | 1.5R | 1 | 287 | 11.8 [9–16] | -0.022 | -6.3 | -10.8 | -6.3 | -0.45 | -0.41 |
| support_disp | zone | day | 1R | 0.5 | 287 | 23.0 [18–28] | -0.043 | -12.2 | -18.5 | -12.2 | -0.93 | -0.84 |
| support_disp | zone | day | 1R | 1 | 287 | 23.0 [18–28] | -0.034 | -9.9 | -12.9 | -9.9 | -0.78 | -0.69 |
| support_disp | zone | day | 2R | 0.5 | 287 | 5.9 [4–9] | -0.041 | -11.8 | -19.7 | -11.8 | -0.81 | -0.74 |
| support_disp | zone | day | 2R | 1 | 287 | 5.9 [4–9] | -0.045 | -12.9 | -18.8 | -12.9 | -0.90 | -0.82 |
| support_disp | zone | day | 3R | 0.5 | 287 | 2.4 [1–5] | -0.033 | -9.4 | -18.7 | -9.4 | -0.62 | -0.56 |
| support_disp | zone | day | 3R | 1 | 287 | 2.4 [1–5] | -0.028 | -7.9 | -16.9 | -7.9 | -0.52 | -0.47 |
| support_disp | zone | day | plan | 0.5 | 287 | 1.0 [0–3] | -0.045 | -13.0 | -22.0 | -13.0 | -0.87 | -0.80 |
| support_disp | zone | day | plan | 1 | 287 | 1.0 [0–3] | -0.049 | -14.1 | -23.0 | -14.1 | -0.96 | -0.89 |
| support_disp | zone | day | pool | 0.5 | 287 | 8.0 [5–12] | -0.031 | -9.0 | -18.0 | -9.0 | -0.62 | -0.56 |
| support_disp | zone | day | pool | 1 | 287 | 8.0 [5–12] | -0.031 | -8.8 | -17.7 | -8.8 | -0.62 | -0.55 |
| support_disp | zone | day | pool05 | 0.5 | 287 | 19.2 [15–24] | -0.031 | -9.0 | -18.0 | -9.0 | -0.66 | -0.59 |
| support_disp | zone | day | pool05 | 1 | 287 | 19.2 [15–24] | -0.032 | -9.2 | -17.6 | -9.2 | -0.69 | -0.61 |
| flip | zone | multi | 1.5R | 0.5 | 211 | 43.1 [37–50] | +0.103 | +21.7 | -3.0 | +18.8 | +0.89 | +0.86 |
| flip | zone | multi | 1.5R | 1 | 211 | 43.1 [37–50] | +0.076 | +16.0 | +11.5 | +16.0 | +0.89 | +0.86 |
| flip | zone | multi | 1R | 0.5 | 211 | 53.1 [46–60] | +0.093 | +19.6 | -4.4 | +16.9 | +0.89 | +0.84 |
| flip | zone | multi | 1R | 1 | 211 | 53.1 [46–60] | +0.037 | +7.8 | +4.8 | +7.8 | +0.54 | +0.52 |
| flip | zone | multi | 2R | 0.5 | 211 | 32.2 [26–39] | +0.091 | +19.2 | -11.9 | +15.5 | +0.68 | +0.63 |
| flip | zone | multi | 2R | 1 | 211 | 32.2 [26–39] | +0.007 | +1.5 | -4.5 | +1.5 | +0.07 | +0.07 |
| flip | zone | multi | 3R | 0.5 | 211 | 27.0 [22–33] | +0.197 | +41.5 | +8.9 | +36.8 | +1.32 | +1.21 |
| flip | zone | multi | 3R | 1 | 211 | 27.0 [22–33] | +0.165 | +34.8 | +25.8 | +34.8 | +1.35 | +1.24 |
| flip | zone | multi | plan | 0.5 | 211 | 29.4 [24–36] | +0.250 | +52.7 | -2.7 | +27.3 | +1.30 | +1.22 |
| flip | zone | multi | plan | 1 | 211 | 29.4 [24–36] | +0.228 | +48.2 | +2.6 | +28.4 | +1.30 | +1.22 |
| flip | zone | multi | pool | 0.5 | 211 | 28.9 [23–35] | +0.252 | +53.2 | -2.2 | +27.8 | +1.31 | +1.23 |
| flip | zone | multi | pool | 1 | 211 | 28.9 [23–35] | +0.221 | +46.6 | +1.0 | +26.8 | +1.27 | +1.18 |
| flip | zone | multi | pool05 | 0.5 | 211 | 33.6 [28–40] | +0.243 | +51.2 | -4.3 | +25.7 | +1.28 | +1.20 |
| flip | zone | multi | pool05 | 1 | 211 | 33.6 [28–40] | +0.202 | +42.7 | -2.9 | +22.9 | +1.18 | +1.11 |
| flip | zone | day | 1.5R | 0.5 | 148 | 30.4 [24–38] | +0.121 | +17.9 | +5.8 | +17.9 | +1.13 | +1.07 |
| flip | zone | day | 1.5R | 1 | 148 | 30.4 [24–38] | +0.052 | +7.7 | +3.2 | +7.7 | +0.58 | +0.56 |
| flip | zone | day | 1R | 0.5 | 148 | 43.9 [36–52] | +0.112 | +16.6 | +5.4 | +16.6 | +1.20 | +1.14 |
| flip | zone | day | 1R | 1 | 148 | 43.9 [36–52] | +0.047 | +7.0 | +4.0 | +7.0 | +0.62 | +0.63 |
| flip | zone | day | 2R | 0.5 | 148 | 23.6 [18–31] | +0.147 | +21.8 | +6.0 | +21.8 | +1.18 | +1.10 |
| flip | zone | day | 2R | 1 | 148 | 23.6 [18–31] | +0.062 | +9.2 | +3.3 | +9.2 | +0.61 | +0.59 |
| flip | zone | day | 3R | 0.5 | 148 | 16.2 [11–23] | +0.174 | +25.8 | +8.5 | +25.8 | +1.27 | +1.16 |
| flip | zone | day | 3R | 1 | 148 | 16.2 [11–23] | +0.127 | +18.8 | +9.8 | +18.8 | +1.04 | +0.96 |
| flip | zone | day | plan | 0.5 | 148 | 20.3 [15–28] | +0.225 | +33.3 | +9.7 | +31.5 | +1.52 | +1.40 |
| flip | zone | day | plan | 1 | 148 | 20.3 [15–28] | +0.221 | +32.6 | +11.0 | +30.9 | +1.53 | +1.42 |
| flip | zone | day | pool | 0.5 | 148 | 20.3 [15–28] | +0.225 | +33.3 | +9.7 | +31.5 | +1.52 | +1.40 |
| flip | zone | day | pool | 1 | 148 | 20.3 [15–28] | +0.221 | +32.6 | +11.0 | +30.9 | +1.53 | +1.42 |
| flip | zone | day | pool05 | 0.5 | 148 | 25.7 [19–33] | +0.242 | +35.8 | +12.2 | +34.0 | +1.65 | +1.52 |
| flip | zone | day | pool05 | 1 | 148 | 25.7 [19–33] | +0.240 | +35.6 | +13.9 | +33.8 | +1.70 | +1.57 |

## Files changed

- `research/scripts/plan_build.py` — options only, defaults unchanged: `day_window`, `zone_stop`, `replay(day_only, stop_at, manage_fn)`, `manage(partial)`, `_limit(last)`, `replay_confirm(day_only, min_rr, min_disp, manage_fn)`
- `research/scripts/plan_sweep.py` — new: the sweep, `manage_np`, `tp1_price`, `excursions`, `stats`
- `tests/test_plan_day.py` — new: 15 tests on hand-built candles
- `research/sweeps/2026-11-16-winrate-sweep.md`, `research/sweeps/FABLES_FINDINGS.md` — this write-up
- `reports/plans-sweep.parquet`, `reports/plans-sweep-fills.parquet` — sweep output; `reports/plans-sim.parquet` regenerated by `--sim` with identical numbers
