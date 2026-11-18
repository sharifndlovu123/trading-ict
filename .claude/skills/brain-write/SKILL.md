---
name: brain-write
description: How a lesson and its links are written into v2's brain (v2/concepts/NN_name/lesson.md). Use only inside the learn pipeline, after Sharif has said the lesson is done, or when adding a link or more context he has confirmed in a day review. Never during a hunt.
---

# Brain write

The brain is made of Sharif's reasoning. This skill is the only way anything is written into it.

## When

- Only in **learn**, and only after he says the lesson is done. While he is still teaching, nothing is written.
- Never in a hunt. A hunt writes notes (`v2/hunts/`), and those reach the brain only through the day review.

## A lesson (`v2/concepts/NN_name/lesson.md`)

1. **Standing first:** when it was taught, what it was confirmed on, and whether it has been tested on a chart Claude
   had not seen.
2. **His words, quoted,** for every point. If a point has no quote, it is Claude's.
3. **Anything of Claude's is named as Claude's** ("mine, not his"), in the lesson and in any tool that uses it.
4. **The why, not the example.** He: "you're taking the context, you're not doing it exactly as I stated." A price,
   a clock time, a timeframe or an instrument from the chart he taught on is an illustration. If it is kept at all,
   it sits under a heading that says it is an example, never inside a rule.
5. **His corrections stay visible:** what Claude got wrong and what he said. They are the best part of the lesson.
6. **Open questions** at the end: what was not taught, so nobody guesses it later.

## Links (the part that makes it a brain)

A concept alone does not read a market. A link says what brings it to mind and what to look for next. He: "when we
see this set of liq swept through and displacement, look for a FVG then."

Every lesson gets a section:

```markdown
## Links

| Comes to mind when | Then look for | Status |
|---|---|---|
| liquidity is swept and displacement follows | an imbalance left by that displacement, in an interesting area | stated by Sharif, 18 Nov 2026 |
```

- **Status is one of two:** `stated by Sharif, <date>` (he said it) or `noticed by Claude, unconfirmed` (Claude saw
  the connection). An unconfirmed link is shown to him and is not used until he confirms it.
- **A link is context.** No clock time, price, timeframe or instrument in it. It must hold on any chart, any day.
- **A link is a "might be".** It says what to look for, not what will happen.
- Links may point to another concept by name. If that concept is not in v2 yet, say so in the row.

## Afterwards

Run the context check on the concept (`uv run python .claude/skills/context-check/check.py NN_name`, then its
reading), and update `v2/MIGRATION.md`.
