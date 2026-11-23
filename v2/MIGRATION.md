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
| 01 | Bias | [x] | [x] | [x] drafted from his words, read by him 20 Nov 2026 ("perfect") | [x] | [ ] |
| 02 | Liquidity, with alt-liquidity (imbalances as draws) | [x] | [x] | [x] drafted from his words, read by him 20 Nov 2026 ("perfect") | [x] | [ ] |
| 03 | Bias and liquidity working together (favouring, the sequence, the trading range and its 50%, targets by timeframe and by bias, the bigger trade) | [x] 20 Nov 2026, a top-down read of the Dow he did not correct: "so far so good, your read is solid" | [x] | [x] 13 stated by him | none yet: read on the chart | [ ] |
| 04 | Sessions: when a trade is looked for (his times, the reference definitions, locked time) | [x] 20 Nov 2026, the same read, made inside the London morning with the session in it from the start | [x] | [x] 4 stated by him | [x] `sessions.py`, 11 tests (20 Nov 2026) | [ ] |

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
| `tools-backtest` | The tools reading old data on the higher timeframes: calls about where price might draw to, each followed to see whether it came true; tables (the first pattern finder); any call opens on the chart in replay | [x] built 20 Nov 2026 (`v2/backtest/`, 40 tests); full run done 20 Nov 2026 on what he trades and three test charts; waiting for him to look at the misses |
| pattern finder | Finds patterns inside the sessions on old data (displacement around his times, for one) | [ ] later, on his request, with backtesting (20 Nov 2026: "I want to build your foundations, then when I ask you to backtest on old data I'll request you build a pattern finder skill") |

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
- [ ] **Tools backtest, for when he is back (20 Nov 2026):** he asked, while away, for the data to be sorted (done: every instrument now runs from late 2019 with no missing months; gold and silver were filled in from the free feed), the backtest carried on, and `/backtest` made informative enough to look at together (done: it leads with the picture he marked as very important, the higher timeframes being stronger, and is grouped by what he trades). Next with him: go through the page, then open the calls the tools got wrong and say what each missed. Nothing in any tool was changed because of the numbers
- [ ] **Trading range as a tool:** later (20 Nov 2026: "consider it later; it's tricky, but keep the fluidity in your mind"). Read by eye until then
- [ ] **Range as a tool:** taught by eye and shown back on 20 Nov 2026; the test is confirmed ("that's correct"). Not in the tool: "a few turns" and "some time" are not numbers he has given
- [x] The three open bias questions: answered 19 Nov 2026 (range defined and held for examples; significance is relative, two up; a marginal close is checked one timeframe down)
- [ ] The brain's pulling design
- [x] **Merging the timeframes (20 Nov 2026):** taught after he went through the first run ("there's a mix of timeframes to provide a result"; "where price is RIGHT NOW is always more important"); written into `03_bias_with_liquidity` with three links; context check passed. The backtest now also makes a merged call per timeframe with the one above it (`calls.merged`, tested); he asked for a second run with it. How the merge is decided is Claude's and waits for his look at the results.
- [x] **Check ten calls with him (20 Nov 2026, his request; done 23 Nov):** `/backtest/check` on the chart server lists ten merged calls where the timeframes disagreed (momentum and key area) on the three indices; each opens on the chart at its moment; he says whether the read was right and what it missed (kept in `v2/backtest/reviews.jsonl`, his file: read, never edit). "If it's too far off we will have to do more later on." What he says goes through learn. **He reviewed all ten (20 Nov):** every momentum read right, the key-area misses wrong. Taken through learn on 23 Nov ("At an interesting zone: the closed candle, on the zone's own timeframe" in `03_bias_with_liquidity`, four links, shown back on two charts, context check passed). On his yes: the merged call now reads every timeframe above it and a key area ends on a close of its own timeframe (`calls.merged`, `calls.resolve`, tested); third run made. **His way of judging a call (23 Nov):** he looks at the statement, bull or bear, and follows it forward; the area being reached by any route is the bias playing out, and only the bias changing ends the idea (written into `03_bias_with_liquidity`, two links; not yet shown back on a chart). The backtest counts it beside the old exact count (`calls.played_out`, tested); the HIT / MISS tags are gone from the check page. **The starting process (23 Nov):** liquidity first from the top down and relative to price, then the bias, then where price is; around an interesting area: sell into it from outside, watch inside it (written into `03_bias_with_liquidity`, three links; shown back and accepted). The merged call follows it (`into area`, watching, `from area`; `calls.merged`, tested) and the three indices were re-run for his review. **Not hit or miss (23 Nov):** "you will never know, you can only let it play out"; written into `03_bias_with_liquidity`. The backtest follows each bias as a story (`calls.story`, `tables.stories`, tested): level broken straight, after a deeper zone, or the bias flipped; the check page lists ten of those with no hit / miss tag. Waits for his look. Held on his word: Fibonacci, small piece trading, extra timeframes, premium; he has "an extra addition" for the bias to bring once this is sorted.
- [ ] The backtest skill: his reminder is `.claude/skills/backtest/README.md` ("that skill is very important")
- [ ] Whether any skill from the old version is wanted in v2 (each would be rebuilt through a design with him)
- [ ] Whether the ICT PDFs come into `references/`

## Log
| Date | What changed |
|---|---|
| 20 Nov 2026 | Tools backtest designed with him, approved and built: calls, outcomes, tables, replay of any call. Range taught and written (a moment inside the bias). The line for the pattern finder below is its first version |
| 20 Nov 2026 | Alt-liquidity: the thing he found on the Dow was a volume imbalance on the highest timeframe, lying inside a lower timeframe's imbalance. Taught: a draw is traded into from outside and watched from inside. Sessions got a tool and tests; the context check's reading was done for 01, 02 and 04; links for 01 and 02 |
| 20 Nov 2026 | Concepts 03 and 04 confirmed on a chart I had not seen (the Dow, London morning): "so far so good, your read is solid". On 19 Nov: his answers to the open questions written into all four lessons; the bias tool looks two timeframes up, finds the level behind as the pullback the break was built on, and can read a line chart; range held for his examples |
| 19 Nov 2026 | Lesson 03 shown back on gold and the Nasdaq; his corrections written in as "The bigger trade" (missed trades, the fluid range, an area's own timeframe, the 50% against the imbalance, knowing what was swept). Concept 04, sessions, written from what he confirmed. Chart: Claude's read tick and answers under his notes; a Same TF switch |
| 18 Nov 2026 | Concept 03, bias and liquidity working together: taught on the Russell 2000 from the monthly down to the 5-minute; lesson and links written when he said it was done. Chart: trading range and 50% marks |
| 18 Nov 2026 | "Very close" is judged by eye, from far (his words). Tool: close = a share of the chart's height; a slider on the chart (≈) shows the equal highs and lows found for any share, so he can set it by eye |
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
