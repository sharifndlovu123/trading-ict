# Pipelines and skills for v2: design

Status: draft for Sharif's approval. Written 18 Nov 2026 from our conversation; read once by a reviewer, whose
questions are answered below. Nothing in it is built yet.

## Why this exists

The first version was damaged because Claude did not keep two kinds of work apart. Sharif would teach on a chart ("notice what
happened with price at 8:21, it left a FVG") and Claude would carry the example into a rule: that time, that price,
that timeframe. Lessons became fixed values, tools were tuned to reproduce a day, and the hunting that ran on top of
them could not be trusted.

Sharif: "We need to build pipelines so whenever I say learn or hunt you know the difference between the two." "It
helps ensure we don't repeat the same mistake." "This is the highest importance because it will assist us to grow the
system well enough."

## The goal it serves (his words)

"You're watching the market live for yourself and you're seeing these patterns and pointing them out and drawing them
yourself, to the point where you can place limits and stops yourself. That's the GOAL. That takes time because I'm
trying to transfer my thinking into you. Up to the point where you might see this better than me."

This is the brain and the eyes he described earlier: "built like a brain, almost some sort of neural network… if you
see this, pull this piece of information", and "you drawing what you see allows me to properly understand what you're
telling me; that's the easiest way to communicate to me."

## What he decided

1. **One pipeline per word.** Saying "learn" runs the learn pipeline and nothing else; saying "hunt" runs the hunt
   pipeline and nothing else. No skill has two modes.
2. **Clear, concise skills, each with one job,** and pipelines that put them in order "so everything works as expected".
3. **Learning builds the brain.** It produces concepts (what a thing is) and links between them ("when we see this set
   of liq swept through and displacement, look for a FVG then"), so the brain "can identify patterns within the market
   and say this might be this".
4. **Corrections made during a hunt are held.** "Hold them, then we go through the notes together, then at the end of
   the trading day we discuss it further and properly implement it into the brain."
5. **Context, not the example.** "The market is a snowflake pattern, it differs every day… you're taking the context,
   you're not doing it exactly as I stated." The context check is the guard, and it is also "the testing of a concept
   is correct and not fixed values".
6. **Drawing is the language** in both modes. In learning it proves the lesson was taken in; in hunting "your focus
   will be drawing on live charts, and I'll correct you or tell you this is missing, or do this, don't do this, or
   provide better context".
7. **How Claude speaks.** "Focus on the key word interesting; don't ever say price is buying nor selling, because we
   don't want a fixed statement, it's fluid, like when writing the bias. It's relative to what's happening now: as much
   as weekly is bullish, hourly is bearish."
8. **Always relative to now.** "Focus on where price currently is, and never try to make the market do what it wants.
   It must focus on what's recent and relative to now."
9. **A backtest pipeline comes later.** "It should be able to run these hunts with old data and once done the data is
   assessed… this time it's not just testing, you're running the hunter through old data and seeing what it produces."
   He pointed to how the old version showed results over different time periods and different assets.

## Goals

- Claude always knows which mode it is in, because only one pipeline runs at a time.
- The brain changes only in learn mode, with Sharif present.
- Nothing enters the brain as a copy of an example.
- Every pipeline and skill is short enough to read in a minute.

## Not goals

- Building the eyes (the top-down process that uses the concepts together) or how the brain pulls a lesson. Sharif
  will set those designs later. This document only fixes where they plug in.
- Turning hunting back on. Hunts stay off until he says.
- Rebuilding more concepts. That continues afterwards, through the learn pipeline.

## What would make this a failure even if it works

- A pipeline so long or strict that Sharif finds it "very complicated" and stops using it.
- A hunt correction reaching the brain without going through the day review and learn.
- Claude stating what price "is doing" as a fact, or a lesson carrying a time, price, timeframe or instrument.
- The check becoming a formality that passes replicas.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| **A (chosen)** | One pipeline skill per word (learn, hunt, day review, later backtest), each an ordered list of steps, plus small skills each step calls | More files, but the mode is never in doubt: one pipeline runs at a time |
| B | One "pipelines" skill holding every order, plus the small skills (how it was done before) | One place to read, but learn and hunt sit side by side in one file, which is how they bled into each other |
| C | No pipeline skills: the orders live in the project notes | Simplest, but the notes get heavy again and nothing enforces the order |

Sharif picked A.

## The pipelines

Each pipeline is a skill in `.claude/skills/<name>/SKILL.md`. Its first act is to say in one line which pipeline is
running. If Sharif's wording does not make the mode clear, Claude asks which one, once.

### Learn (starts on "learn", or when he begins teaching)

| # | Step | Who | Skill used |
|---|---|---|---|
| 1 | Name the concept, and say what it might link to that is already in the brain | Claude | |
| 2 | He explains on a chart, or Claude asks and he defines. Claude takes in the reason. **Nothing is written while he is still teaching** | Sharif | |
| 3 | Claude shows it back on a chart it has not seen, drawing what it sees | Claude | draw, speak |
| 4 | He corrects. Repeat 3 and 4 until he says it is right | Sharif | |
| 5 | He says the lesson is done. Only then is it written: his words, and anything of Claude's named as Claude's | Claude | brain write |
| 6 | The links are written: what brings this to mind, and what to look for next. A link he stated is confirmed; a link Claude noticed is marked as Claude's and is not used until he confirms it | Claude | brain write |
| 7 | Where the concept is something found on a chart: its tools and their tests | Claude | |
| 8 | The context check, on the lesson, the links, the tools and the tests | Claude | context check |
| 9 | The checklist is updated | Claude | |

### Hunt (starts on "hunt"; specified now, runs only when he switches hunting back on and the eyes exist)

| # | Step | Who | Skill used |
|---|---|---|---|
| 1 | Where is price now. A clean chart | Claude | draw |
| 2 | Read top-down with the concepts that are in the brain, and only those | Claude | (the eyes, later) |
| 3 | Draw what is interesting, relative to now | Claude | draw, speak |
| 4 | Say what the brain brings to mind: "this might be this", never a prediction | Claude | (brain pulling, later), speak |
| 5 | He corrects. Each correction is written in the day's hunt notes, in his words, with the chart it was about. **The brain is not changed** | both | |
| 6 | When the hunt ends: the notes are left for the day review | Claude | |

How far Claude goes in a hunt is a stage Sharif sets; Claude never moves itself up:
1. draws what it sees; 2. points out patterns; 3. says where a limit and a stop would go, on paper; 4. places them.
(These stages are Claude's proposal; Sharif has not yet confirmed them.)

### Day review (end of the trading day)

| # | Step | Who |
|---|---|---|
| 1 | Go through the day's hunt notes together, one at a time | both |
| 2 | For each, he says: a lesson, more context for an existing lesson, or only about that day | Sharif |
| 3 | "A lesson" or "more context" goes through the learn pipeline from step 5. "Only about that day" stays in the notes | Claude |

### Backtest (later; not built in this round)

Runs the hunt pipeline over old data and then assesses what it produced, across time periods and assets. What this
document fixes now, so it can be built later without redesign:
- It runs **the same hunt pipeline**, not a separate set of rules.
- At every step the hunter sees only what had happened by then (the chart is cut at "now").
- The brain is not changed by a backtest. What it surfaces goes to a review with Sharif, like hunt notes.
- When it is built, Sharif is asked first whether to look at how the old version stored and showed results per
  period and per asset (his suggestion). Its fixed rules and tuned values are not carried over, and v2 does not
  depend on it.
- How much of the hunter is tools and how much is Claude reading the chart is decided when the eyes are designed.

## The small skills

Each is `.claude/skills/<name>/SKILL.md`, one job, used by the pipelines above.

| Skill | Its one job | Built from |
|---|---|---|
| **context check** | Catch any lesson, link, tool or test that copied the example instead of the context, and confirm a concept's tests test the idea and not fixed values | The existing `v2-concept-check`, renamed and widened: today it checks tools and tests; it must also check lessons and links |
| **draw** | How marks go on a chart: relative to now, top-down, original liquidity before alt-liquidity, every mark ends, no text on the chart, look at the page after drawing | New |
| **brain write** | How a lesson and its links are recorded: his words quoted, the date and what it was confirmed on, anything of Claude's named as Claude's, a link's status (stated by him, or noticed by Claude and unconfirmed) | New |
| **speak** | Claude's wording: "interesting"; never "price is buying / selling"; each statement tied to its timeframe and to now; a pattern is "might be" | New |

## Where things are kept

| What | Where |
|---|---|
| A concept's lesson, tools, tests | `v2/concepts/NN_name/` (as now) |
| A concept's links | A "Links" section in its `lesson.md`: "comes to mind when…" and "then look for…" |
| Hunt notes (held corrections) | `v2/hunts/YYYY-MM-DD.md` |
| Pipelines and small skills | `.claude/skills/` at the top level |
| The eyes, and how the brain pulls | `v2/eyes/`, `v2/brain/`: empty until Sharif sets the designs |

Links are written as plain sentences for now. How they are stored for pulling (the "neural network") is part of the
brain design he will discuss later; the sentences are written so they can be moved into whatever that becomes.

## What gets built in this round

All three pipeline skills (learn, hunt, day review) and the four small skills. The backtest pipeline is not built.

- **Hunt is written now but stays switched off.** While hunts are off, saying "hunt" gets one line back: hunts are
  off, and does he want them on. It runs nothing. Its steps 2 and 4 are marked "not available yet" until the eyes and
  the brain's pulling exist, so when he does switch hunting on early, Claude can only draw what the concepts in the
  brain let it see.
- **Day review is written now** and is usable as soon as there is a hunt-notes file.
- **Concepts 01 and 02 have no links yet.** The context check reports a lesson without a Links section as "no links
  yet", not as a failure. Their links are added through learn, when Sharif states them. A sub-part file such as
  `alt-liquidity.md` may carry its own Links section.

## How the separation is kept

By the pipelines themselves and by the context check, not by anything that blocks Claude's hands. There are no
hooks or locks on the files. Reason: a lock would make the system harder to use and to change, and the failure this
guards against (a replica reaching the brain) is one a reader catches and a lock does not.

## How the draw skill puts marks on the chart

(Changed 18 Nov 2026, the same day, when Sharif asked that nothing outside the old version point into it: the chart
was rebuilt clean in `v2/chart/`.)

- Marks go in `v2/chart/marks.json`: per instrument, a list of marks (a level, a zone, a line or a vertical line;
  each with its timeframe, a start and an end) and the words shown beside the chart.
- After drawing, Claude opens the page and looks at it before saying the marks are there.
- The page (port 8776) is `v2/chart/server.py`. It shows candles and marks and nothing else. What Sharif draws and
  saves is kept in `v2/chart/saves.jsonl`.

## Where the speaking rule applies

Everywhere, not only inside a pipeline: he said "don't **ever** say price is buying nor selling". So the rule is
also written into `CLAUDE.md`, the speak skill holds the detail and examples, and the context check flags a lesson
or a hunt note that states what price "is doing" as a fact.

## Decided by Claude, for Sharif to overrule

- "Learn" also starts when he simply begins teaching, without the word.
- If he starts teaching in the middle of a hunt, the hunt pauses and Claude says so. What he teaches is treated as a
  correction (noted and held) unless he says "learn".
- The four hunt stages listed above.
- `v2-concept-check` is renamed `context-check`.
- Links live inside each lesson for now, not in a separate brain file.
- Marks are drawn on v2's own chart page (port 8776, `v2/chart/`).
- The backtest pipeline is designed in detail only after the eyes exist.
- Hunt is written now but answers "hunts are off" until he switches them on.
- A lesson without links is reported, not failed.
- No hooks or file locks; the pipelines and the context check keep the modes apart.
- The speaking rule applies to everything Claude says and writes, and goes in `CLAUDE.md` too.

## Left to the builder

- The exact wording of each skill, kept to about a page.
- How the context check reads a lesson and its links mechanically (which give-aways a script can catch) and what it
  leaves to the reading.
- The layout of a hunt-notes file.
- Adding the pipelines and skills to `CLAUDE.md` and the migration checklist.
