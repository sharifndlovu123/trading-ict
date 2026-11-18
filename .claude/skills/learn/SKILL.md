---
name: learn
description: The LEARN pipeline - the ordered steps for a teaching session in which Sharif explains a concept and Claude takes it into v2's brain. Use when Sharif says "learn", "let me teach you", "lesson", names a concept to work on, starts explaining what price did on a chart, or asks Claude to show a concept back on a chart. This is the only pipeline in which the brain changes.
---

# Learn

**Say first, in one line: "Learn pipeline."** Only this pipeline is running. If it is not clear whether he means
learn or hunt, ask once.

In learning Sharif is explaining: "look at what price did here, it swept this area and had displacement afterwards."
He is mostly giving the answer, or teaching outright. The job is to take in the **reason**, so it can be used when
learning the next thing and when hunting. Learning is also where the brain is built: concepts, and the links between
them.

## The steps

| # | Step | Who |
|---|---|---|
| 1 | Name the concept. Say what already in the brain it might link to | Claude |
| 2 | He explains on a chart, or Claude asks one question at a time and he defines. **Nothing is written while he is still teaching** | Sharif |
| 3 | Show it back on a chart Claude has not seen, by drawing (skills: **draw**, **speak**). Give the read first, then the reasons | Claude |
| 4 | He corrects, in the chat, with his own marks on the chart (`v2/chart/saves.jsonl`) or in the chart's **Notes** panel (kind "learn"; `v2/chart/notes.jsonl`). Read all three. Repeat 3 and 4 until he says it is right | Sharif |
| 5 | He says the lesson is done. Only then write it (skill: **brain-write**) | Claude |
| 6 | Write the links: what brings this to mind, what to look for next. His are confirmed; Claude's are marked unconfirmed | Claude |
| 7 | If it is something found on a chart: its tools and their tests, on hand-built candles | Claude |
| 8 | Run the **context-check** on the lesson, links, tools and tests. Fix what it finds | Claude |
| 9 | Update `v2/MIGRATION.md` | Claude |

## Rules for the whole session

- **He leads.** He names the concept and says how it is done. Do not plan concepts ahead of him.
- **Context, not the example.** "The market is a snowflake pattern, it differs every day." A time, price, timeframe
  or instrument from his chart is an illustration of the idea.
- **Do not do too much.** Fix what he pointed at. One question at a time.
- **Relative to now.** "Focus on where price currently is, and never try to make the market do what it wants."
- **Tests are part of every tool.** "Tests are included, because they validate what you claim."
- If he says "pause" or "the lesson isn't done", stop writing and keep listening.

## It is finished when

He has said the lesson is done, the lesson and links are written in his words, the context check passes, and the
checklist is updated. A concept Claude can define but that links to nothing is not finished: say so.
