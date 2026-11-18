# v2 checklist

**This week's objective (Sharif, 18 Nov 2026; the week of 16 to 20 November 2026): "cleaning up our mess."** No
hunting, no new strategies.

Update whenever a box changes. `[x]` done · `[~]` partly (see the note) · `[ ]` not started.

## Concepts (one folder each under `concepts/`)

| Box | Meaning |
|---|---|
| Taught | Sharif taught it and confirmed my hand read on a chart I had not seen |
| Lesson | `lesson.md` written: his words, the why |
| Links | The lesson says what brings it to mind and what to look for next |
| Tools + tests | The concept's tools find it on a chart, with passing tests on hand-built candles |
| In use | A hunt reads it |

| # | Concept | Taught | Lesson | Links | Tools + tests | In use |
|---|---|---|---|---|---|---|
| 01 | Bias | [x] | [x] | [ ] | [x] | [ ] |
| 02 | Liquidity, with alt-liquidity (imbalances as draws) | [x] | [x] | [ ] | [x] | [ ] |

Note on 01: the tool agrees fully with his confirmed read on the DAX, on direction on the dollar index, and differs
on the FTSE. The open questions are in `concepts/01_bias/lesson.md`.

Note on 02: tested on the FTSE and confirmed ("I'm happy"). Run on the FTSE the tools give the same picture as the
confirmed hand read, with one difference written in the lesson. Choices that are mine are named in the tool files.

Sharif names each concept and says how it is done. Nothing is listed ahead of him. He named order block context as
coming after liquidity.

## The brain and the eyes

| Item | State |
|---|---|
| The eyes: the top-down process that uses the concepts together | [ ] later, once the concepts it needs are in |
| The brain pulls lessons when the eyes see something (`brain/`) | [ ] waiting for Sharif's design |
| What the brain and eyes see is drawn on the chart | [ ] |

## Pipelines and skills (`.claude/skills/`; design in `specs/`)

| Skill | What it is | State |
|---|---|---|
| `learn` | The learn pipeline: the only one in which the brain changes | [x] built 18 Nov 2026; first run-through done on the Russell 2000 |
| `hunt` | The hunt pipeline | [x] built; switched off |
| `day-review` | Held hunt corrections become lessons, or not | [x] built; not yet used |
| `context-check` | Context, not the example: lessons, links, tools, tests, hunt notes | [x] in use; 11 tests |
| `draw`, `brain-write`, `speak` | Marks on the chart; how a lesson and its links are written; wording | [x] built |
| backtest pipeline | Runs the hunt pipeline over old data and assesses it | [ ] later, after the eyes |

## The system

| Item | State |
|---|---|
| v2 folder, rules, tests running | [x] |
| References cleaned into `references/` | [x] waiting for his check |
| The old version sealed off in its own folder, with its own settings, environment, pages, skills and ignore file; nothing at the top level reads it, runs it or points into it | [x] 18 Nov 2026 |
| The chart rebuilt clean in `chart/`, one page laid out like TradingView: any number of charts (layouts, expand, full screen), his full drawing tools with move / resize / grab, notes on the chart, linked crosshair and scrolling, line mode, % compare, watchlist, Claude's read, replay (take time back) | [x] 18 Nov 2026; for him to try |
| Top-level project settings, readme and ignore file are v2 only | [x] 18 Nov 2026 |
| Project notes (`CLAUDE.md`) written around v2 | [x] 18 Nov 2026 |
| Hunts switched off | [x] 18 Nov 2026 |
| Live candles on the chart: a switch on the page; while on, the instruments shown are refreshed from the free feed about once a minute and kept in the candle files | [x] 18 Nov 2026 |
| Hunting again, on v2's eyes and brain | [ ] |
| The old version's folder deleted, when he says | [ ] |

## Waiting on Sharif
- [ ] The first links for bias and liquidity (only he can state them)
- [ ] The three open bias questions
- [ ] The brain's pulling design
- [ ] The backtest skill: his reminder is `.claude/skills/backtest/README.md` ("that skill is very important")
- [ ] Whether any skill from the old version is wanted in v2 (each would be rebuilt through a design with him)
- [ ] Whether the ICT PDFs come into `references/`

## Log
| Date | What changed |
|---|---|
| 18 Nov 2026 | Learn run-through on the Russell 2000 (bias, liquidity, alt-liquidity): "so far I am happy". Added to the lessons: a body beyond a level is a break however it got there; mark from the monthly down; equal and eaten are both relative; an eaten set comes off the chart. Liquidity tool fixed (3 tests), bias test added |
| 18 Nov 2026 | Chart: a Live switch (free feed, about a minute behind; only the instruments on the page; stops by itself when the page is closed) |
| 18 Nov 2026 | Chart: one colour per kind of mark (Claude's dashed, his solid); a light / dark switch; candles blue and black (light grey for black on the dark page) |
| 18 Nov 2026 | Chart drawing: snap to a candle's open / high / low / close (toggle, M); double-click locks and unlocks a mark, and a locked one lets clicks through to what is underneath; a block's corners size it both ways |
| 18 Nov 2026 | Chart: our candle colours; a Notes tab (tall text area) in the right panel; a LEARN / HUNT / OFF mode shared by the page and the pipelines, shown at the top left with a coloured strip |
| 18 Nov 2026 | Chart: the old single chart and multi-chart rebuilt as one page in the TradingView layout he is used to; replay added on the server (nothing after the chosen minute is sent); 16 tests |
| 18 Nov 2026 | Sweep: the old version made self-contained and sealed off; a clean chart built in `chart/` with tests; every pointer into the old version removed from the notes, skills and tests. The four hunt stages confirmed by him |
| 18 Nov 2026 | Pipelines and skills designed with him, approved and built: `learn`, `hunt` (off), `day-review`, `context-check`, `draw`, `brain-write`, `speak` |
| 18 Nov 2026 | Hunts off; `CLAUDE.md` rewritten; memory notes sorted. Bias: he confirmed a break needs a body close, not a wick |
| 18 Nov 2026 | Concept 02: his answers on picking liquidity out; tools and tests. Eyes and brain set for later |
| 17 Nov 2026 | Concept 02, liquidity: lesson and alt-liquidity written from his teaching; opening range gap dropped |
| 17 Nov 2026 | Source notes cleaned into `references/` |
| 17 Nov 2026 | v2 created; bias confirmed on three unseen charts and entered as concept 01 |
