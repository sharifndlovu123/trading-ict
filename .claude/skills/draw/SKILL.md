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

- **Claude's marks:** `v2/chart/marks.json`. Per instrument: `marks` and `read` (the lines shown beside the chart);
  `at` at the top says when it was written. A mark has `kind` (its short label), `tf`, `t0`, `t1` (null while it is
  still in play) and a `shape`:
  - `level`: `price`
  - `zone`: `top`, `bottom`
  - `line`: `p0` at `t0` to `p1` at `t1`
  - `vline`: a vertical line at `t0` (a change of bias, for example)
- **Times** are New York clock times as epoch seconds, the same as the candles the page serves
  (`/api/candles?asset=<NAME>&tf=<TF>`), so take `t0` and `t1` from those candles.
- **Page:** `http://127.0.0.1:8776/?asset=<NAME>&tf=<TF>`. If it is down:
  `uv run python v2/chart/server.py --host 0.0.0.0 --password-env LIVE_PAGE_PASSWORD` (only port 8776 may listen on
  the network). Fresh candles: `uv run python v2/chart/fetch.py <NAME>`, then press refresh on the page.
- **His marks:** he draws with the buttons under the chart and presses save; they are appended to
  `v2/chart/saves.jsonl`. Read them; never edit them.

## Before saying the marks are there

Open the page and look. Take a picture of each timeframe that was drawn on and check the marks show where intended.
Say which views were looked at and which were not.

## After he corrects a mark

In a learn session: fix it and show it again. In a hunt: fix it on the chart, and write the correction in the day's
hunt notes; the brain is not changed (see the hunt pipeline).
