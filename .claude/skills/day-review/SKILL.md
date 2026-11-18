---
name: day-review
description: The DAY REVIEW pipeline - going through the corrections held from the day's hunt with Sharif and deciding which become lessons. Use at the end of a trading day, when Sharif says "review the day", "go through the notes", "what did we note today", or when a hunt has ended and its notes are waiting.
---

# Day review

**Say first, in one line: "Day review pipeline."**

A correction made during a hunt is about one chart on one day. This is where it is decided whether it is a lesson.
Sharif: "then at the end of the trading day we discuss it further and properly implement it into the brain."

The chart's mode is set to no session during a day review (`"mode": ""` in `v2/chart/mode.json`): it is neither a
lesson nor a hunt until a note is taken into learn.

## The steps

| # | Step | Who |
|---|---|---|
| 1 | Open today's notes, `v2/hunts/YYYY-MM-DD.md`, and his own "hunt" notes from the chart's Notes panel (`v2/chart/notes.jsonl`). Go through them together, one at a time, in the order they happened | both |
| 2 | For each one, he says which it is: **a lesson**, **more context for a lesson already in the brain**, or **only about that day** | Sharif |
| 3 | "A lesson" or "more context": take it through the **learn** pipeline from step 5 (he says it is done, then **brain-write**, links, tools and tests if needed, **context-check**). "Only about that day": it stays in the notes, marked so | Claude |

## Rules

- **He decides, per note.** Claude may say what it thinks a note is, but does not file it before he answers.
- **The context, not the day.** When a note becomes a lesson, the day's price, time, timeframe and instrument stay
  behind in the notes as the illustration.
- **Every note ends the review with a mark:** `-> lesson (NN_name)`, `-> context (NN_name)` or `-> that day only`.
  No note is left undecided; if he wants to think about one, mark it `-> open` and bring it back next review.
