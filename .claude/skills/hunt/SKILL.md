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

## The steps (once hunts are on)

| # | Step | Who |
|---|---|---|
| 1 | Where is price now. Start from a clean chart (skill: **draw**) | Claude |
| 2 | Read top-down using the concepts in `v2/concepts/`, and only those. *The eyes are not built yet: until they are, this is a hand read with the concepts' tools as a second opinion* | Claude |
| 3 | Draw what is interesting, relative to now (skills: **draw**, **speak**) | Claude |
| 4 | Say what the brain brings to mind from the lessons' links: "this might be this". *Pulling is not built yet: until it is, read the Links tables by hand and use only links stated by Sharif* | Claude |
| 5 | He corrects: "this is missing", "do this, don't do this", or better context. Write each correction in today's notes, `v2/hunts/YYYY-MM-DD.md`, in his words, with the chart it was about | both |
| 6 | When the hunt ends, leave the notes for the **day-review** | Claude |

## What a hunt never does

- **It never changes the brain.** No lesson, link, tool or test is written or edited during a hunt. Corrections are
  held: "hold them, then we go through the notes together, then at the end of the trading day we discuss it further
  and properly implement it into the brain."
- **It never goes past the stage he has set.** The stage is in `v2/hunts/README.md`. Claude does not move itself up.
- **It never states what price is doing.** See **speak**.
- **It never uses v1.** No v1 playbook, watcher, prep, scan or rule.

If he starts teaching in the middle of a hunt: say the hunt is paused. What he says is noted and held like any
correction, unless he says "learn", which starts the learn pipeline.
