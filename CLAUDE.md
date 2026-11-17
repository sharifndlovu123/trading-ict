# CLAUDE.md

Guidance for Claude Code in this repository. Sharif is a discretionary ICT (Inner Circle Trader) trader teaching
Claude to read the market his way.

## Where things stand (read first)

- **v2 is the project.** `v2/` is the clean rebuild, started 17 Nov 2026. All new work goes there.
- **v1 is deprecated.** `v1/` holds everything built before (`ict_engine`, `tests`, `research`, `reports`,
  `references`, `out`). Sharif: "v1 is broken because it was built off of exact defined targets and values which
  don't help at all." It is history, not a source. Its own description is `v1/README.md`.
- **Hunts are off** (18 Nov 2026): no London or New York prep, no watcher, no paper trades, no scheduled jobs. Do
  not restart any of it. Hunting returns only on v2 and on his word.
- **This week's objective** (week of 16 to 20 Nov 2026): "cleaning up our mess." Check with him after that week.

## v2

- Rules: `v2/README.md`. Checklist: `v2/MIGRATION.md` (read it at the start of v2 work; update it when a box changes).
- **One concept = one numbered folder** under `v2/concepts/`: `lesson.md` (his words, the why), the concept's
  tools (`<name>.py`) and their tests (`test_<name>.py`). In so far: `01_bias`, `02_liquidity` (with alt-liquidity:
  imbalances as draws).
- **The eyes** (the top-down process that uses the concepts together) **and the brain** (how lessons are pulled
  while price moves; `v2/brain/`) **come later.** Do not build either ahead of him.
- `v2/references/`: cleaned copies of the source notes (private, not in git). The ICT PDFs are in `v1/references/`.
- Tests: `uv run pytest -q v2`. Everything: `uv run pytest -q -rs` (v1's tests too; a skip is not a pass).
- Validate every concept with the `v2-concept-check` skill before ticking its box:
  `uv run python .claude/skills/v2-concept-check/check.py`, then the reading in its `SKILL.md`.

## How to work with Sharif (these caused v1's damage; they are not optional)

1. **Examples are snowflakes.** Learn why he marks something; never carry a price, time, timeframe or instrument
   from his example into a rule, a tool or a test. "If I give you a different chart you'll be confused."
2. **Only what he has confirmed enters v2,** in his words. Anything that is yours is named as yours, in the lesson
   and in the code.
3. **Tests are part of every fix.** "Whenever I say fix this and systems, tests are included, because they validate
   what you claim." Hand-built candles with known answers, several price scales and timeframes, no look-ahead.
4. **He leads.** He names each concept and says how it is done. Do not write a lesson until he says it is done; do
   not plan concepts ahead of him. Tell him before deciding anything structural.
5. **Do not do too much.** Fix what he pointed at. When he asks for a read, give the read first (for bias: per
   timeframe, bull / bear / range), then the reasons.
6. **Two modes:** teaching (be exact on his chart, learn the why) and hunting (off for now).
7. Say plainly what was checked and what was not; restart anything that serves a page after changing what it reads.

## Vocabulary he has fixed (v2)

- **Bias:** the break that set it, the level behind it (a body close through it is the change; a wick is not), the
  level ahead (failing at it changes nothing). A new swing is not a change.
- **Liquidity:** stops above old highs and below old lows. Read relative to now, from the weekly down. "Eaten" and
  "swept" are the same thing. Uneaten stays, however far; eaten is used up.
- **Imbalance** is the family name (not "FVG"): FVG (BISI, SIBI), IFVG, NDOG, NWOG, volume imbalance. As draws they
  are **alt-liquidity**: second in importance to original liquidity. The opening range gap is dropped.
- Other ICT shorthand (MSS, BOS, PDH / PDL, PWH / PWL, EQH / EQL, PO3, premium / discount): check the glossary in
  `v1/references/2022 Content.pdf` before guessing. When sources contradict, ictindex.io decides (it needs a browser).

## Standing rules

- All times are New York time (America/New_York), DST-aware.
- Secrets live in `.env` (never print, echo or commit them; never ask him to paste one in chat). Free data only.
- The chart page on port 8776 is the only thing that may listen on the network (with its password); anything else
  stays on 127.0.0.1. It is kept as a chart for teaching marks: marks only, no text on the chart, every mark ends.
- His saved reviews (`v1/reports/reviews/*.jsonl`) are read-only. `read1.png` and `read2.png` are his; leave them.
- Commit, do not push, unless he says. Cap 10 workers.
- Python for the code; `uv sync` for the environment.
