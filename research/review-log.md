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
| 5 | 2026-11-14, 2022 model Apr 16 2024 | Daily OB: confirmation on a close through its open; body quadrants, 50% = MT (ICT rulings §11) | `order_blocks(confirm=)`, `quadrants`, pd_return `ob_confirm/ob_measure` | `preregistered-htf-ob-2026-11-14.md` | sweep running |
| 6 | 2026-11-14, liquidity guidance | Equal highs/lows; pools (EQH near PDH = stronger); trendline phantoms (ICT rulings §12) | `equal_levels`, `liquidity_pools`; trendlines not yet | targets: next | found Sharif's EQL ×3 at 18051.5 |
| 7 | 2026-11-14, 2022 model Apr 16 2024 | Daily FVG failed on a DAILY close → IFVG; leaves EQLs; retest validates; OB inside | engine flips on 1m closes (wrong for HTF) | `preregistered-htf-ifvg-2026-11-14.md` | to build after the OB sweep |

## Also from ICT's live executions (re-read 2026-11-14)
Ride the wave in 8 of 11; a sweep of a session/intraday low first in 10 of 11; entries 08:30–11:15 NY (6 on news or
macros); TP1 = nearest internal swing (75–80% off), runner to the real pool; HTF entry arrays mostly 1H/4H FVGs.
