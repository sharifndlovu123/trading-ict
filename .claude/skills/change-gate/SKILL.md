---
name: change-gate
description: Decide whether a recommendation from the improvement skills (trade-review "For the engine", pattern-finder "Try more / less", pd-array-audit recommendations, FABLES_FINDINGS, review-log ideas) should change the codebase — and if so, make the change safely: classify it, check that the other skills' evidence agrees, implement it behind a flag with unit + regression tests, run the suite, and record the decision. Use whenever someone asks "should we change the code for this", "apply this finding", "implement FF-xx", "make this the default", or when a review/pattern/audit result proposes an engine change; also use before turning any finding into a default.
---

# Change gate: does this recommendation change the code?

The improvement skills produce many ideas, and most should **not** become code. Any idea also has to be judged against what the other skills say, because a pattern that wins on paper can rest on a broken detector, and a review lesson from one trade can contradict the numbers from 600.

This skill is the single place where an idea becomes:
- (a) no change;
- (b) a test or measurement to run first;
- (c) a bug fix;
- (d) an option behind a flag;
- (e) a new default.

It never skips the evidence for the convenience of the change.

## 1. State the recommendation

Write it as one sentence with:
- its **source**: the skill or file, the item ID (e.g. FF-07, a pattern row, a trade-review file), and the numbers behind it;
- the exact **code location** it would touch: module, function, parameter.

If you can't name the location, it isn't ready.

## 2. Classify it

| Class | Test | What it needs |
|---|---|---|
| **No change** | It's a reading or execution note for the trader, or already exists (grep the code, check `research/review-log.md`) | A note in the decision record |
| **Measure first** | A claim about trades with no or weak evidence: one trade, n < 30, a LEAN label, in-sample only | A run of pattern-finder or a backtest/sim variant; come back with the result |
| **Bug fix** | The code contradicts its own definition, a ruling, or the spec. Examples: look-ahead, a wrong edge, a zero-width area, a crash, a wrong metric | A failing unit test first, then the fix; the defaults' results may move, so say how much |
| **Option (flag)** | New behaviour worth testing: a new trigger, stop or target rule, or a filter | A parameter that defaults to the current behaviour, a variant name, and tests for both settings |
| **New default** | An option that already beat the baseline **out-of-sample** in a pre-registered test (`research/preregistered-*.md`: ≥ 30 OOS trades, z ≥ 2.4) | Only then flip the default; record the pre-reg file and result |

Selection uses 2022-01-03 → 2024-06-28 only, and nothing becomes a default on in-sample evidence. If someone asks to make an in-sample winner the default, the answer is "option + pre-registration", with the reason why.

## 3. Check that the other skills agree

Gather the evidence each skill can give on the same idea, run whatever is cheap, then fill in this table:

| Witness | How to ask it | Agrees / disagrees / silent |
|---|---|---|
| **pattern-finder** | `research/scripts/pattern_find.py` on the relevant trades (`--target win` and R) | Does the trait that the change targets actually separate wins from losses, robustly? |
| **pd-array-audit** | `research/scripts/pd_audit.py` (or the latest `research/pd-audit/*.md`) | If the idea depends on an array type: is that array detected and on the map correctly? If not, fix that first |
| **trade-review** | `research/trade-reviews/log.jsonl` + the review files | Do reviewed trades show this failure step? How many, and are they the same kind of trade? |
| **review log / Fable** | `research/review-log.md`, `research/sweeps/*.md`, `FABLES_FINDINGS.md` | Was it tried before and did it fail (rows #1–36…)? Does Fable's ledger mark the area as a consistent loser? |
| **Sharif's saves** | `reports/reviews/*.jsonl` (read only) | Does his own handling do this? |

Decide:
- **Proceed** only if no witness disagrees with evidence, and at least one gives real evidence (not a single trade).
- **Disagreement:** stop, lay out both sides with numbers, and ask Sharif. That's a decision for him, not a tie to break quietly.
- **A failed detector or audit underneath the idea:** that fix goes first, as its own bug-fix change.

## 4. Change the code (only classes c, d, e)

- **Before touching engine code,** make sure no sweep or backtest is running (`pgrep -fa "ict_engine.eval|plan_build|plan_sweep"`).
- **Keep the layers separate** (`CLAUDE.md`): concepts, patterns, strategies, models. Put the change in the module the pipeline names (`references/pipeline.md`).
- **Write the test first**, on hand-built candles with known answers:
  - for a bug: the failing case;
  - for an option: both settings;
  - plus a no-look-ahead check where time is involved.
  - Add a real-data regression where one exists (e.g. `tests/test_regression_ict_trades.py`, the gold regressions in `tests/test_htf_draw.py`).
- **Implement.** Options default to the current behaviour, and the variant name shows the setting (as `stop_type` → `-stop_ob`).
- **Run** the new tests, then the full suite once: `uv run pytest -q -rs` (about 5 min). Skips are not passes. A failure in an untouched area means the change has side effects, so fix or revert.
- **For a bug fix that moves results,** re-run the affected sim or backtest (`plan_build.py --sim` takes about 2 min from cache) and report before → after.

## 5. Record the decision

Write `research/decisions/<YYYY-MM-DD>-<slug>.md`:

```markdown
# <recommendation, one line>
Source: <skill / file / ID> · Class: <no change | measure first | bug fix | option | new default>
## Evidence (witness table)
## Decision and why
## Change
<files + functions, flag name/default, tests added, suite result (N passed), before → after numbers if any>
## Next
<pre-registration to write, or what would change the decision>
```

Add a row to `research/review-log.md` when something was tested or changed. Commit when the user's instruction covers it, with one commit per decision.

## 6. Reply

In chat, cover:
- the class and the decision;
- the witness table in short;
- what changed: files, flag, tests, suite result;
- what still needs Sharif: a disagreement, or a default that waits for a pre-registration.

Several recommendations can go through the gate in one pass, but each gets its own class, decision and record.
