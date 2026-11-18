# CLAUDE.md

Guidance for Claude Code in this repository. Sharif is a discretionary ICT (Inner Circle Trader) trader teaching
Claude to read the market his way.

## Where things stand (read first)

- **v2 is the project.** `v2/` is the clean rebuild, started 17 Nov 2026. All new work goes there.
- **The old version is sealed off in `v1/`.** Sharif: "v1 is broken because it was built off of exact defined
  targets and values which don't help at all." **Nothing outside that folder reads it, runs it, imports it or points
  into it,** and it may be deleted. Do not open it for v2 work. If he asks about something old, ask him first.
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
- `v2/references/`: cleaned copies of the source notes (private, not in git).
- `v2/chart/`: the chart page (candles and marks only). Start it with
  `uv run python v2/chart/server.py --host 0.0.0.0 --password-env LIVE_PAGE_PASSWORD`, open
  `http://127.0.0.1:8776/?asset=UK100&tf=1D`. Claude's marks: `v2/chart/marks.json`; what he draws and saves:
  `v2/chart/saves.jsonl`. Fresh candles: `uv run python v2/chart/fetch.py <ASSET>` (free data, needs Node.js).
- Tests: `uv run pytest -q v2` (a skip is not a pass).
- Validate every concept with the `context-check` skill before ticking its box:
  `uv run python .claude/skills/context-check/check.py`, then the reading in its `SKILL.md`.

## Pipelines: one word, one pipeline (design: `v2/specs/2026-11-18-pipelines-and-skills.md`)

Only one pipeline runs at a time, and its first line says which. If it is not clear which he means, ask once.

| He says | Pipeline (skill) | In short |
|---|---|---|
| "learn", or he starts teaching | `learn` | He teaches → Claude draws it on a chart it has not seen → he corrects → he says it is done → lesson and links written → tools and tests → context check. **The only pipeline in which the brain changes** |
| "hunt" | `hunt` | **Off for now: answer that hunts are off and ask.** When on: where is price now → draw what is interesting → what the brain brings to mind → his corrections are noted in `v2/hunts/` and held |
| end of the trading day | `day-review` | Go through the held notes together; he says which are lessons; those go through learn |
| (later) | backtest | Runs the hunt pipeline over old data and assesses it. Not built |

Small skills the pipelines use: `context-check` (context, not the example), `draw` (marks on the chart),
`brain-write` (how a lesson and its links are recorded), `speak` (wording).

**The goal (his words):** "You're watching the market live for yourself and you're seeing these patterns and
pointing them out and drawing them yourself, to the point where you can place limits and stops yourself."

**How to speak, always** (skill `speak`): point at what is **interesting**; never say "price is buying" or "price is
selling"; tie every statement to a timeframe and to now ("the weekly is bullish, the hourly is bearish"); a pattern
is "might be".

## How to work with Sharif (ignoring these is what broke the old version; they are not optional)

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
- Other ICT shorthand (MSS, BOS, PDH / PDL, PWH / PWL, EQH / EQL, PO3, premium / discount): do not guess. Ask him, or
  search ICT's own words on ictindex.io (it needs a browser). When sources contradict, ictindex.io decides.

## Standing rules

- All times are New York time (America/New_York), DST-aware.
- Secrets live in `.env` (never print, echo or commit them; never ask him to paste one in chat). Free data only.
- The chart page on port 8776 is the only thing that may listen on the network (with its password); anything else
  stays on 127.0.0.1. Marks only, no text on the chart, every mark ends.
- What he saves from the chart (`v2/chart/saves.jsonl`) is his: read it, never edit it. `read1.png` and `read2.png`
  are his; leave them.
- Commit, do not push, unless he says. Cap 10 workers.
- Python for the code; `uv sync` for the environment.
