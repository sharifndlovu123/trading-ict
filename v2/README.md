# v2: the clean rebuild

Started 17 Nov 2026 on Sharif's decision. The earlier research and database were damaged by rules fitted to examples
and by lessons locked to specific prices, times and timeframes, and nobody knows how deep that goes. So everything
before this folder is **v1 and deprecated**, and everything the brain and the eyes need is rebuilt here, with Sharif
guiding each piece.

## v1 and v2
| | v1 (deprecated, kept as history) | v2 (this folder) |
|---|---|---|
| Engine code | `ict_engine/` | `v2/engine/` |
| Tests | `tests/` | `v2/tests/` |
| Research, lessons | `research/` | `v2/research/` |
| References | `references/` | `v2/references/` |
| Reports, saves | `reports/` | `v2/reports/` (made when first needed) |
| Output | `out/` | `v2/out/` (made when first needed) |

The v1 folders have not been moved yet: the live page, the feed and the hunt still run from them. They move under
`v1/` later, in one block (his choice, 17 Nov 2026). Until then "v1" means every folder in the left column.

## Rules
1. **v2 never reads v1.** No imports from `ict_engine` or `research/scripts`, no v1 notes as a source. A v1 idea enters
   only by being re-taught or re-checked with Sharif and written here afresh. (Raw candles from the data loader and the
   live feed are data, not content, and may be used.)
2. **Only what Sharif has confirmed** enters, in his words, with the date and what it was confirmed on.
3. **Each lesson is its why**, never a price, a time or a timeframe from an example. Examples are snowflakes.
4. **Every claim has tests**: hand-built candles with known answers, more than one price scale and timeframe, and a
   no-look-ahead test. "Tests are included, because they validate what you claim." Nothing is tuned to a real day.
5. **Code is a second opinion beside the hand read.** Where they disagree it is written down as an open question.
6. The brain and the eyes point here only.

## What is in v2
| Piece | Lesson | Code | Tests | Status |
|---|---|---|---|---|
| Bias | `research/lessons/bias.md` | `engine/bias.py` | `tests/test_bias.py` | lesson confirmed on three unseen charts; code matches the confirmed reads partly (see the lesson) |

## Still v1 (to be rebuilt here one at a time, each with his check)
Conditions (choppy / clean), volatility, liquidity eaten and created (per sub-group), named levels, gaps and their
states, order blocks and breakers, displacement, areas top-down, the range and premium / discount, entries, managing a
trade, the trade card, session and time rules, the watcher and the page.

Run the v2 tests: `uv run pytest -q v2/tests`.
