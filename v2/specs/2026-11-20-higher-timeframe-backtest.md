# A backtest of the tools on higher timeframes: design

Status: draft for Sharif's approval. Written 20 Nov 2026 from our conversation. Nothing in it is built yet.

## Why this exists

Four concepts are in v2 (bias, liquidity with alt-liquidity, the two working together, sessions) and three of them
have tools. Those tools have only ever been checked on the handful of charts Sharif and Claude looked at together.

Sharif, 20 Nov 2026: "I know we currently don't have entries etc, but I'm thinking we can build backtesting with what
we have and the pattern finder. You can start looking at old data and looking at bias etc, liq, and looking to areas
to see price go and leave from, and evaluate if price moves how you're seeing it could. This will help strengthen
those tools first."

## What he decided

1. **The tools make the read, not Claude.** At fixed moments over old data, the tools say what they see. (He chose
   this over Claude reading each moment by hand.)
2. **Higher timeframes only.** "We are looking at the bias and liq eaten at higher levels, so this backtest will be
   higher timeframes, so lowest tf is probably hourly or 4h."
3. **A paper trade here is only a call about a draw.** "Such as: we are looking for price to possibly draw into this
   area, or this section; did that happen or not." "DON'T look at the exact entries and details in depth."
4. **Every call can be opened on the chart** as it stood at that moment, so he can look at the ones that went wrong
   and say what the tool missed. (Approach C of the three offered.)
5. **A pattern finder comes with it,** to find what repeats, including inside the sessions.

## Goals

- For each tool, a plain answer to "when it said this, how often did price then do it?", over years and across
  instruments, not on four charts.
- A way for Sharif to look at any single call on the chart, at the moment it was made, with nothing after it shown.
- A first pattern finder: tables of what repeats, with how many times each was seen.

## Not goals

- Entries, stops, targets, profit or loss. There are none in this backtest.
- Anything below the 1-hour chart.
- The eyes, the brain's pulling, or hunting. Hunts stay off; this places nothing and watches nothing live.
- A range or trading-range reading: neither has a tool yet.

## What would make this a failure even if it works

- **A tool or a lesson being changed to make a number better.** That is how the first version was damaged. What the
  backtest shows goes to Sharif, the way hunt notes do; a tool changes only through learn, with him.
- **Looking ahead.** A read that uses a candle that had not closed yet, or a high that was not yet known to be a high.
- **A result presented as an edge or a rule.** These are observations about tools.
- **A flattering number.** The nearer of two levels is usually reached first whatever the bias says. A result that
  does not account for that would make the bias tool look good for no reason.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Draw calls: the tools read each timeframe at fixed moments, make a call about where price might draw to, and the outcome is recorded | Tests the tools together, as they are used; a bad number does not always say which tool is at fault |
| B | One study per tool, each alone | Easy to see which tool is weak; never tests them working together |
| **C (chosen)** | A, and any call can be opened on the chart in replay with the tools' marks as they stood | More to build; lets him correct what a tool missed by looking at it |

Sharif picked C: "C makes sense."

## How it works

### 1. The moments

A read is made at fixed moments, on every trading day in the data, for each instrument. Proposed: **twice a day, at
the start of the London kill zone and the start of the New York kill zone** (his session times, from the sessions
tool). At a moment, only candles that had fully closed by then exist.

### 2. The read, per timeframe

For each of the monthly, weekly, daily, 4-hour and 1-hour charts, the existing tools give:

- the bias, the level behind it and the level ahead (the bias tool, looking two timeframes up);
- the nearest resting buyside above price and the nearest resting sellside below (the liquidity tool, with his eye's
  measure for "very close");
- the nearest unfilled imbalance above and below (the alt-liquidity tool: three-candle gaps and volume imbalances).

No tool is changed for this. The backtest only calls them.

### 3. The calls

Each read produces a small number of calls. A call is one sentence that can turn out true or false:

| Call | What it says | It came true when | It was undone when |
|---|---|---|---|
| **Liquidity with the bias** | Bias bull: price might draw to the resting buyside above. Bias bear: to the sellside below | that liquidity is eaten | the resting liquidity on the other side is eaten first, or a body closes through the level behind |
| **The bias holds** | The level behind will not be closed through before the level ahead is | a body closes through the level ahead | a body closes through the level behind |
| **Imbalance as a draw** | Price might reach the nearest unfilled imbalance in the direction of the bias | price trades into it | a body closes through the level behind first |

A call that is neither true nor undone after a set number of candles of its own timeframe is recorded as
**unresolved**, not dropped.

For every call these are kept beside it, because they are what the patterns will be looked for in:

- the instrument, the timeframe, the moment, which session it was made in;
- whether its timeframe's bias agrees with the timeframe above (with or against);
- how far away the target was compared with the thing that would undo it;
- how long it took, in candles, and which session it resolved in.

### 4. Keeping the numbers honest

- **The nearer level usually goes first.** So every result is shown split by which was nearer, the target or the
  thing that undoes it. "The bias was right 60% of the time" means nothing by itself; "the bias was right 60% of the
  time when the target was the farther one" does.
- **With the bias against the same call made against it.** For liquidity, the same race (buyside or sellside first)
  is counted for the bias's side and for the other side, so the bias tool's worth is the difference between them.
- **Counts beside every percentage.** A pattern seen eleven times is shown as eleven times.
- **Years and instruments shown separately** before any total, so one unusual year cannot carry a result.

### 5. The replay view

Each call has an id. The chart page opens a call with that id: the chart is taken back to the moment of the call
(nothing after it is shown), with the tools' marks as they stood (levels behind and ahead, the liquidity, the
imbalance, the target). Stepping the replay forward shows what happened. This uses the replay the chart already has.

### 6. The pattern finder (first version)

A set of tables built from the calls, answering "what repeats?":

- which calls come true most and least, by timeframe;
- with the timeframe above against against it;
- by the session a call was made in and the session it resolved in, including the time of day targets get reached;
- by how far the target was;
- by instrument and by year.

It reports what stands out and how many times it was seen. It does not propose rules. Sharif's expectation that
displacement gathers around certain times is **not** tested in this round: there is no displacement tool yet.

## Where things are kept

| What | Where |
|---|---|
| The backtest's code and its tests | `v2/backtest/` |
| The calls and their outcomes (large, rebuilt by running it) | `v2/backtest/out/`, not in git |
| The tables | a page the chart server shows, on the same port and behind the same password |
| How to run it and what it must never do | `.claude/skills/backtest/SKILL.md` (his reminder file there is kept) |

## What it runs on

The 1-minute candle files already on disk (free data): the indices from late 2019, the metals, the dollar index and
the euro from late 2021. No new data is bought. It uses at most 8 workers.

## Tests (part of the build, not after it)

On hand-built candles with known answers, at several price scales and timeframes:

- a call comes true, is undone, and stays unresolved, each when it should;
- nothing after the moment of the read can change the read (the same read with and without later candles);
- a candle still forming at the moment is not used;
- the "which was nearer" split is right;
- the session a moment falls in comes from the sessions tool, in summer and in winter.

And the context check is run on the backtest as on a concept: no price, date or instrument in the code.

## Decided by Claude, for Sharif to overrule

- Two moments a day, at the starts of the London and New York kill zones.
- The lowest timeframe is the 1-hour; the highest is the monthly.
- The three kinds of call in the table above, and what makes each true or undone.
- A call left unresolved after 20 candles of its own timeframe.
- The tables live on the chart page, not in a separate program.
- The first pattern finder only makes tables; it suggests nothing.
- The older backtest idea (running the whole hunt over old data) stays where it was: later, after the eyes. This one
  is called the **tools backtest** to keep the two apart.
- The old version's way of storing and showing results is not looked at. (The earlier design said to ask him first
  whether to; this is that question.)

## Left to the builder

- How the calls are stored, and how the run is split across instruments.
- The layout of the tables page.
- The exact wording of the skill.

## What he will see first

A first run on one instrument and one year, with the tables and a handful of calls to open on the chart, before
anything is run over everything. He says whether the calls are the right calls before the full run.
