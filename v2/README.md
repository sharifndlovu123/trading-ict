# v2: the clean rebuild

Everything outside this folder is **v1 and deprecated** (Sharif, 17 Nov 2026: the earlier research was damaged by rules
fitted to examples and lessons locked to specific values). Everything the brain and the eyes need lives here.

## The folders

```
v2/
  README.md        this page
  MIGRATION.md     the checklist: where each concept stands
  concepts/        one numbered folder per concept, in the order Sharif teaches them
    01_bias/
      lesson.md        the brain's part: his words, the why, what it was confirmed on
      bias_eyes.py     the eyes' part: code that sees it on a chart
      test_bias.py     the tests that validate it
  brain/           how lessons are pulled together while price moves (empty until Sharif sets the design)
  references/      fixed sources v2 may cite (empty until each is re-checked with him)
```

**One concept = one folder.** Its lesson, its eyes and its tests sit together, so nothing about a concept is read from
anywhere else. The number is the order it was built in. A new concept is a new folder with the same three files.

## Rules
1. v2 never reads v1: no imports from `ict_engine` or `research/scripts`, no v1 notes as a source. (Raw candles are data and may be used.)
2. Only what Sharif has confirmed enters, in his words.
3. A lesson is its why, never a price, a time or a timeframe from an example.
4. Every claim has tests on hand-built candles. "Tests are included, because they validate what you claim."
5. Code is a second opinion beside the hand read; disagreements are written in the lesson as open questions.
6. Sharif starts each concept and says how it is done.

Run the tests: `uv run pytest -q v2`.
