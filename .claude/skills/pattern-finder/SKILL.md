---
name: pattern-finder
description: Find the trade traits that repeat on our winners or losers and turn them into "do this more / do this less" — e.g. does an order-block entry beat an FVG entry, a killzone beat another, counter-weekly beat aligned, slow moves beat fast ones. Mines any set of trades (engine backtests in the trade store, the engine-plan simulation, Sharif's reviewed trades) with win rate, R, robustness and multiple-testing checks, and marks what holds. Use whenever someone asks what works, what to do more or less of, which setups/entries/times/arrays win, "find patterns", "what do our wins have in common", "why do we keep losing on X", or wants to raise the win rate from evidence — even if they don't say "pattern".
---

# Pattern finder: do more, do less

The goal is a short, honest list of traits that go with winning (do more) and losing (do less). Every claim needs enough trades and has to survive being searched for among many. Searching dozens of traits on the same trades will always turn up a few "winners" by chance, so the checks below exist to keep only what holds.

## 1. Pick the trades

| Source | Command flag | What it is |
|---|---|---|
| Engine plan simulation | `--sim reports/plans-sim.parquet --mode confirm_flip` (or `touch`, `confirm`, `confirm_reaction`, `confirm_flip_reaction`) | One plan per day at 08:30 on US100/US500/US30, by entry mode |
| Engine backtests (trade store) | `--files "reports/trades/<run>.parquet"` | 2022 model, MMxM, silver bullet, cameron runs |
| Reviewed trades | `--reviews research/trade-reviews/log.jsonl` | Trades reviewed with the trade-review skill; the checklist grades become traits |

**Store runs:** list them with `uv run python -m ict_engine.eval.store runs`. Use **one run per family × asset** (the default settings), or the same trade gets counted once per variant. Glob several assets of the same settings together, for example `"reports/trades/2022_model-*-2022-01-03-2024-06-28-<commit>.parquet"`.

**Pick the mode deliberately.** Different entry modes trade different days, so don't mix them.

**Reviewed trades:** there are few, so lower `--min-n` (e.g. 8). Treat what comes out as conversation material, not evidence.

## 2. Run it

```bash
uv run python research/scripts/pattern_find.py <source> [--pairs] [--min-n 30] [--features a,b,c] \
    --out research/patterns/<source-name>-<YYYY-MM-DD>.md
```

- **Traits** are taken automatically from the columns known when the trade was decided:
  - categorical columns as they are;
  - numbers cut into thirds.
- **Outcome columns are never traits:** r, vote, exit, MAE, shadow_*, cf_*, outcome and the like. Using them would be hindsight.
- **`--target win`** judges the win rate (TP1 hit before the stop, two-proportion z) instead of mean R. Sharif's goal is win rate, so run both and report both.
- **`--pairs`** also tests two traits together, such as "gap entry & slow move". Use it when singles look mixed.
- **Rows from 2024-07-01 on are dropped by default:** that data stays unseen. `--include-unseen` is only for running a pre-registered confirmation.

**To test a trait the table doesn't have yet**, add it as a column to the source first, computed from decision-time data only. Examples: "liquidity swept before the entry", "stop beyond a pool", an OB strength flag. `research/scripts/trade_eval.py` has functions for several of these.

## 3. Read the labels

- **DO MORE / DO LESS:** passes the false-discovery correction (Benjamini–Hochberg, q 0.10). The sign also has to hold in both halves of the period, in most assets, and with each trade capped at 10 R (so one outlier can't carry it).
- **LEAN MORE / LESS:** z ≥ 2 and stable, but not through the correction. A lead worth checking, not a finding.
- **Strong but not stable:** a big z carried by one half, one asset or one outlier. Usually noise, so say so.

What to watch for:
- **Win rate and R can disagree.** Fill-on-touch counter-weekly shorts won 76% for only +0.35 R. A high win rate with tiny R, or a low win rate carried by a few huge wins, needs saying explicitly. The goal is **≥ 50% win rate with positive expectancy**, so report both numbers.
- **Mirror traits are one finding, not two.** `fast=True` DO LESS and `fast=False` DO MORE say the same thing.
- **Pairs that just repeat a single** (e.g. `src=gap & fast=False` when nearly all trades are gaps) add nothing. Name the single.
- **Overlap:** consecutive days can re-trade the same zone, so z is optimistic. Weigh the n and the Wilson range.
- **Small n:** n < 30 stays a lead whatever its z.

## 4. Write it up

Save the script's tables to `--out` (a .csv with every test is written alongside). Then add a short section at the top of that file:

```markdown
## Try more
- <trait, in plain trading words> — win X% [lo–hi] vs Y%, ΔR +0.xx (capped +0.xx), n N, holds in both halves and A/B assets. <why it may make sense in ICT terms, or "no known reason">
## Try less
- ...
## Leads (not yet evidence)
- ...
## Next
- <the one or two findings worth a pre-registration: the exact rule, the data, and the pass bar (≥ 30 unseen trades, z ≥ 2.4)>
```

Translate traits into how a trader would say them. `read_kind=counter_weekly & side=short` becomes "shorts when the weekly is bull but the daily/4H turned bear". `fast=True` becomes "the move into the zone ran ≥ 0.2 ADR per 4H candle".

## 5. Reply

In chat: the try-more and try-less lists (3–5 items each, with win %, ΔR and n), what to pre-register next, and the file path. Say plainly that this is in-sample, and how many tests were run.

## Ground rules
- Follow `CLAUDE.md`.
- Selection uses 2022-01-03 → 2024-06-28 only. A pattern becomes an engine default only after it beats the baseline on unseen data via a pre-registration (`research/preregistered-*.md`).
- Log results in `research/review-log.md`. Check that log before reporting a "new" pattern: it may already have failed (rows #1–36).
- Never write into `reports/reviews/*.jsonl` (Sharif's review saves).
- Single trades are the trade-review skill's job. This skill is about what repeats across many.
