---
name: draw
description: How Claude puts marks on the chart for Sharif - in a learn session to show a lesson was taken in, and in a hunt to show what it sees. Use whenever marks are to be drawn, changed or removed on the chart page, when Sharif says "draw", "mark", "show me on the chart", or asks to see what Claude sees.
---

# Draw

Sharif: "You drawing what you see allows me to properly understand what you're telling me; that's the easiest way to
communicate to me." Drawing is the language in both modes. A mark is a claim he can check at a glance.

## What to draw, and in what order

1. **Relative to now.** "Draw it based on what you see right now." Mark what matters for where price is at this
   moment. Something that was liquidity for an earlier price is not drawn.
2. **From the monthly down, and every timeframe gets its own marks.** Monthly first, then weekly, daily, lower. Do not
   only read a higher timeframe: draw on it. (He, 18 Nov 2026, after I marked nothing on the monthly: "when marking
   you're starting from the top to the bottom, BUT it is relative to now, so what's happening in our current time, but
   relative to tf this xx is close so mark it.")
   - **"Close to price" is judged on each timeframe's own scale.** An area a hundred points away is close on the
     monthly and far on the hourly. On each timeframe ask: from where price is now, what on *this* timeframe is close?
   - The higher timeframe's marks are what the lower ones sit inside: say so in the read (an hourly low inside a
     monthly imbalance is the point, not a detail).
3. **Original liquidity before alt-liquidity.** Pools of stops first; imbalances second.
4. **Only what is in the brain.** Draw with concepts that are in `v2/concepts/`, and nothing else.
5. **Keep it readable.** Few marks. If the chart is busy, the read is not clear yet.
6. **A trading range is drawn only when looking for a trade,** and only the one relevant to now (he, 19 Nov 2026:
   "the trading range should be drawn when you're looking for a trade"). Draw the higher timeframe's range before a
   lower one, and ask on each timeframe whether its trade has already passed (lesson 03, "The bigger trade").
7. **Say what was swept, as well as what is resting.** Eaten liquidity comes off the chart, but the read names it:
   "you would have to know it was a sweep, because this was a time to get interesting price action."
8. **An entry is only looked for inside his session times** (lesson 04). Outside them, read and mark; do not look
   for a trade.

## How a mark is made

- **Marks only, no text on the chart.** Words go in the read beside the chart, in the speak skill's wording.
- **Keep the read short.** The bias is not written as a sentence: set `bias` in `marks.json`
  (`{"1M": "bull", "1W": "bear", …}` with bull, bear or range) and the page shows one chip per timeframe, coloured
  green, red or grey ("just state the tf and color"). Under the chips come two short lists, in this order (his words:
  "next subset below the tf should be your interesting points, after that what you're currently considering"):
  `interesting` (what is interesting on the chart, above and below) and `considering` (what Claude is weighing right
  now, each a "might", never a prediction). One line per point, two or three points each.
- **Refer to a mark by its name, not by its price.** Write `[BISI 1M]`, `[EQH 1D]`, `[buyside 1h]`: the mark's `kind` and
  its `tf` in square brackets. The page shows it as a tag in that mark's colour, and the chart carries the same name on
  the mark. No prices in the read. (He: "price is annoying to read, your chart covers that, just let me know it's BISI
  1M.") So every mark needs a plain `kind` and its `tf`, and two marks on one timeframe must not share a name. No reasons, history or caveats: if he wants the why, he asks. (He, 18 Nov 2026: "it's a
  lot of context I have to read every time… the chart's content should already help me see what's going on.")

## Where the marks go

The chart is `v2/chart/`: a page that shows candles and marks, and nothing else.

- **Claude's marks:** `v2/chart/marks.json`. Per instrument: `marks`, `read` (the lines shown in the right panel) and,
  rarely, `notes` (`t`, `price`, `tf`, `text`: a short note pinned on the chart; he asked for no text on the chart, so
  use one only when he asks);
  `at` at the top says when it was written. A mark has `kind` (its short label), `tf`, `t0`, `t1` (null while it is
  still in play) and a `shape`:
  - `level`: `price`
  - `zone`: `top`, `bottom`
  - `line`: `p0` at `t0` to `p1` at `t1`
  - `vline`: a vertical line at `t0` (a change of bias, for example)
- **Times** are New York clock times as epoch seconds, the same as the candles the page serves
  (`/api/candles?asset=<NAME>&tf=<TF>`), so take `t0` and `t1` from those candles.
- **Page:** `http://127.0.0.1:8776/?asset=<NAME>&tf=<TF>` (several charts: `?assets=A,B&tf=<TF>`). One page, laid out
  like TradingView: instrument and interval along the top, his drawing tools down the left, the watchlist and Claude's
  read on the right, replay along the bottom. **Replay** takes every chart back to a moment and shows nothing after it:
  use it to show a concept back on a chart without seeing what came next. If the page is down:
  `uv run python v2/chart/server.py --host 0.0.0.0 --password-env LIVE_PAGE_PASSWORD` (only port 8776 may listen on
  the network). Fresh candles: the **● Live** switch on the page keeps the instruments shown up to date (about a
  minute behind) while it is on; it is his switch, so ask before relying on it. By hand:
  `uv run python v2/chart/fetch.py <NAME>`, then press refresh. Candle files only go as far as the last time an
  instrument was live or fetched: say how recent the data is whenever you read a chart.
- **The mode:** `v2/chart/mode.json` (`learn`, `hunt` or empty). The page shows it at the top left with a coloured
  strip; the pipelines set it.
- **His notes:** he writes in the **Notes** tab of the right panel; each is saved under the current mode; each is appended to
  `v2/chart/notes.jsonl` with the instrument, the timeframe and the time the chart was showing. He prefers this to
  writing on the chart ("writing on the chart gets too messy"). Read them; never edit them.
- **Colours:** every kind of mark has its own colour (`KIND_COLOR` in `v2/chart/marks.js`), the same whoever drew it.
  Claude's marks are dashed and labelled "C ·"; his are solid and labelled "S ·". Use his kind names ("EQL",
  "buyside", "BISI", "order block", "level behind"…) in a mark's `kind` so it takes that colour; a free label takes
  the colour of the kind it names.
- **His tools:** snap (the magnet, M) puts a point exactly on a candle's open, high, low or close; double-click locks
  or unlocks a mark; a block's corners size it both ways. A mark of his may carry `locked: true`: it means only that he
  fixed it in place.
- **His marks:** he draws with the tools on the left and presses save; marks and notes are appended to
  `v2/chart/saves.jsonl` (with `chart_time` when the chart was in replay). Read them; never edit them.

## Before saying the marks are there

Open the page and look. Take a picture of each timeframe that was drawn on and check the marks show where intended.
Say which views were looked at and which were not.

## After he corrects a mark

In a learn session: fix it and show it again. In a hunt: fix it on the chart, and write the correction in the day's
hunt notes; the brain is not changed (see the hunt pipeline).
