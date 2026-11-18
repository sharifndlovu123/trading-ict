# v2: the clean rebuild

Everything outside this folder is **v1 and deprecated**, and since 18 Nov 2026 it sits under `../v1/` (Sharif,
17 Nov 2026: the earlier research was damaged by rules fitted to examples and lessons locked to specific values).
Everything the brain and the eyes need lives here.

## The folders

```
v2/
  README.md        this page
  MIGRATION.md     the checklist: where each concept stands
  concepts/        one numbered folder per concept, in the order Sharif teaches them
    01_bias/
      lesson.md        the lesson: his words, the why, what it was confirmed on
      bias.py          the tool: code that finds it on a chart
      test_bias.py     the tests that validate it
    02_liquidity/
      lesson.md        liquidity: what it is, how to read it (relative to now, from the weekly down)
      alt-liquidity.md its sub-part: imbalances price is drawn to
      liquidity.py, alt_liquidity.py     the tools
      test_liquidity.py, test_alt_liquidity.py
  brain/           how lessons are pulled together while price moves (empty until Sharif sets the design)
  hunts/           the hunt stage he has set, and one notes file per hunting day (hunts are off)
  specs/           design documents he approved
  skills_tests/    tests for the skills' own code
  references/      fixed sources v2 may cite (empty until each is re-checked with him)
```

**One concept = one folder.** Its lesson, its tools and its tests sit together, so nothing about a concept is read from
anywhere else. The number is the order it was built in. A new concept is a new folder with the same three kinds of file.

**How work is done:** through the pipelines in `.claude/skills/` (`learn`, `hunt`, `day-review`) and the small skills
they use (`context-check`, `draw`, `brain-write`, `speak`). Design: `specs/2026-11-18-pipelines-and-skills.md`.

**The eyes and the brain come later** (Sharif, 18 Nov 2026): the eyes are the top-down process that uses a range of
concepts together, and the brain is how lessons are pulled while price moves. Neither is built until the concepts
they need are in. What is built now, concept by concept, is the lesson, its tools and their tests.

## Rules
1. v2 never reads v1: no imports from `ict_engine` or `research/scripts`, no v1 notes as a source. (Raw candles are data and may be used.)
2. Only what Sharif has confirmed enters, in his words.
3. A lesson is its why, never a price, a time or a timeframe from an example.
4. Every claim has tests on hand-built candles. "Tests are included, because they validate what you claim."
5. Code is a second opinion beside the hand read; disagreements are written in the lesson as open questions.
6. Sharif starts each concept and says how it is done.
7. Before a concept is called done, it goes through the `context-check` skill (`.claude/skills/context-check/`): a script for the give-aways and a reading of the code against his words, to make sure the logic was taken in context and is not a replica of an example.

Run the tests: `uv run pytest -q v2`.
