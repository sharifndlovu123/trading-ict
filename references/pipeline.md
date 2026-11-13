# Trade pipeline — how a trade is found, marked and measured

One standard path for every model. Each stage has one job, writes its output, and never reaches back into an earlier stage. Rules live in `framework.md`, `models.md`, `patterns.md`; this file is only the **order** and the **records**.

**Snowflake rule:** no two setups are identical. The pipeline never asks "is this exactly ICT's trade?" It records the trade's **traits** (time, liquidity taken, PD array, pricing, entry, stop, TP1, model) and compares traits by similarity (`ict_engine/eval/similarity.py`). Two trades are alike when enough traits are alike.

```
 bars ─▶ 0 Data ─▶ 1 Day context ─▶ 2 Clock ─▶ 3 Events ─▶ 4 Model state ─▶ 5 Gates ─▶ 6 Mark ─▶ 7 Simulate ─▶ 8 Record ─▶ 9 Measure
                    (before open)    (each bar)  (each bar)   (each bar)       (on trigger)  (plan)    (bar by bar)   (trade card)   (reports)
```

## 0. Data
- 1-minute OHLC per asset (Dukascopy v1), timestamps converted to **America/New_York** (DST-aware).
- Calendars: sessions, holidays, news events (NFP, CPI, FOMC…), contract roll dates for futures references.
- Output: clean bars + calendar. No look-ahead: every later stage sees only bars up to "now".

## 1. Day context (computed before the session; frozen for the day)
- **Bias** M / W / D (`framework.md` §1) with the reason (draw on liquidity).
- **Dealing ranges**: HTF 20/40/60-day and the intraday leg; premium/discount and quadrants (§3).
- **HTF POIs**: FVGs, OBs, breakers, NDOG/NWOG, opening range gap — only *valid* ones (§9).
- **Liquidity map**: PDH/PDL, PWH/PWL, Asia / London highs & lows, EQH/EQL, swing points (4-candle swings).
- **Tags**: weekday, news event, NFP week, month (August), quarter (§5).
- Output: `DayContext`. A model may not change it during the day.

## 2. Clock (every bar, first check — time is king)
- Which windows are open: killzones, Silver Bullet hours, macros, lunch (no new trades 12:00–13:00).
- A model whose window is closed does nothing further on this bar (events are still detected and logged).

## 3. Events (every bar; concept detectors — detected, never scored)
- Swing high/low confirmed · liquidity **sweep** (which pool) · **displacement** · **MSS / BOS** · **FVG / IFVG / VI formed** · POI **touched** · gap **filled / invalidated**.
- Each event gets an id, time, price range and timeframe. Events are the evidence a trade will point to.

## 4. Model state (every bar)
- Each model is a **sequence of required steps** (from its card), run as a small state machine per direction. Example, 2022 model long: `opposite liquidity taken → displacement + MSS → FVG formed in discount inside a POI → price returns to FVG`.
- A step is satisfied by an event id. Steps time out (e.g. FVG not returned to before the window closes → reset).
- Patterns (`patterns.md`) are checked alongside and attached as tags; *required* patterns are steps, *tracked* patterns are just recorded.

## 5. Gates (when a model reaches its trigger) — fixed order
`time → bias → premium/discount → HTF POI → entry trigger`
- Pass all → go to Mark.
- Fail any → **logged as a "would-be" setup** with the gate that stopped it. Nothing is thrown away: this lets us later measure what each gate is worth.

## 6. Mark (the trade plan — written *before* the fill, then frozen)
- **Entry** type: drill / CE / complete fill (§8) → price.
- **Stop** type: imbalance end / OB / swing point / wick CE → price.
- **TP1** = earliest close, low-hanging fruit (§7) → price and R. **Final target** → price and R.
- **Style** (scalp / day / swing) and its time exit (§0).
- Reject if TP1 < minimum (10 handles indices / 15 pips FX potential) or the path to TP1 is high-resistance.
- Output: `TradePlan`. A plan can never be edited after the entry is placed — that is what makes the vote honest.

## 7. Simulate (bar by bar on 1m)
- Fill when price reaches the entry inside the window; unfilled at window end → cancelled (logged).
- Stop and TP1 in the **same 1m bar → count the stop first** (conservative) and flag the trade as ambiguous.
- After TP1: runner variants (all-out at TP1 / partial + runner / trail stop under the launching FVG).
- Time exit per style. Costs (spread, slippage) applied.

## 8. Record — the **trade card** (one per trade, also one per would-be setup)
| Group | Fields |
| --- | --- |
| Identity | id, model, variant (params), asset, style, direction, day |
| Traits | entry time/price, stop, TP1, final, R values, PD array + timeframe, liquidity taken, window, pricing zone |
| Evidence | event ids for each model step (sweep id, MSS id, FVG id, POI id) — the "why" |
| Context | bias M/W/D, dealing range, tags (weekday, news, killzone, quarter), patterns present |
| Gates | pass/fail per gate, in order |
| Result | filled?, TP1 hit before stop (**vote**), R at TP1 exit, runner R, ambiguity flag, exit reason |

The traits block is exactly `TradeSnapshot` in `ict_engine/eval/similarity.py`, so any card can be compared with any reference case. Cards also feed the chart overlays in OpenCharts (entry/stop/TP lines + evidence boxes).

## 9. Measure
- **Leaderboard** (per style, per time bucket): expectancy (R), votes, Wilson win-rate range, edge vs random-entry baseline, minimum 30 trades, out-of-sample 70/30.
- **Reference recall** (`tests/cases/ict_live_exec.yaml`): for each ICT trade, the engine's most similar card on that day and its verdict — *match* (≥ 0.80), *similar* (≥ 0.60), *different*. The report lists which traits agreed and which didn't, e.g. "time 1.00, PD array 0.60 (FVG vs IFVG), entry 0.85".
- **Extras**: engine trades resembling no reference are not errors (ICT didn't take every setup) — they go to a review list.
- **Gate value**: compare would-be setups vs trades to see what each gate filters out.

## Where the code lives
| Stage | Module (planned) |
| --- | --- |
| 0 | `ict_engine/data/` (**built**: Dukascopy fetch → Parquet, NY-time load, quality check) |
| 1–3 | `ict_engine/concepts/` (**built**: `bars.py` resampling, `context.py` day context + pricing + v1 bias, `clock.py`, `events.py` swings / displacement / FVG / VI / IFVG lifecycle / sweeps / BOS-MSS) |
| 4 | `ict_engine/models/` (one state machine per model card) |
| 5–7 | `ict_engine/sim/` |
| 8 | `ict_engine/records/` (trade cards → DuckDB) |
| 9 | `ict_engine/eval/` (**built**: similarity, reference cases, feed-basis anchors) |
