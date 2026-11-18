---
name: context-check
description: Check that what entered v2 is the context Sharif taught and not a copy of the example he showed - for a concept's lesson, its links, its tools and its tests, and for hunt notes. Catches prices, clock times, timeframes and instruments lifted from an example, links without a status, fixed statements about what price "is doing", rules with no words of his behind them, and tests that lean on a real day instead of testing the idea. Use at the end of every learn session, whenever a lesson, link, tool or test in v2 is added or changed, before ticking a box in v2/MIGRATION.md, and whenever Sharif says "validate", "check", "context check", "are you copying my example" or asks whether something was built the right way.
---

# Context check

Sharif rebuilt this project as v2 because v1 was damaged in one specific way: Claude turned his worked examples into
rules. A price, a time of day, a timeframe or a fitted margin from one chart became "the rule", and tools and tests
were tuned to reproduce that chart. His words: "you're still locking in specific values to what you're learning, and
not taking in context" and "if I give you a different chart you'll be confused."

This skill checks that a v2 concept did not do that. It has two halves. The script finds what can be found
mechanically. The reading is the part that matters and cannot be skipped: only a reader can tell whether the code
carries the **reason** he gave or a **copy** of what he showed.

## 1. Run the script

```bash
uv run python .claude/skills/context-check/check.py              # every concept, and the hunt notes
uv run python .claude/skills/context-check/check.py 02_liquidity # one
```

- `FAIL` lines must be fixed before anything else. They are the give-aways: a value from the lesson's examples in the
  code or tests, a named timeframe or instrument in a tool, a test that leans on a real day, an import from v1, a tool
  without tests, no test across price scales and timeframes, no no-look-ahead test, a lesson without his words,
  a link that carries a clock time, a price, a timeframe or an instrument, a link without a status, a link that
  states what price "is doing".
- A lesson with no links is reported as "no links yet". That is not a failure: links are added in learn, when he
  states them.
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

### Links and lessons get the same reading

For every row of a lesson's Links table, and every sentence of the lesson that is not a quote of his:

- **Is this the context, or the example?** His own illustration: "notice what happened with price at 8:21, it left a
  FVG." The lesson is not 8:21; "that time won't always leave a FVG." The lesson is a FVG found in an interesting
  area. If a sentence would be false on another day or another chart, it is the example.
- **Who stated the link?** "Stated by Sharif" only if he said it. Anything Claude noticed is "noticed by Claude,
  unconfirmed" and is not used until he confirms it.
- **Is it a fixed statement?** "Price is buying" is one. A lesson says what is interesting, tied to a timeframe and
  to now (see the speak skill).

## 3. Report

Lead with the verdict: **passes**, or **fails**, with the failing rows. Then the table, then the list of choices
that are yours, then the open questions for Sharif. If it fails, fix it and run the whole check again before saying
it is done. Only then tick the concept's box in `v2/MIGRATION.md` and add a line to its log.

## What this skill does not do

It does not say whether the concept is *right*: only Sharif's check on a chart you had not seen says that. It also
does not cover the eyes or how the brain pulls a lesson; those come later.
