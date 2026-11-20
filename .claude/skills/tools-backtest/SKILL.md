---
name: tools-backtest
description: Run and read the TOOLS BACKTEST - the concept tools (bias, liquidity, imbalances, sessions) reading old data on the higher timeframes, making calls about where price might draw to, and each call followed to see whether it came true. Use when Sharif says "backtest", "run the backtest", "test the tools on old data", "what do the tables say", "open that call", "pattern finder", or asks how often a tool is right. It has no entries, places nothing, and never changes a tool or a lesson. (The larger backtest that runs the whole hunt over old data is a different thing and waits for the eyes: see the README in the backtest skill folder.)
---

# Tools backtest

Sharif, 20 Nov 2026: "we can build backtesting with what we have and the pattern finder… looking at bias etc, liq, and
looking to areas to see price go and leave from, and evaluate if price moves how you're seeing it could. This will help
strengthen those tools first." Design: `v2/specs/2026-11-20-higher-timeframe-backtest.md`.

## What it is

At the start of each of his kill zones, on every trading day in the candle files, the tools read the monthly, weekly,
daily, 4-hour and 1-hour charts and make **calls**. A call is one sentence that can turn out true or false:

| Call | It says | True when | Undone when |
|---|---|---|---|
| liquidity | with the bias, price might draw to the resting liquidity on the bias's side | that liquidity is eaten | the other side is eaten first, or a body closes through the level behind |
| bias | the bias holds | a body closes through the level ahead | a body closes through the level behind |
| imbalance | price might reach the nearest unfilled imbalance in the bias's direction | price trades into it | a body closes through the level behind |

No entries, stops or targets. "DON'T look at the exact entries and details in depth."

## Running it

```bash
uv run python v2/backtest/run.py US30 --since 2025-01-01 --until 2025-12-31    # one instrument, part of the data
uv run python v2/backtest/run.py                                                # what he trades (the default)
uv run python v2/backtest/run.py --all                                          # every instrument in the data
```

About two minutes per instrument per year. Results go to `v2/backtest/out/` (not in git; rebuilt by running).
**A first look is always one instrument and one year, shown to him, before a full run.**

## Reading it

- The tables: `http://127.0.0.1:8776/backtest` (the chart server; restart it after a run if the page shows nothing new).
- Any call opens on the chart at its own moment, nothing after it shown: the "open on the chart" links, or
  `http://127.0.0.1:8776/?call=<id>`. Step the replay forward to see what happened.

## How to speak about a result (these are not optional)

1. **Say which was nearer.** The nearer of two levels usually goes first whatever a tool says. "The call came true 74%
   of the time" means nothing; "74% when the target was the nearer one, 30% when it was the farther one" does.
2. **Give the count with every share,** and say "few" when there are few.
3. **A result is about a tool, not about the market,** and several of the tools' rules are Claude's choices, named as
   such in each tool. A bad number may be measuring one of those and not his teaching.
4. **Never an edge, never a rule.** Point at what is interesting; a pattern is "might be".
5. Instruments that move together (the three US indices) are not three separate confirmations.
6. **Focus on what he trades.** "When it comes to backtesting focus more on what we're trading with": US100, US500
   and US30 first, then gold with silver beside it. Other instruments are fine for building and checking tools, and
   are shown apart, labelled as tests.
   Why: "these backtesting tools are validating for trades you're expected to make in the future yourself."

## The first thing it showed, which he marked as very important

"Notice the picture: the higher timeframes have higher percentages than below; note that, it's very important."
(20 Nov 2026.) What the bias adds to a liquidity call grows with the timeframe, from very little on the lowest one read
to the most on the weekly. Lead with the higher timeframes when reading a result, and never judge a lower timeframe's
call without the bias of the ones above it.

## Two timeframes read together (his correction after the first run, 20 Nov 2026)

He went through the first run and said the reads were right but stood side by side: "you're still looking at the
chart itself from daily and that's one perspective, or monthly and that's one perspective… there's a mix of
timeframes to provide a result." The lesson is in `03_bias_with_liquidity` ("Merging the timeframes"). So each
timeframe below the top also makes one **merged** call with the timeframe above it: whatever is nearest from price
now, on either of them (`calls.merged`). How "agree", "momentum" and "key area" are told apart is Claude's choice and
is named so in the code. The single-timeframe calls are kept so the two can be compared (section 2 of the page).

**Checking calls with him:** `/backtest/check` lists ten merged calls where the timeframes disagreed (`tables.check`),
each opening on the chart at its moment. What he says about a call is saved in `v2/backtest/reviews.jsonl`: his file,
read it, never edit it. His corrections there go through learn.

## What it must never do

- **Change a tool or a lesson.** What it shows goes to Sharif, the way hunt notes do. A tool changes only in learn,
  with him. Changing a tool to make a number better is what broke the first version.
- **Look ahead.** A read uses only candles that had closed; the candle still forming only moves "price now" and can
  use up a level. The tests hold this; keep them when anything changes.
- **Place or watch anything live.** Hunts are off; this is not hunting.

## When he looks at a call that went wrong

That is where the strengthening happens. Open the call with him, take what he says the tool missed as a correction,
and carry it through **learn**: his words into the lesson, then the tool and its tests, then the context check, then
run the backtest again and show the change on every instrument, not on that call.

## Choices that are Claude's, named in the code

Two reads a day at the kill-zone starts; the three calls and what undoes each; a call is not made again while the same
one is still open; 20 candles of its own timeframe before a call is left unresolved; 120 candles as "the picture being
looked at" for his eye's measure; the bias standing in for "the way price is moving"; candles, not the line chart.
