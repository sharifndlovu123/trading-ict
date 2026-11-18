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
2. **From the weekly down.** The higher timeframe first, then lower. It is far from price sometimes, and still first.
3. **Original liquidity before alt-liquidity.** Pools of stops first; imbalances second.
4. **Only what is in the brain.** Draw with concepts that are in `v2/concepts/`, and nothing else.
5. **Keep it readable.** Few marks. If the chart is busy, the read is not clear yet.

## How a mark is made

- **Marks only, no text on the chart.** Words go in the read beside the chart, in the speak skill's wording.
- **Every mark ends.** Give it an end where it stopped mattering (eaten, filled, the week is over). Only what is
  still in play stays open.
- **Name the timeframe** each mark belongs to; it shows on that timeframe and the lower ones.
- **Say what it is in the label**, shortly: "EQL", "PWL", "alt: BISI", "level behind".

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
  the network). Fresh candles: `uv run python v2/chart/fetch.py <NAME>`, then press refresh on the page.
- **His notes:** he writes in the **Notes** tab of the right panel, as "learn" or "hunt"; each is appended to
  `v2/chart/notes.jsonl` with the instrument, the timeframe and the time the chart was showing. He prefers this to
  writing on the chart ("writing on the chart gets too messy"). Read them; never edit them.
- **His marks:** he draws with the tools on the left and presses save; marks and notes are appended to
  `v2/chart/saves.jsonl` (with `chart_time` when the chart was in replay). Read them; never edit them.

## Before saying the marks are there

Open the page and look. Take a picture of each timeframe that was drawn on and check the marks show where intended.
Say which views were looked at and which were not.

## After he corrects a mark

In a learn session: fix it and show it again. In a hunt: fix it on the chart, and write the correction in the day's
hunt notes; the brain is not changed (see the hunt pipeline).
