# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Early-stage ICT (Inner Circle Trader) engine. Built so far: pipeline stage 0 (`ict_engine/data/` — Dukascopy download, NY-time bars, quality check), stages 1–3 (`ict_engine/concepts/` — resampling, day context, clock, event detectors), stages 4–6 for the 2022 model (`ict_engine/models/` — gates, plan), stage 7 (`ict_engine/sim/` — fill/stop/TP1 simulation, day runner) and stage 9 (`ict_engine/eval/` — similarity scoring, reference cases, feed-basis anchors, `python -m ict_engine.eval.report`). Spec lives in `references/`.
- Visual index: `uv run python -m ict_engine.viz.daypack --references` → `out/index.html` (one day pack per reference trade: candles, levels, windows, events, every setup's gate trace, ICT's trade mapped onto the feed). Single day: `... daypack US100 2024-01-09 [--relaxed]`. Viewer template: `viewer/daypack.html`.

- Env: `uv sync`. Tests: `uv run pytest -q -rs` (`-rs` shows skips: real-data tests skip until data is fetched — a skip is not a pass).
- **Testing rule:** every module gets unit tests on hand-built candles with known answers, plus real-data regression tests against ICT's live executions (`tests/test_regression_ict_trades.py`). Events carry `ts` = when they became known; tests must check no look-ahead.
- Data: `uv run python -m ict_engine.data.dukascopy fetch US100 2023-11-01 2024-01-31` (assets: US100 US500 US30 XAUUSD XAGUSD DXY EURUSD, or `all`); `... check ...` for gaps/bad candles. Parquet cache in `data/bars/` (git-ignored). Bars are UTC on disk, NY-indexed when loaded.
- **Feed basis:** Dukascopy CFDs are not futures; the gap is carry (tens to 150+ NQ points, jumps at contract roll). Never measure it at a trade's entry. Use the case's `anchors` (named chart levels) → `ict_engine.eval.basis.estimate_offset` → `case.compare_kwargs(offset)`.
- **Pipeline** (`references/pipeline.md`): the standard path every trade follows — data → day context → clock → events → model state → gates → mark (plan frozen before fill) → simulate → record (trade card) → measure. Build new stages into the modules it names.
- **Trades are snowflakes:** never test for an exact match. Compare traits with `ict_engine.eval.compare` (score 0–1; match ≥ 0.80, similar ≥ 0.60; prices in R; missing traits dropped). Reference trades: `tests/cases/ict_live_exec.yaml` (from ICT's live executions; screenshots in `references/personal/notion/img/live-exec/`).
- Contradictions between sources are settled on ictindex.io; rulings in `references/personal/ictindex-rulings.md`.

- `ref.md` — the intended charting/trading platform base: OpenCharts (https://github.com/dylanpersonguy/OpenCharts).
- `references/` — ICT methodology PDFs that serve as the domain spec:
  - `The ICT Bible - V1 - By Ali Khan.pdf` (37 pp) — foundational ICT concepts and abbreviations.
  - `2022 Content.pdf` (31 pp) — terminology glossary, ICT 2022 model, trade examples.
  - `Market Maker Model - PDF.pdf` (9 pp) — buy/sell market maker models, identification and execution (intraday focus).
  - `PO3 - Fractal Study.pdf` (8 pp) — Power of 3 (accumulation/manipulation/distribution) across month/week/day timeframes.

- `references/models.md` — curated model cards (Silver Bullet, 2022 model, MMBM/MMSM, PO3 day, OTE, PD array returns, TGIF). Source of truth for what the engine evaluates.
- `references/framework.md` — rules above every model: bias (M/W/D), timeframe jobs, premium/discount pricing, POI rule, quarterly theory, killzones, earliest close (TP1), entry/stop types.
- `references/personal/notion.md` — index of Sharif's cleaned Notion notes (`references/personal/notion/*.md`). Each section links its Notion page; the chart screenshots (worked examples) stay in Notion. Romeo and some Setups/Extras sections are third-party and labelled.
- `references/patterns.md` — pattern cards (Turtle Soup, Judas Swing, Unicorn, SMT, algorithmic macros, opening range, time-of-day behaviour).

Spec: "ICT Engine — Spec (Draft)" at https://claude.ai/artifact/1PbBE8zuRHZJQSyfMTTcz4. The engine opens/closes simulated trades per model; **a vote = one winning trade** (earliest close / TP1 hit before stop). The leaderboard ranks models by **expectancy (R)** per time bucket (killzone, weekday, NY hour, quarter), with votes, Wilson win-rate range and edge vs a random-entry baseline beside it. Time is checked before any price pattern. Metrics are viewed in a Model Leaderboard panel inside OpenCharts. Benchmark assets: gold, silver, US500, US100, US30, US dollar index, Euro currency index. v1 data = free Dukascopy 1-minute (XAU/USD, XAG/USD, USA500.IDX, USATECH.IDX, USA30.IDX, DOLLAR.IDX, EUR/USD as Euro index proxy) via `dukascopy-node`; futures (GC, SI, ES, NQ, YM, DX, 6E) later. Analysis correctness matters more than perfect data.

Languages: Python for the engine and analysis; TypeScript only where needed (OpenCharts adapter, overlays, dashboard).

## Conventions

- Keep four layers separate: **concepts** (FVG, OB, NWOG, killzones — detected, not scored), **patterns** (recognisable, often time-bound events — scored by hit rate), **strategies** (bias/narrative filters — never open trades), **models** (full trade recipes — the only thing that collects votes). Don't mix them in one file or one rule.
- Patterns and models are separate but linked: each model card lists required/tracked patterns, and every trade records which patterns were present, so we can compare win rates with vs without each pattern.
- Every trade is tagged with a trading style (scalp / day / swing) and all analysis is reported per style — never mixed (framework.md §0).
- Check order on every candle: time window → bias → premium/discount of the dealing range → HTF POI → entry trigger. A FVG outside a POI or outside its time window never opens a trade (it is still logged).
- All times are New York local time (America/New_York, DST-aware).
- To clarify any ICT concept, search ICT's own transcripts at https://ictindex.io (search page is JS-rendered; use a browser). ICT's words beat the PDFs, which beat third-party write-ups. ICT's direct words include his Twitter Spaces, livestreams and "Michael" notes (Michael J. Huddleston = ICT). **When sources contradict, ictindex.io decides.**
- OpenCharts (`ref.md`) is the local chart for viewing and testing: React/TS, lightweight-charts; feed it data via an `OpenChartsAdapter`, draw overlays via `PluginBase` plugins.

## Reading the references

The PDFs are text-extractable. Pull just the pages you need rather than whole files:

```bash
pdftotext -f <first> -l <last> "references/<file>.pdf" -
```

## Domain vocabulary

The references (and likely future requests) use ICT shorthand, e.g.: MSS (market structure shift), BOS (break of structure), STH/STL, ITH/ITL, LTH/LTL (short/intermediate/long-term highs/lows), BSL/SSL (buyside/sellside liquidity), EQH/EQL, PDH/PDL, PWH/PWL (previous day/week high/low), IDM (inducement), FVG (fair value gap), PO3 (power of 3), premium/discount. Check the glossary in `2022 Content.pdf` before guessing what an abbreviation means.
