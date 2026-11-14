# Review log: what Sharif's chart reviews found that the engine missed

Source: the Trade Review page (https://claude.ai/artifact/8mV3wr5PECosNCgDSj8vUX; notes in `corrections`,
drawings in `drawings`). Each item moves: **found → built → pre-registered → tested → result**. A rule only becomes
a default after it beats the baseline out-of-sample on 2022–24 and then passes the forward test.

| # | Found (date, trade) | What the engine missed | Built | Pre-registered | Result |
|---|---|---|---|---|---|
| 1 | 2026-11-14, 2022 model / PD return Sep 16–17 2024 | Ride the wave: don't sell the presumed top; 15m momentum sets the side | – | – | open |
| 2 | 2026-11-14, several | IFVG flip: a close through your FVG means you're on the wrong side | – (exit-only version tested 2026-11-13, hurt) | – | open |
| 3 | 2026-11-14, MMxM / SB Sep 16–17 2024 | Re-entry after a sweep stop-out inside the window | – | – | open |
| 4 | 2026-11-14, SB Apr 15 2024 | Targets too close; aim at PDL/PWL (real draws) | liquidity pools (#6) | next | open |
| 5 | 2026-11-14, 2022 model Apr 16 2024 | Daily OB: confirmation on a close through its open; body quadrants, 50% = MT (ICT rulings §11) | `order_blocks(confirm=)`, `quadrants`, pd_return `ob_confirm/ob_measure` | `preregistered-htf-ob-2026-11-14.md` | **failed** (all 5, both bases; best z +0.3): `htf-ob-results-2026-11-14.md` |
| 6 | 2026-11-14, liquidity guidance | Equal highs/lows; pools (EQH near PDH = stronger); trendline phantoms (ICT rulings §12) | `equal_levels`, `liquidity_pools`; trendlines not yet | targets: next | found Sharif's EQL ×3 at 18051.5 |
| 7 | 2026-11-14, 2022 model Apr 16 2024 | Daily FVG failed on a DAILY close → IFVG; leaves EQLs; retest validates; OB inside. Bias stayed bullish: the IFVG is a counter-bias **sellers' turn** (a leg to the EQLs), which the bias gate blocks today | engine flips on 1m closes (wrong for HTF) | `preregistered-htf-ifvg-2026-11-14.md` | to build after the OB sweep |
| 8 | 2026-11-14, week of Apr 15 2024 | Power of 3 / weekly play: HTF picture sets the week's expectation; sell above the open (manipulation), then distribution | weekly open: not built | `preregistered-po3-opening-price-2026-11-14.md` | open |
| 9 | 2026-11-14, Sharif (liquidity types) | FVGs are liquidity/draws too, alongside highs and lows, but only when price is already moving toward them (it reprices into the inefficiency, then often on to the low/high beyond). ICT: "inefficiency to liquidity" (Live Tape Reading 2023-03-15); a volume imbalance/premium array "is gonna be a draw on liquidity" (Bridge Builder). Candidate rule: unfilled FVGs in the direction of travel join the target list (near edge = first touch, CE, far edge) | not yet (to build after the OB sweep) | next | open |
| 10 | 2026-11-14, US100 monthly/weekly/3h Sep–Nov 2026 | Same failed-FVG narrative one level up: weekly FVG fails on a weekly close → IFVG inside a monthly OB, respected 3×, then sellside runs (Sep 16 low, July low). Also Sharif's quarterly-cycle read: the 4-week cycle (Q1–Q4 = weeks of the month), red/green Q2–Q3 = accumulation, blue Q4 = expansion | weekly/monthly TFs needed in pd_return | IFVG pre-reg amendment 2 (weekly+monthly variant) | quarterly: unconditional check on 2022–24 found no Q4 expansion (week 4 range 0.97× avg vs week 2 1.07×); conditional version (Q4 after a Q2–Q3 range) still open |

## Also from ICT's live executions (re-read 2026-11-14; most charts are Sharif's TradingView redraws of ICT's trades, so the markings are his)
Ride the wave in 8 of 11; a sweep of a session/intraday low first in 10 of 11; entries 08:30–11:15 NY (6 on news or
macros); TP1 = nearest internal swing (75–80% off), runner to the real pool; HTF entry arrays mostly 1H/4H FVGs.
