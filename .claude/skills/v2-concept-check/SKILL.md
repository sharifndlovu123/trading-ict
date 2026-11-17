---
name: v2-concept-check
description: Validate a v2 concept (v2/concepts/NN_name: lesson, tools, tests) before calling it done - that the tools follow what Sharif taught in context and are not replicas of his examples, that nothing is locked to a price, time, timeframe or instrument, that every rule traces to his words or is named as Claude's own choice, and that tests on hand-built candles validate each claim. Use whenever a concept is added or changed in v2, when a lesson is written or edited, before ticking a box in v2/MIGRATION.md, when Sharif says "validate", "check the process", "are you copying my example", or asks whether a tool was built the right way; also run it on every existing concept after any change to v2's rules.
---

# v2 concept check

Sharif rebuilt this project as v2 because v1 was damaged in one specific way: Claude turned his worked examples into
rules. A price, a time of day, a timeframe or a fitted margin from one chart became "the rule", and tools and tests
were tuned to reproduce that chart. His words: "you're still locking in specific values to what you're learning, and
not taking in context" and "if I give you a different chart you'll be confused."

This skill checks that a v2 concept did not do that. It has two halves. The script finds what can be found
mechanically. The reading is the part that matters and cannot be skipped: only a reader can tell whether the code
carries the **reason** he gave or a **copy** of what he showed.

## 1. Run the script

```bash
uv run python .claude/skills/v2-concept-check/check.py              # every concept
uv run python .claude/skills/v2-concept-check/check.py 02_liquidity # one
```

- `FAIL` lines must be fixed before anything else. They are the give-aways: a value from the lesson's examples in the
  code or tests, a named timeframe or instrument in a tool, a test that leans on a real day, an import from v1, a tool
  without tests, no test across price scales and timeframes, no no-look-ahead test, a lesson without his words.
- `JUDGE` lines are for step 2.
- The script also runs `pytest v2`. Failing tests fail the check.

## 2. Do the reading

Open the concept's `lesson.md` (and any sub-part), its tools and its tests, and fill in this table in your answer.
One row per rule the code applies, not per function.

| Rule in the code | His words it comes from (quote) | Same idea, or a copy of the example? | Test that validates it |
|---|---|---|---|

For each row, ask these and be hard on yourself:

1. **Is there a quote?** If no sentence of his supports the rule, it is yours. It must be named as yours in the tool's
   docstring and in the lesson ("mine, not his"), and it should be the simplest choice available. A rule that is
   neither quoted nor named is a FAIL.
2. **Would it still be right on a chart he never showed?** Read the rule and imagine a different instrument, another
   timeframe, a market ten times the price. If the rule only makes sense on the chart from the lesson, it is a copy.
3. **Does the rule say why, or only what?** "A close through the level behind the bias is the change" carries the
   reason. "Bear when the weekly closes 0.1 ATR under the low" carries a number. Numbers need a quote or a "mine".
4. **Every number on a `JUDGE` line:** tie it to his words (5 p.m. and 6 p.m. are his definition of the opening gaps)
   or mark it as yours. A threshold with neither is a FAIL. Prefer handing the caller the choice (a parameter with no
   default) over burying a number.
5. **Did anything he said get left out?** Read the lesson once more for sentences with no row in the table. A lesson
   sentence with no code and no test is fine only if the lesson says it is a hand judgement.
6. **Do the tests test the idea?** Each test should fail if the idea were wrong, on candles built by hand for that
   purpose. A test whose expected values came from running the code on a real chart is a replica, not a test.
7. **Is what he corrected in there?** Each correction he made while teaching (they are in the lesson as "my mistake"
   or "he:") should have a test that would have caught the mistake.

Then compare with the hand read he confirmed, if the tool was run on that chart: differences are written in the
lesson as open questions. Never change the tool to make it match that chart.

## 3. Report

Lead with the verdict: **passes**, or **fails**, with the failing rows. Then the table, then the list of choices
that are yours, then the open questions for Sharif. If it fails, fix it and run the whole check again before saying
it is done. Only then tick the concept's box in `v2/MIGRATION.md` and add a line to its log.

## What this skill does not do

It does not say whether the concept is *right*: only Sharif's check on a chart you had not seen says that. It also
does not cover the eyes or the brain (the top-down process and how lessons are pulled); those come later.
