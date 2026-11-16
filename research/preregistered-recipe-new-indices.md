# Pre-registration — the recipe on indices it has never seen (Russell 2000, DAX, FTSE)

Written 2026-11-16, before any bar of these three instruments beyond one probe month (January 2020, loaded only to check the feed exists) was fetched, and before any model was run on them. Sharif approved the run ("okay proceed with 2", 2026-11-16).

## Why
Every period of US100 / US500 / US30 has been used to look at the recipe (`research/forward-recipe-v1.md`). The forward log gives about 30 trades a year. New instruments are the only unseen data available today. They are **not independent of the three indices**: they move with them on the same days. This is a check on new instruments, not on new time, and is recorded as that.

## The run (fixed now)
- **Rule:** variant `recipe4: recipe3, mornings only` at commit `forward-recipe-v1` logic, unchanged: no parameter is re-fitted to the new instruments. Futures cost (1 tick + 4.5 per round trip in the contract's currency: RTY, mini-DAX, FTSE 100 future).
- **Period:** 2020-01-02 → 2026-11-13 (data fetched from 2019-10 for the lookbacks).
- **Instruments:** **US2000 (primary)**: US hours, US news. DE40 and UK100 (secondary): the rule's New York morning window and the US calendar were designed for US hours, so they are reported beside the primary and do not decide the outcome.
- **Conditions:** as in the forward test: the instrument's own volatility state (`ict_engine/concepts/regime.py`, known before the day) and a scheduled high-impact US release that day.

## Candidates and outcomes (fixed now)
| # | Candidate | Supports | Does not support | Unclear |
|---|---|---|---|---|
| 1 | Every recipe trade on US2000 | ≥ 40 trades and mean R > 0 | mean R ≤ 0 | fewer than 40 trades |
| 2 | Recipe on a high-volatility or high-impact-news day, US2000 | ≥ 20 trades in each group, mean R > 0 **and** ≥ 0.2 R above the other days | mean R ≤ 0, or at or below the other days | anything else |
"Confirmed" is not on offer at this sample size on one instrument. Reported beside the outcomes: win rates with ranges; the three new instruments pooled with a day-clustered z; by year; by index; right half of the range, Monday, session note.

## Rules of the run
- `dukascopy check` on each instrument first; days with bad data are reported, not patched by hand.
- A code fix needed for the new instruments is allowed only if no trade on US100 / US500 / US30 changes.
- Whatever the outcome, the forward test's rules do not change.
- After the run: at least 30 trades reviewed in writing (15 winners, 15 losers).

## Result
_(not run)_
