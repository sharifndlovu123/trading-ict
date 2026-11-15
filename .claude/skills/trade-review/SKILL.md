---
name: trade-review
description: Review a trade after it is made — Sharif's own trade, ICT's, or an engine trade — and say what the trader tried to do, how it played out, and what was missed or should have been seen, graded on the ICT checklist (time, bias, premium/discount, POI, liquidity sweep, trigger, stop, targets, management) with known-at-entry facts kept apart from hindsight. Use whenever someone shares a trade to evaluate or post-mortem, asks "what went wrong / what did I miss / was this a good trade", pastes entry/stop/TP levels or a TradingView chart of a closed or running trade, or points at an engine plan or trade (out/plans, out/trades, backtest rows) to dissect — even if they don't say "review".
---

# Trade review (after the trade)

The goal is a fair, specific review that improves the next trade and feeds the engine. That means two things:
- separate **process** from **outcome**: a good trade can lose and a bad one can win;
- separate **what was knowable at the entry** from **what only hindsight shows**.

Blaming a trader for something no chart showed at entry teaches the wrong lesson. Ignoring a pool that was sitting right there misses the real one.

## 1. Get the trade

What you need: the asset, the side, the entry time (New York time), the entry price, the stop, the TPs (with % per TP if they scaled out), and whether the stop went to entry after TP1. Optional: the actual exit, a note on the idea, and chart links or screenshots.

- **A TradingView link** (`tradingview.com/x/<id>`): the image is at `https://s3.tradingview.com/snapshots/<first letter of id, lowercase>/<id>.png`. Download it to the scratchpad and look at it. Charts are often FXCM or futures, while our data is Dukascopy CFD, so prices can differ by a basis.
  - Map levels by structure (the same swing or candle), not by exact price.
  - For futures, see the feed-basis rule in CLAUDE.md.
- **An engine trade:** `--item out/trades/s/<id>.json` or `out/plans/s/<id>.json` fills everything in.
- **Something missing** (usually the entry time or the TPs): ask once. A review without the entry time can't separate known facts from hindsight.

Restate the trade in one line before going further, so a wrong level is caught early.

## 2. Pull the facts

```bash
uv run python research/scripts/trade_eval.py <ASSET> <long|short> "<YYYY-MM-DD HH:MM NY>" \
    --entry <p> --stop <p> --tp <p>:<pct> [--tp <p>:<pct>] [--be] [--exit-time "<...>" --exit <p>] \
    [--after 2] [--note "<their idea>"] [--json <scratchpad>/facts.json]
```

Assets: US100 US500 US30 XAUUSD XAGUSD DXY EURUSD. If the data doesn't reach the entry yet, fetch it:
`uv run python -m ict_engine.data.dukascopy fetch <ASSET> <start> <end>`.

The sheet has two sections:
- **Known at the entry:** the engine's read; the range place; liquidity taken in the 6 h before; the stop and TP1 checked against pools; the clock window and nearest news.
- **After the entry:** their management, the same trade flat at 16:55 NY, MFE/MAE, the pools price took next, and stopped-then-target.

Read the whole sheet before judging. The engine read statements under `<details>` are the monthly → 1H story.

## 3. Judge it on the rubric

Read `references/rubric.md` and grade each of its 10 steps: **pass / partial / fail / n/a**, with one line of evidence each.
- Steps 1–8 may cite only **known** facts.
- Where the trader's chart or note shows they saw something the engine didn't (or the reverse), say so. The disagreement is useful for both.
- The engine read is a strong witness, not the judge. When the trader's reading is the better one, say that.

## 4. Write the review

Save it to `research/trade-reviews/<YYYY-MM-DD>-<ASSET>-<side>.md` (append `-2` etc. if the file exists). Use this structure:

```markdown
# <ASSET> <side> — <entry date time> NY · <result in R> (<their management>) · day-only <R>
## What they tried to do
<2–4 lines: the idea in ICT terms. Which HTF story, which array, which liquidity as the target. Use their note or chart; if inferred, say so.>
## What happened
<3–5 lines from the after section: fill, path, exit, where price went next.>
## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time | ... | ... |
... (all 10)
## What they missed / should have seen (known at the entry)
- <each point cites a fact from the known section>
## What the market did (hindsight — lessons to test, not blame)
- <stopped-then-target, pools taken next, overnight vs day-only, how far it ran>
## Verdict
<one of: earned win · acceptable loss · lucky win · lesson loss>, and the single most useful change for next time.
## For the engine
- <a rule or check this trade suggests, phrased so it can be tested across many trades (which flag/param, in-sample first, pre-registered on 2024-07+ before it becomes a default)>
```

Keep it short and concrete: prices, times, R. Use ICT terms (MSS, BOS, FVG, IFVG, OB, EQH/EQL, PDH/PDL, BSL/SSL); never "CHoCH".

Then append one JSON line to `research/trade-reviews/log.jsonl`, so reviews can be mined later for which step fails most and which verdicts repeat:
`{"file", "asset", "side", "entry_time", "r_own", "r_day_only", "verdict", "grades": {"1": "pass", ...}, "missed": [short tags], "engine_idea": "..."}`.

## 5. Reply

Give a short summary in chat: the verdict, the two or three things that mattered most, and the R (their management vs day-only). Link the review file. If several trades are reviewed together, add a line on what repeats across them: that's the pattern worth testing.

## Ground rules
- This repo keeps its rules in `CLAUDE.md`; follow them.
- ictindex.io decides contradictions between sources.
- In-sample vs unseen data rules still apply to anything proposed for the engine.
- Never write into `reports/reviews/*.jsonl`. Those are Sharif's saves from the review pages.
- The trader is Sharif or ICT, both experienced. Write as a peer doing a post-mortem: direct, specific, no lecturing.
