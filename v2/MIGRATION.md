# Migration to v2: checklist

Update whenever a box changes. `[x]` done · `[~]` partly (see the note) · `[ ]` not started.

## Concepts (one folder each under `concepts/`)

| Box | Meaning |
|---|---|
| Taught | Sharif taught it and confirmed my hand read on a chart I had not seen |
| Brain | `lesson.md` written: his words, the why |
| Eyes | The eyes file sees it on a chart, with passing tests |
| In use | The hunt reads it from v2, not v1 |

| # | Concept | Taught | Brain | Eyes | In use |
|---|---|---|---|---|---|
| 01 | Bias | [x] | [x] | [~] | [ ] |
| 02 | Liquidity, with alt-liquidity (imbalances as draws) | [~] | [x] | [ ] | [ ] |

Note on 01: the eyes agree fully with his confirmed read on the DAX, on direction on the dollar index, and differ on
the FTSE. The open questions are in `concepts/01_bias/lesson.md`.

Note on 02: the lesson and its alt-liquidity sub-part are written from his answers. Not yet tested on an unseen chart, and no eyes code: how to pick pools out (how equal is equal, how far to look, trendlines) is not taught yet, and guessing it is how v1 went wrong.

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
| The eyes run every concept on one chart and give one description | [ ] |
| The brain pulls lessons when the eyes see something (`brain/`) | [ ] waiting for Sharif's design |
| What the brain and eyes see is drawn on the chart | [ ] |

## The system

| Item | State |
|---|---|
| v2 folder, rules, tests running | [x] |
| References cleaned into `v2/references/` (engine notes stripped; v1 summaries left out) | [x] waiting for his check |
| A v2 page, feed, watcher and prep instructions | [ ] |
| v1 folders moved under `v1/` and the hunt switched to v2 | [ ] |

## Waiting on Sharif
- [ ] How the next concept is started ("I will state how")
- [ ] The three open bias questions
- [ ] His check of my weekly bias marks on US100, US500 and US30
- [ ] Reteaching NDOG, NWOG and the opening range gap
- [ ] The brain's pulling design

## Log
| Date | What changed |
|---|---|
| 17 Nov 2026 | Concept 02, liquidity: lesson and alt-liquidity (NDOG, NWOG, volume imbalance, FVG as BISI / SIBI, IFVG) written from his teaching; opening range gap dropped |
| 17 Nov 2026 | Source notes cleaned into `v2/references/personal/` (11 files); framework, models, patterns, pipeline, order flow left out |
| 17 Nov 2026 | v2 created; bias confirmed on three unseen charts and entered as concept 01; folders simplified to one folder per concept |
