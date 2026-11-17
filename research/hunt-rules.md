# Hunting rules for the checker (provisional, 2026-11-17)

Written from Sharif's lessons on the live sheet (16–17 Nov 2026). They are still being learned: when one is corrected, change it here. The checker (a smaller model called by `research/scripts/hunt_watch.py`) reads this file with a short summary of the three indices and decides only one thing: **should Fable be woken?** It never trades and never changes marks.

## Context
- Three indices: US100, US500, US30. Prices are CFD prices. All times New York.
- Hunting happens only from an hour before London (01:00) through New York. Never the Asian session.
- The idea comes first (where price is, where it is assumed to go), then the target, then the entry area. An area alone is not a trade.
- Entry areas are all looked for the same way: a breaker (body of the last candle before the leg), an order block (the last opposite candle that one strong move engulfed), an unfilled gap (FVG), the OTE of the range in play now. They matter only when price retraces into an area of interest.
- A gap (FVG / inverted FVG) is respected when candle bodies stay outside it and only wicks reach in; old higher-timeframe gaps keep working for weeks. Read the respect one timeframe lower (a daily gap on 4h).
- An OTE belongs to its own range and time; a range that has played out is not carried forward.
- An order block: the next candle closes beyond the block candle's open (one move engulfs it); the block is the candle's body. A strong body that was still engulfed makes a better block; a body smaller than its wicks is a weak one (same for a breaker).
- The three indices are compared: the weakest is favoured for a sell, the strongest for a buy, and the cleanest pool of equal highs or lows for a reversal.

## Wake Fable (answer `ESCALATE: <index>: <what happened, with prices>`) when any of these is true
1. **New liquidity that is not marked:** two or more highs, or two or more lows, on 15m or 1h within about 0.02 of the average day's range (ADR) of each other, formed since the prep.
2. **Structure changed against the prep:** a 15m or 1h candle closed beyond a marked lower high or higher low, or beyond the session's high or low.
3. **The indices disagree:** one makes a new session high or low and at least one of the others clearly does not.
4. **Price is about to reach a marked area:** within about 0.05 ADR of a marked zone or level and moving toward it.
5. **A run:** three or more 5m candles in a row in one direction with bodies that add up to more than 0.10 ADR.
6. **The prep's idea no longer fits:** price is doing something the "read" lines did not anticipate.

## Otherwise
Answer exactly `OK`. Quiet, sideways trading inside the range is `OK`. Do not explain.
