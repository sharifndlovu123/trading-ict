# Task list — session of 2026-11-16 (Sharif away; machine off when all done)

Goal: ≥ 50% win rate (TP1 before the stop) with positive R, day-only holds, proven on data never used for selection. Free data only. Every change through the change gate; every result through the pipelines (`.claude/skills/pipelines`).

Status: ☐ open · ◐ running · ☑ done · ✗ dropped

## A. Activity gate (hunt when price is moving)
- ☑ A1 Build `min_activity` as an option, off by default (tests first, suite 506 passed)
- ☑ A2 In-sample variant run (decision-time gate): weak — 2022 model −0.066 → −0.059 R (2 of 3 indices, removed trades −0.16 R, z −0.75); MMxM worse; silver bullet unchanged
- ☑ A3 Decision: the decision-time gate is NOT taken to 2021 (too weak; the clean year is kept)
- ☑ A3b Fill-time mode built (`min_activity_at="fill"`: the order is pulled when the market is quiet at the fill; suite 565 passed)
- ☑ A3c Fill-time gate in-sample (2022 model): −0.066 → −0.033 R pooled, 2 of 3 indices, removed 114 trades at −0.36 R (z −2.7); mostly US100
- ☑ A3d Re-check after the DST fix: pooled −0.066 → −0.044 but only 1 of 3 indices (a US100 effect) — the condition fails
- ✗ A4 2021 run: not run (condition failed); 2021 stays untouched
- ☑ A5 Logged (review log #43); the option stays in the code, off

## B. 30-trade review (15 winners / 15 losers), price focus
- ☑ B1 Fact sheets with the turn point (where price really turned + known levels there)
- ☑ B2 Written reviews, two reviewers × 15 trades (`research/trade-reviews/2026-11-16-30-trades/`)
- ☑ B3 Synthesis: `research/trade-reviews/2026-11-16-30-trades/SUMMARY.md`
- ☑ B4 Level-based tweaks on all 4,656 trades: none lifts mean R (stops beyond array/pool raise win rate to 44–50% at the same R; entry at the HTF array is worse, z −2.0)
- ☑ B5 Nothing qualifies for the change gate (rule R11). Weak lead only: skip when a pool sits within 0.15 ADR beyond the stop (+0.053 vs −0.027 R, z ≈ 1)
- ☑ B6 PD-array flags from the reviewers listed in the review summary and in the session summary (open item for the next array audit)

## C. Microstructure (the layer we had not used)
- ☑ C1 Break the references (`references/orderflow.md`, `references/microstructure/`) into components: measure, formula, data it needs, computable with our data or not
- ☑ C2 Compute each usable component as a fact known at the entry, with tests (bar-based on all 7 datasets; trade-flow based on NQ 2024)
- ☑ C3 Test each component on the backtest trades: does it separate wins from losses, on how many datasets?
- ☑ C4 Verdicts: 26 components, 52 tests, none passes the false-discovery check; volatility and real volume duplicate the activity measure (`research/microstructure/2026-11-16-study.md`)
- ☑ C5 Nothing positive → nothing to the change gate. One lead (flow against the trade in the last 30 min did better) needs Sharif's go-ahead: its test would use the 2024-H2 hold-out
- ☑ C6 DST fix: the activity baseline uses calendar days (test first; suite 570 passed)

## D. Engine fixes queued
- ☑ D1 Index-point thresholds scale by the futures tick outside the indices and gold (`instruments.unit` / `scaled`); futures cost for DXY and EUR/USD; indices untouched by construction
- ☑ D2 Backtests on silver, dollar index, EUR/USD: they trade now; no edge (review log #44)

## E. Wrap-up
- ☑ E1 Summary: `research/SESSION-2026-11-16.md`
- ☑ E2 Suite 570 passed after the last engine change; committed; review log #35–44; memory updated
- ☑ E3 Machine powered off (scheduled after the final commit)

## Done earlier this session
- ☑ Engine-plan confirmation entries, zone stop, results page
- ☑ Fable sweep + FABLES_FINDINGS
- ☑ Skills: trade-review, pattern-finder, pd-array-audit, change-gate, pipelines
- ☑ US100 full sweep; three-index check (stop-size rule failed, 2020–21 hold-out not spent)
- ☑ New datasets: 2020 indices, gold (silver / DXY / EUR/USD blocked by D1); cameron and MMxM-on-gold parked
- ☑ Tweak lab; order-flow facts in trade reviews

---

## Round 3 (2026-11-16, after the failed confirmation; Sharif: "proceed")
Order agreed: calendars → the unseen 2020 news split → forward log → conditions rules for the older models on 2021.

### F. Calendars
- ☑ F1 Holiday calendar (`ict_engine/news/holidays.py`: holiday / early close / after holiday), tests; on every fact sheet (a skip gate is left for J)
- ☑ F2 News calendar back to 2019-10 (ALFRED vintages kept in `ict_engine/news/vintages/`; FOMC 2019–2020 checked on the Fed's pages)
- ☑ F3 10:00 releases by publication rule (approximate) and the Jackson Hole speeches 2020–2025 (2026 to add)
- ☑ F4 `us_calendar.csv` rebuilt: 958 → 1,458 events, every old row unchanged; suite 588 passed

### G. The one unseen split
- ☑ G1 Pre-registered (`research/preregistered-recipe-news-2020.md`)
- ☑ G2 Run once: UNCLEAR (news days +0.39 R, others +0.25; volatility separates more)

### H. Forward log
- ☑ H1 Forward rules frozen: `research/forward-recipe-v1.md`, tag `forward-recipe-v1`, three candidates
- ☑ H2 `research/scripts/forward_recipe.py` → `reports/forward/recipe-forward.parquet` + `research/forward/recipe-forward-log.md` (counts only until the first look); 0 trades so far

### I. Older models by condition, confirmed on 2021
- ☑ I1 Three hypotheses fixed (`research/preregistered-conditions-2021.md`)
- ☑ I2 Run once: H1 and H2 not supported, H3 too few to judge (MMxM high vol: 25 trades, +0.63 R); no model has an edge on 2021
- ☑ I3 30 trades reviewed in writing (`research/trade-reviews/2026-11-16-conditions-2021/SUMMARY.md`)

### J. Fixes the reviews asked for (after F–I, each through the change gate)
- ☑ J1 TP1 picker: checked on existing facts, no consistent effect → not built (`research/decisions/2026-11-16-tp1-picker-min-widths.md`)
- ☑ J2 `cancel_run_r` option built (off); 2022–24 sweep: no gain → stays off (`research/decisions/2026-11-16-cancel-run.md`); 30 dropped trades under review
- ☑ J3 Minimum widths: checked, the size effect is US100 / 2022-model only, MMxM opposite → not built (same decision file)
- ☑ J4 Fact sheet: the turn line uses the trade's own day (to 16:55 NY); the note prints the area, the decision time and the trigger gap


## Round 4 (2026-11-16 evening: the live sheet and Sharif's lessons; to go through on 2026-11-17, with the live chart)

### K. Waiting on Sharif's answer
- ☐ K1 Order blocks on the page: show only the ones that form when price retraces into an area of interest. Is the right set "a breaker, an unfilled gap, the OTE of a break, a swept pool"?
- ☑ K2 Order block (answered 2026-11-17): engulf = the next candle closes beyond the block candle's open; the block is the body only. A better block has a strong body that was still engulfed; a body smaller than the wicks is not a strong block
- ☑ K3 Weak blocks: keep them dimmed for now, for learning (answered 2026-11-17)
- ☐ K4 His stop on the gap trade (trade 1, US100 Thu 12 Nov 10:03)
- ☑ K00 "Liquidity is created or taken" built into the system, 2026-11-17 during the New York session at Sharif's word: playbook steps 7a–7b, rule sheet (first three things + STATE lines), watcher (`conditions`, `pools`, taken levels in the summary), page (conditions / eaten / created at the top of Claude's read), prep prompts (`research/hunt-prep-prompt.md`), `CLAUDE.md`, worked example `research/hunt-log/2026-11-17-case-us100-ny-open.md`
- ☐ K01 Conditions gate (Sharif 2026-11-17: "identifying if the current market is moving cleanly and fast enough to even consider trades"): a clean / choppy reading per index for the page badge, the watcher summary and the checker (first try: net move ÷ distance travelled over the last hour of 1m candles, plus whether the three indices agree); check it against his own calls before trusting it
- ☐ K02 **Remind Sharif to go over paper idea NY-1 in detail** (his request, 2026-11-17; the cancel was not needed: only wicks below the range, no closes, not strong). The list of points: `research/hunt-log/2026-11-17-ny1-discussion.md`
- ☐ K03 The hunting brain (his design ask, 2026-11-17). Stage 1 done: the eyes (`hunt_scan.py`, five judgements, timeframe-free, hand-built tests). Stage 2 done: the page's "what the scan sees" layer (amber "B ·" marks + the five-judgement card), kept current by the feed; waiting for his check of the eyes before stage 3. Stage 3: `research/brain/lessons.toml` (each lesson as its WHY, linked to observation types) and recall by spreading activation. Then let the watcher refresh it every minute during a hunt. Check each stage with him; nothing tuned to a past day
- ☑ M2 Pushed by Sharif 2026-11-17
- ☐ K0 **Remind Sharif to reteach NDOG, NWOG and the opening range gap** (his request, 2026-11-17: he mixed some content up; the trading range is not the opening range gap). Until then the page's opening-gap rows and `research/ndog/` are unconfirmed
- ☐ K5 The weekend gap (NWOG) on regular-hours charts: which two prices define it
- ☐ K6 Watching 05:00–09:00 New York (tradable by his rule, no check-ins now); is 15 minutes the right rhythm
- ☑ K8 Afternoon window = 13:20–14:00 New York (answered 2026-11-17)
- ☐ K7 Should his marks carry from London into New York, or stay one session each (as now)

### L. To do
- ☐ L1 Does a breaker / order-block entry pay? In-sample run + 30 trades reviewed in writing (so far only his examples)
- ☐ L2 Gap-trade entry (`ndog_eql.py` `fvg_entry`): the "gap fully above the pool" rule is too strict (skipped US500 on 12 Nov, 2 points inside)
- ☐ L3 Choosing the index (weakest for a sell, cleanest pool) as a testable step
- ☐ L4 A script scoring his live marks against what happened (needs more saves)
- ☐ L5 Jackson Hole 2026 in the news calendar
- ☐ L6 A switch to hide the dotted reference levels until the hunt (if he wants it)
- ☐ L7 The engine's `order_blocks` does not follow his rule (`engulfed_blocks` lives in the live script only); move it into the engine behind an option once K1–K3 are settled

- ☐ L8 When the hunting rules are settled, write them down so a smaller model (Sonnet) can run the routine watch; Fable only for preps and key moments (Sharif 2026-11-17)

### M. Housekeeping
- ☑ M1 Hunting schedule set for 2026-11-17 (London prep 08:05 SAST, every 5 minutes 09:00–12:00; New York prep 14:45 SAST; live every minute 08:20–09:00, 09:20–10:00, 10:20–11:00 and 13:20–14:00 New York, every 5 minutes everywhere else from 02:00 to 14:00 New York). Session-only: re-create it if the Claude session was closed; expires after 7 days
- ☐ M2 Push (the remote is behind)
- ☑ M4 Gold and silver stay on the live sheet, for looking only (Sharif 2026-11-17: "keep gold and silver just for looking"): never hunted, never traded, no watcher marks. Start the feed with `live_recipe.py --assets US100 US500 US30 XAUUSD XAGUSD`
- ☑ M5 `/multi` has the drawing tools (2026-11-17, his request while reviewing NY-1): one palette for all charts, the same draft as the single chart, Reset and Save. Notes (write on chart) are still single-chart only
- ☐ M3 Forward test: first look when candidate 2 has 60 trades or on 2027-11-16 (`research/forward-recipe-v1.md`)

### Done in round 4
- ☑ 2026-11-17: script + Sonnet watcher (`hunt_watch.py`, `research/hunt-rules.md`); London hunt on US100 logged with a worked example (`research/hunt-log/`); lessons in the hunting playbook (memory), incl. the middle-of-the-block entry with the stop at the block's far edge; 1m chart; `/multi` page (own instrument and timeframe per chart, linked crosshair, % compare); line chart type on both pages (key L on the single chart); Claude's read cleared when a hunt closes
- ☑ Breaker detector: `merge` and `block="body"` options, off by default (`research/decisions/2026-11-16-breaker-merge.md`)
- ☑ Live sheet: entry areas, Claude's marks + "Claude's read", 1M–5m charts, Alt+R, reset, full-width layout, hunting window, clean chart per session
- ☑ README screenshot; CLAUDE.md updated; full suite 618 passed
