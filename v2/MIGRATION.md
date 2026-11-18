# Migration to v2: checklist

**This week's objective (Sharif, 18 Nov 2026; the week of 16 to 20 November 2026): "cleaning up our mess."** No hunting, no new strategies. The work is moving what is worth keeping into v2, one concept at a time with him, and retiring v1.

Update whenever a box changes. `[x]` done · `[~]` partly (see the note) · `[ ]` not started.

## Concepts (one folder each under `concepts/`)

| Box | Meaning |
|---|---|
| Taught | Sharif taught it and confirmed my hand read on a chart I had not seen |
| Lesson | `lesson.md` written: his words, the why |
| Tools + tests | The concept's tools find it on a chart, with passing tests on hand-built candles |
| In use | The hunt reads it from v2, not v1 |

| # | Concept | Taught | Lesson | Tools + tests | In use |
|---|---|---|---|---|---|
| 01 | Bias | [x] | [x] | [x] | [ ] |
| 02 | Liquidity, with alt-liquidity (imbalances as draws) | [x] | [x] | [x] | [ ] |

Note on 01: the tool agrees fully with his confirmed read on the DAX, on direction on the dollar index, and differ on
the FTSE. The open questions are in `concepts/01_bias/lesson.md`.

Note on 02: the lesson and its alt-liquidity sub-part are written from his answers. Tested on the FTSE and confirmed ("I'm happy"). Tools and 34 tests in (18 Nov 2026). Run on the FTSE they give the same picture as the confirmed hand read, with one difference written in the lesson. Choices that are mine are named in the tool files.

**Was next, now done as a lesson:** 02, liquidity (Sharif, 17 Nov 2026: "let's rather focus on liq next, it fits"), starting from the cleaned references. Order block context comes after.

Sharif names each concept and says how it is done. Nothing is listed ahead of him.

<details><summary>What v1 holds that is not in v2 yet (a reminder, not a plan)</summary>

Conditions (choppy / clean), volatility, liquidity created and eaten, named levels, gaps and their states, order
blocks, breakers, displacement, areas top-down, the range and premium / discount, opening gaps (to be retaught),
comparing the indices, context (what, where, when), entries, the trade card, managing a trade, targets and the split,
time and sessions.
</details>

## The brain and the eyes as a whole

| Item | State |
|---|---|
| The eyes: the top-down process that uses the concepts together (later, once the concepts it needs are in) | [ ] |
| The brain pulls lessons when the eyes see something (`brain/`) | [ ] waiting for Sharif's design |
| What the brain and eyes see is drawn on the chart | [ ] |

## The system

| Item | State |
|---|---|
| v2 folder, rules, tests running | [x] |
| References cleaned into `v2/references/` (engine notes stripped; v1 summaries left out) | [x] waiting for his check |
| A v2 page, feed, watcher and prep instructions | [ ] |
| v1 hunt switched off (preps cancelled, no watcher, no paper trades) | [x] 18 Nov 2026 |
| v1 folders moved under `v1/` (`ict_engine`, `tests`, `research`, `reports`, `references`, `out`); v1 still runs from there, all tests pass | [x] 18 Nov 2026 |
| Project notes (`CLAUDE.md`) rewritten around v2; the v1 description moved to `v1/README.md` | [x] 18 Nov 2026 |
| Memory notes sorted into current and v1 | [x] 18 Nov 2026 |
| Chart viewer moved to the root, out of `v1/` (page server, feed and its data), so `v1/` can be marked deprecated or deleted (Sharif, 18 Nov 2026: "at some point") | [ ] |
| Hunting again, on v2's eyes and brain | [ ] |

## Claude skills

The skills written for v1 carry v1's process and its fixed values, so they need the same clean-up as the code. Until
then they sit under `v1/.claude/skills/` (moved 18 Nov 2026, temporarily, so they are not picked up for v2 work).

| Skill | What it was for | State |
|---|---|---|
| `context-check` (was `v2-concept-check`) | Context, not the example: checks lessons, links, tools, tests and hunt notes | [x] in use; 11 tests |
| `learn` | The learn pipeline: the only one in which the brain changes | [x] built 18 Nov 2026; not yet used on a concept |
| `hunt` | The hunt pipeline | [x] built; switched off |
| `day-review` | Held hunt corrections become lessons, or not | [x] built; not yet used |
| `draw`, `brain-write`, `speak` | Marks on the chart; how a lesson and its links are written; wording | [x] built |
| backtest pipeline | Runs the hunt pipeline over old data and assesses it | [ ] later, after the eyes |
| `trade-review` | Reviewing a trade on the ICT checklist | [ ] v1: to be cleaned or dropped |
| `pattern-finder` | Mining trades for what to do more or less of | [ ] v1: to be cleaned or dropped |
| `pd-array-audit` | Checking the engine's PD arrays against his drawn zones | [ ] v1: to be cleaned or dropped |
| `change-gate` | Deciding whether a finding changes the code | [ ] v1: to be cleaned or dropped |
| `pipelines` | The order the v1 improvement skills run in | [ ] v1: to be cleaned or dropped |
| `microstructure-library` | Reading the order-flow books in `v1/references/microstructure/` | [ ] v1: skipped for now (Sharif: "skip micro structure") |

For each: Sharif decides whether v2 needs it. If it does, it is rewritten against v2 (his words, no fixed values) and
moved back to `.claude/skills/`; if not, it stays in v1 as history.

## Waiting on Sharif
- [ ] How the next concept is started ("I will state how")
- [ ] The three open bias questions
- [ ] His check of my weekly bias marks on US100, US500 and US30
- [ ] Reteaching NDOG, NWOG and the opening range gap
- [ ] The brain's pulling design
- [ ] The first links for bias and liquidity (both lessons have none yet; only he can state them)
- [ ] Whether the four hunt stages are right

## Log
| Date | What changed |
|---|---|
| 18 Nov 2026 | Pipelines and skills designed with him, approved and built: `learn`, `hunt` (off), `day-review`, `context-check` (widened to lessons, links and hunt notes), `draw`, `brain-write`, `speak` |
| 18 Nov 2026 | The six v1 skills moved to `v1/.claude/skills/` (temporary); skills added to this checklist |
| 18 Nov 2026 | v1 folders moved under `v1/`; hunts off; `CLAUDE.md` rewritten; memory notes sorted. Bias: he confirmed a break needs a body close, not a wick |
| 18 Nov 2026 | Concept 02: his answers on picking liquidity out; tools (`liquidity.py`, `alt_liquidity.py`) and 34 tests. Eyes and brain set for later, as the process that uses the concepts |
| 17 Nov 2026 | Concept 02, liquidity: lesson and alt-liquidity (NDOG, NWOG, volume imbalance, FVG as BISI / SIBI, IFVG) written from his teaching; opening range gap dropped |
| 17 Nov 2026 | Source notes cleaned into `v2/references/personal/` (11 files); framework, models, patterns, pipeline, order flow left out |
| 17 Nov 2026 | v2 created; bias confirmed on three unseen charts and entered as concept 01; folders simplified to one folder per concept |
