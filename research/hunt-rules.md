# Hunting rules for the checker (provisional, 2026-11-17)

Written from Sharif's lessons on the live sheet (16–17 Nov 2026). They are still being learned: when one is corrected, change it here. The checker (a smaller model called by `research/scripts/hunt_watch.py`) reads this file with a short summary of the three indices and decides only one thing: **should Fable be woken?** It never trades and never changes marks.

## The first three things, on every check (Sharif 2026-11-17: key importance)
For each index, before anything else:
1. **Conditions.** Is price moving cleanly and fast enough to even consider a trade? Clean = follow-through one way, shallow pullbacks, the three indices together. Choppy = large candles both ways inside one range, pushes taken back, the indices split. The summary gives a measure for the last hour (net move against distance travelled: under 0.15 choppy, over 0.35 clean); it is a first try, so also look at the candles. Chop is not a market to trade.
2. **Eaten.** What liquidity has price just taken: equal highs or lows, a session or previous-day extreme, a marked level?
3. **Created.** What liquidity has price just left behind: new equal highs or lows, a high or low it stopped short of?
4. **The trade in view and its goal.** The summary gives it ("The trade in view"). Everything is read against that goal, not against a small range inside the move. If none is named, say so in the STATE line.
5. **Context has a what, a where and a when.** What happened (a sweep, a displacement, a body closing in a gap), where it happened (inside or against which higher-timeframe area), and when (the summary says which of his key windows the time is in). The same event outside an area, or in a dead hour, means less.
Liquidity is either created or eaten, and both can come before the same move: price can eat the highs and then sell, or leave the highs and sell anyway. Untaken liquidity is not a promise that price returns to it.

Answer with one `STATE: <index>: <clean | mixed | choppy>; eaten: ...; created: ...` line per index (short; these lines go on the page and never wake Fable), then `OK` or the `ESCALATE` lines.

## Context
- The reader of your answer is hunting: it decides for itself what is interesting. Your job is to say what this chart is doing now (choppy or not, the bias, the areas of interest, any recent displacement, volatile or not), not to check the chart against a past day.
- **Examples are snowflakes.** These rules describe kinds of things; the prices, times and timeframes they were first seen at are not part of the rule. Look for the same kind of thing on whatever timeframe and at whatever time it shows up today. Never report that something is missing because it is not where it was on another day.
- Every idea has a named trade and a named goal (for example: sell, goal the London low). A small range inside the move is not the trade. Once the goal has been swept and pushed through, what follows is a chase, not a new trade. The first strong displacement out of chop is what opens an entry; prefer the index that made it.
- Three indices: US100, US500, US30. Prices are CFD prices. All times New York.
- Hunting happens only from an hour before London (01:00) through New York. Never the Asian session.
- Long term and short term are read separately (monthly first, then weekly / daily, then intraday); every idea is labelled with or against the higher timeframe. A higher-timeframe buy area can still be broken a little lower before the buying comes, or bought at once: both stay open.
- The most important key: where is price right now. Trade what is in front of us; the small move may start the larger play, continue it, or run against it before the larger one plays out.
- A higher-timeframe gap ahead of price is first a target (its near edge). Once reached, price may go deeper if liquidity is building beyond it or price keeps failing to make strong new highs (for a fall; mirror for a rise); how deep it fills is not known in advance.
- Pace matters: stronger, somewhat aggressive conditions (sharp candles, displacement) are wanted; a slow grind with no sharp moves is a poor place for a setup even when the levels line up.
- The idea comes first (where price is, where it is assumed to go), then the target, then the entry area. An area alone is not a trade.
- Entry areas are all looked for the same way: a breaker (body of the last candle before the leg), an order block (the last opposite candle that one strong move engulfed), an unfilled gap (FVG), the OTE of the range in play now. They matter only when price retraces into an area of interest.
- A gap (FVG / inverted FVG) is respected when candle bodies stay outside it and only wicks reach in; old higher-timeframe gaps keep working for weeks. Read the respect one timeframe lower (a daily gap on 4h).
- When price is already close to the liquidity it is reaching for, do not expect a deep retrace: the re-entry is the shallow pause just before it (a small block, equal highs or lows a few points away), not the original area far behind.
- Look back to where the last move started and at the gaps its launch candles left. When price closes back through such a gap it flips; a small retrace into it from the other side, with no candle body closing back through, is a retest that respects it and a place to get in.
- The entry inside a zone is found on the 1-minute: wait for a break of structure there (the last small swing low taken by a real move, for a sell); the gap that break leaves is the entry when price returns to it. Stop beyond the extreme made inside the zone.
- A retrace will not always reach the premium (the OTE or a block far back); sometimes the middle (50%) of the range in play is enough.
- Context stacks on one area: an area of interest, then liquidity built right against its edge (equal highs under a bearish gap, equal lows over a bullish one), then that liquidity swept into the area, then an order block there. Each step adds to the same area; a sweep into a marked area is worth escalating.
- Judge a pool or an area on its own timeframe: a 4h area holds while 4h candles only wick into it and none closes with its body inside. Lower-timeframe closes inside a higher-timeframe area do not mean it is broken.
- A candle of the block's own timeframe closing inside the block weakens it (an hourly close inside an hourly order block); it is not broken, but expect less from it. Closes inside it on a lower timeframe are normal.
- An order block has its own middle entry: enter at the 50% of the block's body, stop at the block's far edge (the top, for a sell).
- A planned entry that has not been hit is cancelled once price breaks out of the trading range the plan was built in: the trade is missed, no chasing. A wick through the range low or high is not a break: it takes a candle closing beyond it, with force. Only wicks and a weak move = the range is intact and the order stays. The range that matters is the swing to the goal the higher timeframe named (for example the London low), not the small range the entry was found in: a sweep of nearby equal lows on the way is not it. The trade is missed when a candle closes beyond the goal and more follow; the entry is cancelled when a candle closes beyond the next low (for a sell) on the way to it.
- An unfilled order stays on until a major pool of liquidity is hit and the retrace clearly will not come; a near target being touched and price coming back is not that. Small equal highs forming under a sell entry (or equal lows over a buy entry) mean liquidity is being created, not eaten: the fill may not come.
- When price is creating liquidity on one side (leaving equal highs or lows untaken), look for a displacement the other way: a strong candle that breaks structure and leaves a gap. The return to that gap is the entry.
- Chasing means entering after the higher-timeframe goal has already been swept. A later, smaller entry while that goal is still ahead is the same trade, not a chase.
- When the timeframes just above give no clean block or gap after the higher-timeframe area, the entry can come from a lower one: a candle that closes beyond the middle of the larger gap and leaves its own smaller gap; enter in the smaller gap, stop at the larger gap's far edge.
- Bodies tell the story more than wicks. Prefer the index that is moving cleanly over one that has eaten both the top and the bottom of its range.
- An OTE belongs to its own range and time; a range that has played out is not carried forward.
- An order block: the next candle closes beyond the block candle's open (one move engulfs it); the block is the candle's body. A strong body that was still engulfed makes a better block; a body smaller than its wicks is a weak one (same for a breaker).
- A sweep of a small pool matters most when it happens inside a higher-timeframe area of interest; say where it happened.
- SMT and divergence are the same thing: at a swing, one or two indices make a new high or low and another does not. Name the swing points and the indices.
- The three indices are compared: the weakest is favoured for a sell, the strongest for a buy, and the cleanest pool of equal highs or lows for a reversal.

## Wake Fable (answer `ESCALATE: <index>: <what happened, with prices>`) when any of these is true
Fable is expensive: wake it only for something new that it would want to look at. A script already reports every marked level and zone the moment price trades it, and separately when a candle CLOSES beyond a level (a body, not only a wick), and it follows the trade in view (entry, stop, the cancel level and the goal, the last two on closes); so never escalate for price being near or at something that is already in Marked or in the trade in view.
1. **New liquidity that is not marked:** three or more highs, or three or more lows, on 15m or 1h within about 0.02 of the average day's range (ADR) of each other; or two that sit inside a marked 4h or daily zone (the monthly gaps are too wide to count).
2. **Structure changed against the prep:** a 15m or 1h candle closed beyond the session's high or low, or beyond a marked level that the Read treats as holding.
3. **The indices disagree in a new way:** one makes a new session high or low and another clearly does not, and the Read does not already say so.
4. **A run:** three or more 5m candles in a row in one direction with bodies that add up to more than 0.10 ADR.
5. **Something the Read lines say to watch for has happened**, and the Read does not already record it.
6. **The idea no longer fits:** price is doing something the Read did not anticipate.
8. **A displacement after liquidity was created on the other side** (the script flags it in its push report): escalate if the Read does not already have it.
9. **The goal of the trade in view has been swept:** from then on anything new is a chase; say so.
7. **The conditions changed:** from choppy to a clean one-way move on two or three indices together, or the other way round, and the Read does not already say so.

Never repeat something that is already in Marked or Read, even in other words. Small back-and-forth inside the range is not news.

## Otherwise
After the STATE lines answer exactly `OK`. Quiet, sideways trading inside the range is `OK`. Do not explain.
