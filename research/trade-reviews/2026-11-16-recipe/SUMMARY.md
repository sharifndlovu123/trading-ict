# 30 trades of the first recipe run reviewed (15 winners, 15 losers) — and the leads checked on every recipe trade

The run: Sharif's entry recipe coded on the PD-array-return model (`research/entry-trigger-from-saves-2026-11-16.md`): 1h/4h FVG reached to its 50% → a 15m FVG in the area's direction within 4 hours → limit at that gap; no daily bias; New York windows. Three indices, 2022–24: 287 trades, 22.3% win, +0.006 R. Two reviewers, 15 trades each; files in this folder, fact sheets in `../sheets/2026-11-16-recipe/`. 30 trades are leads; the table below is the check on all trades.

## What the reviewers saw
**Where the coded recipe differs from his words** (both reviewers, independently):
1. **The side comes from the area alone.** Nothing checks where price is now: 9 of the 30 trades were against both the 1h and the 4h structure (03 Jan, 08 Feb, 18 Apr 2022; 01 Feb, 23 Feb, 04 Apr 2023; 24 Oct 2023; 12 Mar, 07 Jun 2024). His notes: "the no. 1 focus is where we currently are", "momentum is selling heavy, I would have sold".
2. **"Be patient" only applies to the touch.** The entry is the 15m gap wherever it forms: 0.13–0.5 ADR from the area on a third of the trades, in the wrong half on 10 of 15 in one batch. His note: "you're shorting quite late".
3. **Any 15m gap counts as momentum**, including gaps 0.6–3.4 points wide and quiet pre-open ones. (The four pre-09:30 entries in batch 1 all won, so this one is not clear-cut.)
4. **Late entries and far targets:** both entries after 15:00 lost; TP1 was 5–9 R away on three trades.

**Where price turned:** winners 0.03–0.3 ADR past the entry, inside the stop, several exactly at the area's edge or 50%; losers 0.03–0.6 ADR beyond the stop at levels known at the entry (the area's far edge, a 4h FVG, PDH/PWH, Asia low). The stop sat on a pool on 28 of 30.

## The leads on every 15m-trigger recipe trade (`reports/recipe-scale-2026-11-16.parquet`)
| Lead | Full recipe (287 trades) | Verdict |
|---|---|---|
| Side against both 1h and 4h structure | 15.9% win, −0.142 R (n 69) vs with both 26.5%, +0.105 R (n 98; positive on all three indices) | Holds in the no-bias recipes; no effect where the daily bias is on |
| Entry further than 0.25 ADR from the area | 2.4% win, −0.242 R (n 42); negative on all three indices and in all six 15m-trigger variants (5–11% win) | **Holds everywhere** |
| Entries from 14:00 | 9.3% win, −0.130 R (n 86), all three indices | Holds in the NY recipes (win rate; far targets late in the day) |
| All three together (not against both, ≤ 0.25 ADR, before 14:00) | **36.2% win, +0.196 R, z 1.75 (n 127); US100 +0.16, US30 +0.29, US500 +0.12; both halves positive** | Worth a real backtest (rule R10): a filter after the fact ignores the one-trade-per-window slots |
| The same three on the all-windows no-bias variant | 32.7% win, −0.037 R (n 663) | Does not carry over: the New York windows and the 50% are part of it |

## Found by the review: a bug in the liquidity map (fixed)
At 10:17 the map listed a 1h FVG whose third candle was the 10:00 hour, still forming, and a 4h one the same way (the reviewers saw arrays whose edge equalled the entry price). An FVG exists only once its third candle has closed. Fixed in `ict_engine/concepts/liquidity_map.py` (test first; suite passed). It affected the map, the read, the plans and the fact sheets; the models' own detection uses completed candles and was not affected.

## Other flags for the array audit
Sliver arrays 0.03–2.5 points wide on 1h/4h/1d; the same daily zone listed as FVG and IFVG (22 Mar 2022); a weekly FVG and IFVG sharing an edge (31 May 2023); TP1 at equal highs already taken (28 Sep 2023 US100); model POIs missing from the map's arrays (09 Jan, 12 Mar 2024). The fact sheet should print the POI bounds, the time the area was reached and the 15m gap.

## Next
The three gates are built as options on the model (`structure_gate`, `max_entry_dist_adr`, `last_entry`; off by default) and the recipe is re-run as a real backtest (`recipe2` variants). If it holds pooled and on at least 2 of 3 indices, it gets its own 30-trade review and a pre-registration for 2021.
