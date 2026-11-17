# Hunting rules for the checker (provisional, 2026-11-17)

Written from Sharif's lessons on the live sheet (16–17 Nov 2026). They are still being learned: when one is corrected, change it here. The checker (a smaller model called by `research/scripts/hunt_watch.py`) reads this file with a short summary of the three indices and decides only one thing: **should Fable be woken?** It never trades and never changes marks.

## Context
- Three indices: US100, US500, US30. Prices are CFD prices. All times New York.
- Hunting happens only from an hour before London (01:00) through New York. Never the Asian session.
- Long term and short term are read separately (monthly first, then weekly / daily, then intraday); every idea is labelled with or against the higher timeframe. A higher-timeframe buy area can still be broken a little lower before the buying comes, or bought at once: both stay open.
- The most important key: where is price right now. Trade what is in front of us; the small move may start the larger play, continue it, or run against it before the larger one plays out.
- A higher-timeframe gap ahead of price is first a target (its near edge). Once reached, price may go deeper if liquidity is building beyond it or price keeps failing to make strong new highs (for a fall; mirror for a rise); how deep it fills is not known in advance.
- The idea comes first (where price is, where it is assumed to go), then the target, then the entry area. An area alone is not a trade.
- Entry areas are all looked for the same way: a breaker (body of the last candle before the leg), an order block (the last opposite candle that one strong move engulfed), an unfilled gap (FVG), the OTE of the range in play now. They matter only when price retraces into an area of interest.
- A gap (FVG / inverted FVG) is respected when candle bodies stay outside it and only wicks reach in; old higher-timeframe gaps keep working for weeks. Read the respect one timeframe lower (a daily gap on 4h).
- A planned entry that has not been hit is cancelled once price breaks out of the trading range the plan was built in: the trade is missed, no chasing.
- An OTE belongs to its own range and time; a range that has played out is not carried forward.
- An order block: the next candle closes beyond the block candle's open (one move engulfs it); the block is the candle's body. A strong body that was still engulfed makes a better block; a body smaller than its wicks is a weak one (same for a breaker).
- A sweep of a small pool matters most when it happens inside a higher-timeframe area of interest; say where it happened.
- SMT and divergence are the same thing: at a swing, one or two indices make a new high or low and another does not. Name the swing points and the indices.
- The three indices are compared: the weakest is favoured for a sell, the strongest for a buy, and the cleanest pool of equal highs or lows for a reversal.

## Wake Fable (answer `ESCALATE: <index>: <what happened, with prices>`) when any of these is true
Fable is expensive: wake it only for something new that it would want to look at. A script already reports every marked level and zone the moment price trades it, so never escalate for price being near or at something that is already in Marked.
1. **New liquidity that is not marked:** three or more highs, or three or more lows, on 15m or 1h within about 0.02 of the average day's range (ADR) of each other; or two that sit inside a marked higher-timeframe zone.
2. **Structure changed against the prep:** a 15m or 1h candle closed beyond the session's high or low, or beyond a marked level that the Read treats as holding.
3. **The indices disagree in a new way:** one makes a new session high or low and another clearly does not, and the Read does not already say so.
4. **A run:** three or more 5m candles in a row in one direction with bodies that add up to more than 0.10 ADR.
5. **Something the Read lines say to watch for has happened**, and the Read does not already record it.
6. **The idea no longer fits:** price is doing something the Read did not anticipate.

Never repeat something that is already in Marked or Read, even in other words. Small back-and-forth inside the range is not news.

## Otherwise
Answer exactly `OK`. Quiet, sideways trading inside the range is `OK`. Do not explain.
