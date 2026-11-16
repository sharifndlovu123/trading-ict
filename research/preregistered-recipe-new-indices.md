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

## Result — run once, 2026-11-16 (`reports/recipe-new-indices-2020-01-02-2026-11-13.parquet`, trades with conditions in `reports/recipe-new-indices-trades.parquet`)
Data check first: full mornings on all three (median 300 of 300 one-minute bars 07:00–12:00), no bad candles, thin days comparable to US500.

| | Trades | Win % [95%] | Mean R | z |
|---|---|---|---|---|
| **US2000, every trade (candidate 1)** | 83 | 36.1 [27–47] | +0.063 | +0.45 |
| **US2000, high-volatility or news day (candidate 2)** | 34 | 38.2 [24–55] | +0.041 | +0.19 |
| US2000, other days | 49 | 34.7 [23–49] | +0.079 | +0.41 |
| DE40, every trade | 61 | 34.4 [24–47] | +0.106 | +0.74 |
| DE40, candidate 2 / other days | 29 / 32 | 37.9 / 31.2 | +0.268 / −0.040 | |
| UK100, every trade | 49 | 26.5 [16–40] | −0.204 | −1.48 |
| UK100, candidate 2 / other days | 25 / 24 | 20.0 / 33.3 | −0.292 / −0.111 | |
| Three pooled | 193 | 33.2 [27–40] | +0.009 | +0.11 (day-clustered 0.11) |
| Three pooled, candidate 2 / other days | 88 / 105 | 33.0 / 33.3 | +0.021 / −0.001 | |

**Outcomes by the rules written above**
- **Candidate 1: "supports"** by the letter (83 trades, mean R above zero), and it is a weak one: +0.06 R with z 0.45 is indistinguishable from zero.
- **Candidate 2: "does not support".** On the Russell the volatile-or-news days did no better than the rest (+0.041 against +0.079). High-volatility days alone lost (−0.30 R, 12 trades); news days alone +0.16 (25).

Beside them: US2000 by year 2020 −0.29, 2021 +0.18, 2022 +0.08, 2023 +0.77, 2024 +0.04, 2025 −0.20, 2026 −0.01 (4 of 7 positive); shorts +0.30 (40), longs −0.16 (43); Mondays −0.11 (18) against +0.11 (65). DE40 Mondays −0.32 (15) against +0.25 (46). The DAX leans the way of the conditions lead (+0.27 against −0.04), the FTSE the other way.

**Reading:** on instruments it had never seen, the recipe is about break-even (the pooled 193 trades: +0.009 R, 33% wins) and the "volatile or news day" split does not repeat on the primary. The split found on the three US indices is weaker evidence than it looked; the forward test stays as written and decides it. "Not Monday" points the same way on the Russell and the DAX (not a registered outcome).
