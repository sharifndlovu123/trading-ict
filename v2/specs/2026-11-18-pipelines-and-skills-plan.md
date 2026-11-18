# Pipelines and Skills for v2: Implementation Plan

**Goal:** Give v2 three pipeline skills (learn, hunt, day review) and four small skills (context check, draw, brain
write, speak), so Claude always knows which mode it is in and nothing reaches the brain as a copy of an example.

**Architecture:** Every pipeline and small skill is one `SKILL.md` under `.claude/skills/<name>/`, about a page each.
Only the context check has code (`check.py`), and that code has tests. Hunt is written but answers "hunts are off".

**Spec:** `v2/specs/2026-11-18-pipelines-and-skills.md` (approved by Sharif, 18 Nov 2026). Built in this session by
Claude (he said "approved, build it").

## Global constraints (from the spec)

- All of it is v2. Nothing is taken from v1's hunting, playbook, watcher, preps or skills.
- No skill has two modes. One pipeline runs at a time, and its first line says which.
- The brain changes only in learn, with Sharif present. A hunt writes notes, never lessons.
- No hooks or file locks.
- A lesson without links is reported, not failed.
- The speaking rule applies everywhere and also goes in `CLAUDE.md`.
- Each skill is short enough to read in a minute.

## Review focus (what is most likely to go wrong in use)

1. A link written with a clock time, a price, a timeframe or an instrument in it. → the check fails it (test).
2. A lesson or hunt note stating what price "is doing" as a fact. → the check flags it (test).
3. A link Claude noticed being treated as confirmed. → the check requires a status on every link (test).
4. "Hunt" said while hunts are off. → the hunt skill's first step answers "hunts are off" and stops.
5. An existing concept with no Links section failing on day one. → reported as "no links yet" (test).

## Tasks

### Task 1: context check (rename, widen, test)
- Move `.claude/skills/v2-concept-check/` → `.claude/skills/context-check/`; frontmatter `name: context-check`.
- `check.py` gains, per concept folder:
  - `links(text) -> list[dict]`: rows of the `## Links` table: `{"when", "then", "status"}`.
  - no `## Links` section → an info line "no links yet" (never a FAIL).
  - a link row with a clock time (`8:21`), a number of four or more digits, a named timeframe or an instrument → FAIL.
  - a link row whose status is not "stated by Sharif …" or "noticed by Claude, unconfirmed" → FAIL.
  - `flat_statements(text) -> list[str]`: phrases such as "price is buying / selling / bullish / bearish" outside his
    quotes → JUDGE in a lesson, FAIL in a link.
  - hunt notes (`v2/hunts/*.md`): the same flat-statement scan, reported as JUDGE.
  - `check(folder, migration_text)` takes the checklist text as an argument so it can be tested on a made-up folder.
- Tests: `v2/skills_tests/test_context_check.py`, on concept folders built in a temporary directory: a clean link
  passes; a link with a time, a price, a timeframe, an instrument each fail; a link with no status fails; no Links
  section is "no links yet" and not a failure; a flat statement is flagged in a lesson and fails in a link; a quote
  of his containing the phrase is not flagged.
- `SKILL.md`: the reading table gains a row type for links, and the question "is this the context, or the example?"
  is asked of every lesson sentence and link.

### Task 2: the three small skills
- `.claude/skills/speak/SKILL.md`: "interesting"; never "price is buying / selling"; every statement tied to a
  timeframe and to now; a pattern is "might be"; before / after examples.
- `.claude/skills/draw/SKILL.md`: relative to now; from the weekly down; original liquidity before alt-liquidity;
  every mark ends; no text on the chart; the overlay file and its mark shapes; start the page from `v1/` if it is
  down; look at the page before saying the marks are there.
- `.claude/skills/brain-write/SKILL.md`: written only after he says the lesson is done; his words quoted with the date
  and what it was confirmed on; anything of Claude's named as Claude's; the Links table and its two statuses; examples
  kept as illustrations, never as the rule.

### Task 3: the three pipelines
- `.claude/skills/learn/SKILL.md`: the nine steps of the spec.
- `.claude/skills/hunt/SKILL.md`: step 0 "are hunts on?" (read `CLAUDE.md`, "Where things stand"); if off, say so,
  ask, stop. Then the six steps, with 2 and 4 marked not available until the eyes and the pulling exist. The stage
  Sharif has set (1 to 4) is read from `v2/hunts/README.md`.
- `.claude/skills/day-review/SKILL.md`: the three steps.
- `v2/hunts/README.md`: the current stage (1), and the layout of a hunt-notes file.

### Task 4: wiring
- `CLAUDE.md`: a "Pipelines" section (which word starts which), the speaking rule, the renamed check.
- `v2/README.md`, `v2/MIGRATION.md`: skills table, the new item "chart viewer moved to the root, out of v1" (Sharif,
  18 Nov 2026: "at some point"), log line. `pyproject.toml` unchanged (`v2` is already a test path).
- Memory: `v2-rebuild.md` gains the pipelines, the goal in his words and the speaking rule.
- Remove the empty leftover folders `v2/engine` and `v2/tests`.

### Task 5: verify and commit
- `uv run ruff check v2 .claude/skills`, `uv run python .claude/skills/context-check/check.py`, `uv run pytest -q v2`.
- Commit. Do not push.
