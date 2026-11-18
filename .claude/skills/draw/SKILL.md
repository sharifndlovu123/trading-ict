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
4. **Only what is in the brain.** Draw with concepts that are in `v2/concepts/`. Do not draw from v1's ideas.
5. **Keep it readable.** Few marks. If the chart is busy, the read is not clear yet.

## How a mark is made

- **Marks only, no text on the chart.** Words go in the read beside the chart, in the speak skill's wording.
- **Every mark ends.** Give it an end where it stopped mattering (eaten, filled, the week is over). Only what is
  still in play stays open.
- **Name the timeframe** each mark belongs to; it shows on that timeframe and the lower ones.
- **Say what it is in the label**, shortly: "EQL", "PWL", "alt: BISI", "level behind".

## Where the marks go (for now)

The chart page is a display borrowed from v1 until v2 has its own. Nothing in v2 reads from it.

- Marks: `v1/out/live/overlay.json`, per instrument: `marks` (a level: `price`; a zone: `top` and `bottom`; a line:
  `shape: "trend"` with `p0`, `p1`; each with `kind`, `tf`, `side`, `t0`, `t1`, `watch: false`) and `read` (the lines
  shown beside the chart).
- Page: `http://127.0.0.1:8776/?asset=<NAME>&tf=<TF>`. If it is down, start it from `v1/` (see `v1/README.md`); only
  port 8776 may listen on the network. Start the feed by hand when fresh candles are needed.

## Before saying the marks are there

Open the page and look. Take a picture of each timeframe that was drawn on and check the marks show where intended.
Say which views were looked at and which were not.

## After he corrects a mark

In a learn session: fix it and show it again. In a hunt: fix it on the chart, and write the correction in the day's
hunt notes; the brain is not changed (see the hunt pipeline).
