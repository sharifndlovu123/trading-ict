# Alt-liquidity: imbalances price is drawn to

Sub-part of `lesson.md`. Taught by Sharif on 17 Nov 2026, question by question; every line below is his answer unless
marked as mine.

- **The name of the family is imbalance**, not FVG. "It's actually called an imbalance not FVG; imbalances have types,
  such as IFVG, FVG, NDOG, NWOG, volume imbalance."
- **Why they are alt-liquidity:** "they all act like alt-liquidity because price is drawn to it."
- **Order:** "original liq is first, alts seem to follow through" = order of importance. The pools of stops are the
  main draw and are marked first; imbalances are secondary draws.
- Read the same way as liquidity: from the weekly down, relative to where price is now.
- The opening range gap is technically an imbalance, but he dropped it: "skip the opening range gap, I don't want it anymore."

## The types
| Type | What it is | How long it is used | Weight |
|---|---|---|---|
| NDOG | "Prior session's 5 p.m. close to the 6 p.m. futures reopen, typically the next day's gap." | Current week only. "Once it's filled it can still be useful through the day but not for the week." | "A nice to have; sometimes it tells us something, sometimes it doesn't." Very small: not that important. Very big: can be nice, but "sometimes it fills half or a portion and the rest later. They normally always fill." |
| NWOG | "Friday's close at 4:59 p.m. to Sunday's 6 p.m. open." One thing, not two: on the regular-hours chart the gap is visible, on the full-hours chart it is not but can be marked. "Use actual, and it's important to use the lowest timeframe available when marking them, so 1m." | The week. "Within that week it can be a useful area." | "Same but has more weight because it's weekly; same filling logic, fills if it wants to but tends to." |
| Volume imbalance | "Absence of body volume": two candles side by side whose bodies do not touch while the wicks overlap. | "Drop it once it's not anywhere near the current price range being watched." | "Higher timeframe, the stronger." |
| FVG | "A three-candle price imbalance: the middle candle moves so sharply that there's a gap between the first candle's range and the third candle's range. ICT describes it as an area where price was delivered inefficiently; traders watch to see whether price returns to that area." | "Both count as a draw when unfilled, but when price is already moving in their direction." | "ICT says price may later reprice into these inefficiencies, but that is not a guarantee every gap will fill." |
| IFVG | "Inversion Fair Value Gap: an earlier FVG that price trades through, then later treats as support or resistance in the opposite direction from its original role. For example, price can trade up through a gap and later use it as support, or trade down through it and later use it as resistance." | "Exact same things" as the FVG. | Same. |

**The two FVGs** (he wants them kept apart: "there is a difference"):
- **BISI**, buy-side imbalance, sell-side inefficiency: "a fair value gap formed by an up-close candle… associated with upward delivery."
- **SIBI**, sell-side imbalance, buy-side inefficiency: "a fair value gap formed by a down-close candle… associated with downward delivery."

FVG and IFVG were taken last "because they're PD arrays": they are also traded from. This file covers only their role
as a draw; trading from them is a later concept.

## My readings, not yet confirmed by him
- "Moving in their direction" = price is already heading toward the gap; an unfilled gap that price is moving away
  from is not a draw right now.
- Marking on the 1-minute applies to the NDOG too, since it is also two exact prices.

## The tools and their tests (18 Nov 2026)
`alt_liquidity.py`: `fvgs` (BISI / SIBI, untouched / partly / filled, and whether it was traded through = IFVG),
`volume_imbalances`, `is_draw` (unfilled and price already moving toward it), `opening_gaps` (NDOG / NWOG from the
1-minute) and `in_use` (how long each is used). Tests: `test_alt_liquidity.py`.

Choices that are mine, named in the code: "filled" = price has traded across the whole gap, "partly" = into it;
"traded through" for an IFVG = a later candle closed beyond the far edge; with no 4:59 p.m. print, the last print
before 5 p.m. is the close.
A three-candle gap whose middle candle did not close in the gap's direction is left unnamed. An IFVG is only
flagged as possible; whether price then treats it as support or resistance is read on the chart.

**Left to the reading, on purpose (no code):** how much weight each type gets (the NWOG more than the NDOG, a higher
timeframe's volume imbalance more than a lower one's), whether a gap is too small to matter, and dropping a volume
imbalance once it is nowhere near the price range being watched.
