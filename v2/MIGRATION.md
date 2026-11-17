# Migration to v2: checklist

Started 17 Nov 2026. Update this file every time a box changes. A box is ticked only when the thing is true and, where
it is code, its tests pass. Rules for what may enter v2 are in `README.md`.

**Marks:** `[x]` done · `[~]` partly, with a note · `[ ]` not started

## The steps every concept goes through

| Step | Meaning |
|---|---|
| 1. Taught | Sharif has taught or re-taught it; I can say the why in my own words |
| 2. Confirmed | I read it by hand on a chart I had not seen, and he confirmed the read |
| 3. Brain: lesson | Written in `brain/lessons/`, in his words, as its why, with the date and what it was confirmed on |
| 4. Eyes: code | Code in `eyes/` that sees it on a chart (where code makes sense), no values taken from examples |
| 5. Tests | Hand-built candles, known answers, more than one price scale and timeframe, no look-ahead |
| 6. Old tests | The v1 tests for it gone through case by case: kept, rewritten or dropped with the reason |
| 7. Checked | Code run on the charts he confirmed; every disagreement written down as an open question |
| 8. Brain: links | The lesson is tied into the brain: what the eyes must see for it to come to mind, and which other lessons it leads to. (How this works is still to be designed with Sharif; until then this box stays open for every concept) |
| 9. In use | The page, the watcher or the prep reads it from v2 and no longer from v1 |

So each concept builds the eyes (step 4) and the brain (steps 3 and 8) as it comes in. What each one added is listed
under "The eyes and the brain, piece by piece" below.

## Concepts

| # | Concept | 1 Taught | 2 Confirmed | 3 Brain: lesson | 4 Eyes: code | 5 Tests | 6 Old tests | 7 Checked | 8 Brain: links | 9 In use |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Bias (the break, the level behind, the level ahead) | [x] | [x] | [x] | [x] | [x] | [x] | [~] | [ ] | [~] |
| 2 | Conditions: choppy or clean | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 3 | Volatility | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 4 | Liquidity created and eaten (equal highs / lows per sub-group) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 5 | Named levels as liquidity (previous day / week, sessions) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 6 | Gaps (FVG) and their states: respected, body inside, flipped | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 7 | Order blocks (his reading: body, clean or dim, the middle) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 8 | Breakers | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 9 | Displacement and break of structure on the lower timeframe | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 10 | Areas of interest, top-down | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 11 | The range we trade; premium and discount | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 12 | Opening gaps: NDOG, NWOG, opening range gap (to be retaught) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 13 | Comparing the indices (strongest / weakest, SMT) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 14 | Context: what, where, when (stacking on one area) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 15 | Entries (the six he has shown) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 16 | The trade card: trade, goal, missing, entry, stop, cancel | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 17 | Managing: unfilled orders, wick is not a break, chasing, partials | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 18 | Targets and the split (with point 8 of the NY-1 review) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 19 | Time: sessions, his key windows, watch limits | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

Sharif sets the order and may add, merge or remove rows. Rows 2 to 19 are my list of what v1 holds; none of it counts
as known in v2 until its row is ticked.

### Notes on the partly-done boxes
- **Bias, 7 Checked:** run on DAX, dollar index and FTSE. DAX agrees fully; the dollar index agrees on direction; the
  FTSE differs on the weekly (code: bull, hand read: range) and on where the daily level behind sits. Open questions
  are listed in `brain/lessons/bias.md`: how he decides "range"; whether "a swing of the timeframe above" is the right
  meaning of significant; the marginal weekly close on US100.
- **Bias, 9 In use:** the prep reads bias by hand his way and the page has a Bias line, but `eyes/bias.py` is not
  shown on the page yet, and v1's scan no longer states a bias.

## The eyes and the brain, piece by piece

One row is added here each time a concept comes into v2, so this table is the build record of both.

| Concept | What the eyes can now see (`eyes/`) | What the brain now holds (`brain/`) | Links to other lessons |
|---|---|---|---|
| Bias | `bias.py`: per timeframe, the break that set the bias, the level behind it, the level ahead; a wick is not a break; smaller swings do not move it | `lessons/bias.md`: a new swing is not a change; the stronger pieces move it all; level below: break = change | none yet (waiting on the design) |

## The brain as a whole

| Item | State |
|---|---|
| Folder for lessons (`brain/lessons/`), one file per confirmed lesson | [x] |
| Folder for the eyes (`eyes/`), one file per thing it can see, each with tests | [x] |
| The eyes run together on one chart and give one description (all pieces, any timeframe) | [ ] |
| How a lesson is pulled when the eyes see something (links, one lighting up another, recall while price moves) | [ ] design to be discussed with Sharif first; nothing built |
| Lessons carry what they were confirmed on and what would make them wrong | [ ] |
| The brain's output drawn on the chart | [ ] |

## The system around it

| Item | State |
|---|---|
| `v2/` created with its rules (`README.md`) | [x] |
| v2 tests run with the main test command (`uv run pytest`) and alone (`uv run pytest -q v2/tests`) | [x] |
| Project notes (`CLAUDE.md`) and my memory say: v1 deprecated, new work in v2, tests always included | [x] |
| A v2 feed of candles for the eyes (data only, nothing from v1's reads) | [ ] |
| A v2 page that draws only what v2 sees | [ ] |
| A v2 watcher and checker rules built only from v2 lessons | [ ] |
| v2 prep instructions (London, New York) built only from v2 lessons | [ ] |
| A v2 hunting playbook, rebuilt lesson by lesson (v1's playbook is not copied across) | [ ] |
| v2 hunt log and paper-trade record (`v2/research/`) | [ ] |
| `v2/references/`: ICT sources re-checked with Sharif before they are cited | [ ] |

## Retiring v1

| Item | State |
|---|---|
| Move `ict_engine/`, `tests/`, `research/`, `reports/`, `references/`, `out/` under `v1/` in one block | [ ] |
| Re-point or switch off what breaks: live feed, the 8776 page, watcher, prep prompts, v1 tests | [ ] |
| Decide what of v1 stays runnable (backtests, the frozen forward recipe, his saved reviews stay read-only) | [ ] Sharif's decision |
| My memory notes from v1 marked as v1 so they are not read as confirmed | [ ] |
| The v1 hunt (playbook, scan, watcher) switched off once v2 can hunt | [ ] |

## Waiting on Sharif

- [ ] Reteach NDOG, NWOG and the opening range gap (row 12), with targets and the split (row 18)
- [ ] The three open bias questions (above)
- [ ] His check of my weekly bias marks on US100, US500 and US30 (on the page, 17 Nov 2026)
- [ ] The design talk on how the brain pulls lessons
- [ ] The order of rows 2 to 19

## Log

| Date | What changed |
|---|---|
| 17 Nov 2026 | Checklist: brain and eyes building made part of every concept's steps, with a build record |
| 17 Nov 2026 | v2 created; bias taught again and confirmed on the dollar index, FTSE and DAX; bias lesson, code and 20 tests in; eyes and brain folders made; this checklist started |
