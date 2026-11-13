# ICT Engine

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-early%20development-orange)
![Tests](https://img.shields.io/badge/tests-pytest-informational)
![Data](https://img.shields.io/badge/data-Dukascopy%201m-lightgrey)

**Tags:** `ict` `inner-circle-trader` `smart-money-concepts` `backtesting` `trading-models` `fair-value-gap` `market-structure` `silver-bullet` `killzones` `futures` `nasdaq` `sp500` `gold` `python` `pandas` `lightweight-charts`

An engine that tests **ICT (Inner Circle Trader) trading models** on historical 1-minute data. For each model it opens and closes simulated trades by rule, marks each one a win or loss, and ranks the models by **expectancy (R)** per time bucket: killzone, weekday, NY hour and quarter.

> Research tool only. Nothing here is financial advice.

## Ideas it is built on

- **Time first.** Every candle is checked in a fixed order: time window → bias → premium/discount → higher-timeframe POI → entry trigger. A fair value gap outside its time window or POI never opens a trade, but it is still logged.
- **Four separate layers:**
  - **Concepts** (FVG, order blocks, killzones) are detected, never scored.
  - **Patterns** (Turtle Soup, Judas swing, SMT…) are scored by hit rate.
  - **Strategies** (bias filters) never open trades.
  - **Models** are full trade recipes, and the only layer that collects votes.
- **A vote is one winning trade:** the earliest target (TP1) is hit before the stop. The plan is fixed before the fill and can't be edited afterwards.
- **Trades are snowflakes.** Engine trades are compared with reference trades by trait similarity (time, entry in R, PD array, liquidity, model), never by exact match.
- **No look-ahead.** Every detected event carries the time it became known, and later stages may only use it after that time.

## Pipeline

```
data → day context → clock → events → model state → gates → mark (frozen plan) → simulate → trade card → measure
```

See [`references/pipeline.md`](references/pipeline.md). Rules live in [`framework.md`](references/framework.md), model cards in [`models.md`](references/models.md), patterns in [`patterns.md`](references/patterns.md).

| Stage | Module | Status |
| --- | --- | --- |
| 0 Data | `ict_engine/data/` | Dukascopy 1m download → Parquet, NY-time bars, quality check |
| 1–3 Context, clock, events | `ict_engine/concepts/` | levels, ranges, pricing, killzones, swings, displacement, FVG / IFVG / VI lifecycle, sweeps, BOS / MSS |
| 4–7 Model, gates, plan, sim | `ict_engine/models/`, `ict_engine/sim/` | 2022 model in progress |
| 8–9 Record, measure | `ict_engine/eval/` | similarity scoring, reference cases, feed-basis anchors |
| Viewer | OpenCharts | planned: day packs → chart overlays |

## Quick start

```bash
uv sync
uv run pytest -q -rs                       # -rs shows skipped real-data tests (a skip is not a pass)

# download 1-minute data (US100 US500 US30 XAUUSD XAGUSD DXY EURUSD, or `all`)
uv run python -m ict_engine.data.dukascopy fetch US100 2023-11-01 2024-01-31
uv run python -m ict_engine.data.dukascopy check US100 2023-11-01 2024-01-31
```

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/) and Node.js (for `npx dukascopy-node`).

## Data

- **v1:** free Dukascopy 1-minute CFD/spot data for gold, silver, US500, US100, US30, the dollar index, and EUR/USD as a Euro-index proxy. The data is not committed; download it with the command above.
- **Later:** futures (GC, SI, ES, NQ, YM, DX, 6E).
- **CFD vs futures:** CFD prices differ from futures by carry, which ranges from tens of points to 150+ NQ points and jumps at each contract roll. Reference trades are mapped across using anchors, named levels read from the reference chart ([`ict_engine/eval/basis.py`](ict_engine/eval/basis.py)), never the trade's own entry.

## Tests

- **Unit tests** on hand-built candles with known answers, for every module.
- **Regression tests** on ICT's own live executions (`tests/cases/ict_live_exec.yaml`). These check that the engine sees what ICT saw: bias, sweep, MSS, displacement FVG, targets. They need downloaded data and skip without it.

## Repository notes

- Third-party study material (PDFs) and personal notes are kept locally and are git-ignored on purpose.
- ICT concepts are attributed to Michael J. Huddleston (ICT). This project is not affiliated with or endorsed by him.

## License

Not yet chosen. Private repository for now; pick a license before making it public.
