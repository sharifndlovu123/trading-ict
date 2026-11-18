---
name: hunt
description: The HUNT pipeline - the ordered steps for Claude watching a market for itself, drawing what is interesting, and noting Sharif's corrections without changing the brain. Use when Sharif says "hunt", "go hunt", "watch the market", "what do you see live", or asks to switch hunting on or off. Hunts are currently OFF - this skill's first step handles that.
---

# Hunt

**Say first, in one line: "Hunt pipeline."**

The goal this serves, in Sharif's words: "You're watching the market live for yourself and you're seeing these
patterns and pointing them out and drawing them yourself, to the point where you can place limits and stops
yourself. That's the GOAL."

## Step 0: are hunts on?

Read `CLAUDE.md`, "Where things stand". **If it says hunts are off, answer in one line that hunts are off and ask
whether he wants them on. Run nothing else.** Only Sharif switches hunting on; when he does, update that line in
`CLAUDE.md` and `v2/hunts/README.md` first.

## Show the mode on the chart

Sharif: "we should be able to clearly tell when it's in hunt or learn mode." The chart page shows the mode at the top
left (LEARN blue, HUNT orange, OFF) with a coloured strip across the page, and saves his notes under it.

- **When this pipeline starts and hunts are on,** write the mode: `{"mode": "hunt", "by": "Claude", "at": <epoch seconds>}` into
  `v2/chart/mode.json`. The page picks it up within a few seconds.
- **When it ends,** write `"mode": ""` (no session).
- **He can set it himself** on the page. Read `v2/chart/mode.json` when a session starts: if he has set a mode that
  differs from what you were about to run, say so and ask which he means. If the page says HUNT while hunts are off,
  that is him asking: answer that hunts are off and ask whether to switch them on.

## The steps (once hunts are on)

| # | Step | Who |
|---|---|---|
| 1 | Where is price now. Start from a clean chart (skill: **draw**) | Claude |
| 2 | Read top-down using the concepts in `v2/concepts/`, and only those. *The eyes are not built yet: until they are, this is a hand read with the concepts' tools as a second opinion* | Claude |
| 3 | Draw what is interesting, relative to now (skills: **draw**, **speak**) | Claude |
| 4 | Say what the brain brings to mind from the lessons' links: "this might be this". *Pulling is not built yet: until it is, read the Links tables by hand and use only links stated by Sharif* | Claude |
| 5 | He corrects: "this is missing", "do this, don't do this", or better context, in the chat or in the chart's **Notes** panel (kind "hunt"; read `v2/chart/notes.jsonl`). Write each correction in today's notes, `v2/hunts/YYYY-MM-DD.md`, in his words, with the chart it was about | both |
| 6 | When the hunt ends, leave the notes for the **day-review** | Claude |

## What a hunt never does

- **It never changes the brain.** No lesson, link, tool or test is written or edited during a hunt. Corrections are
  held: "hold them, then we go through the notes together, then at the end of the trading day we discuss it further
  and properly implement it into the brain."
- **It never goes past the stage he has set.** The stage is in `v2/hunts/README.md`. Claude does not move itself up.
- **It never states what price is doing.** See **speak**.
- **It uses only what is in v2.** No playbook, watcher, prep, scan or rule from before v2.

If he starts teaching in the middle of a hunt: say the hunt is paused. What he says is noted and held like any
correction, unless he says "learn", which starts the learn pipeline.
