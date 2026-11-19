# Bias

Run through again on 18 Nov 2026 on a fourth chart I had not seen, the Russell 2000, with liquidity ("so far I am happy,
I think we are good"). Confirmed by Sharif on 17 Nov 2026 on three charts I had not seen: the dollar index per timeframe ("well done"), the
FTSE daily ("you see the bias properly now") and the DAX weekly ("perfect, now you've got it").

## His words
- "Just because you made a new swing upward doesn't mean you're bullish; what about the HTF higher low, which is significant."
- "What you saw was smaller pieces of the puzzle. Don't forget the stronger pieces which actually move it all."
- "Price failed to break the second upper BOS, so it's still in the first BOS level, because if the BOS below gets broken then it's a change."
- "Key areas are the bigger picture; the tricky part was 'level below: break = change'."
- "Higher TF highs and lows have higher importance."
- "Don't look at that task's exact values, understand why I put lines where I put them... because if I give you a different chart you'll be confused."

## What counts as a break (confirmed again 18 Nov 2026, on the Russell 2000 run-through)
- "A wick breaking through an area isn't truly a break." (I asked; he: "yes".)
- "If we have a body candle under or above that zone, it's a break."
- A body beyond the level is a break **however the candle got there**. His example was a week that opened already
  under the level: the candle never crossed it, there was a gap between the level and the open, and it is still the
  break. He: "this was a rare instance because there's a gap… so I wanted to clarify it."
- Say it as "a closed candle below (or above) it", naming that candle's timeframe. A level can be broken on the daily
  and not on the weekly at the same moment; both are true.

## How to read it
State it per timeframe first (bull / bear / range), highest timeframe first. For each, name:
1. **the break** that put the bias where it is: a close through a significant high or low;
2. **the level behind it**: the swing that break was built on. A close through it is the change; nothing else is;
3. **the level ahead**: breaking it continues the trend and moves the level behind up to the newest pullback; failing at it changes nothing.
Everything between the levels is the smaller pieces: pullbacks, ranges, one side building.

## The tool and its tests
`bias.py`, tests `test_bias.py`, both beside this file (hand-built candles).

**Mine, not his:** the tool takes "significant" to mean a swing of the timeframe above (a candle of that timeframe
whose high is above the highs either side). That is my way of putting his "higher TF highs and lows have higher
importance" into code. He has not confirmed it, and on the FTSE daily it placed the level behind differently from
his own mark.

**Confirmed by him, 18 Nov 2026:** a break and a change are judged on a close beyond the level, never a wick.
"Correct, and a body close; some form of body needs to do it, not wick."

He read the rest of what is listed as mine on 18 Nov 2026 ("I read your mine content, it's fine"); it stays named
as mine because the words are mine.

Also mine, not his sentences (he said "perfect, now you've got it" to DAX marks drawn this way, which is a check of
the result, not of each rule):
- the level behind is the lowest low (highest high) between the level that was broken and the candle that broke it;
- after a break, only the highest significant high since then continues the trend; a lower high closed through is a
  smaller piece;
- after a change, the new level behind is the extreme since the old one;
- the highest timeframe, with nothing above it, uses its own swings.

Run once on the charts he confirmed, 17 Nov 2026 (a check; nothing was tuned to them):
| Chart | Code against the confirmed hand read |
|---|---|
| DAX | all five timeframes agree; the weekly gives the same levels (October's low behind, the November high ahead) |
| Dollar index | all five agree on direction; the weekly's levels differ from the hand read |
| FTSE | weekly: code says bull, hand read said range. Daily: both bull, but the code puts the level behind at March's low and his own mark is May's low |

## Open questions for him
- **Range, answered 19 Nov 2026:** "Range is consolidative: price isn't really bearish or bullish, or it's eating
  important lows but then it eats important highs, it's almost confused; and it gets to a point where that most recent
  high and most recent low is a range, and nothing is breaking it; it's stuck in that middle area going up and down
  but never breaking it." The tool does not say "range" yet.
- **A close under by a small amount, answered 19 Nov 2026:** "You're right, it was a small close, but if you're
  confused, take a look at that same chart on daily; I don't think you'll be confused by those two lows." When a
  higher timeframe's close beyond a level is marginal, the timeframe below shows whether it was clean. (The second
  sentence is mine. On his example the daily closed far beyond both lows.)
- **"Significant" as a swing of the timeframe above, answered 19 Nov 2026:** "This still counts; it's relative to what
  you're looking at: if you're on daily, obviously weekly and monthly is stronger; if you're on hourly, 4-hour and daily
  is stronger." So the tool's reading stands as far as it goes.
  - **How far up (19 Nov 2026):** "This is relative all the way to the top, but depending on where you're trading
    there is a limit, so 2 up makes sense. For example, if you're trading 15-minute, daily is very steep for you; it's
    not an issue if it's with bias, but if it's against bias the distance between the two timeframes can be wide."
  - The tool now takes the timeframe above and, when given, the one above that (`bias_levels(c, parent, grand)`): a
    turn on either is a significant level. Which timeframes those are is the caller's choice. Tests: a top that is a
    turn only two up counts when two are given and not when one is; it is not a level before it is known there.
- **Where the level behind sits, answered 19 Nov 2026 on the chart where the tool and his mark differ.** I showed
  both and asked: is his low the level behind because the break was built on that pullback, and not on the older,
  lower low? "Yes." So the level behind is the low of the pullback the break was built on. A lower low from the leg
  before it is not the level behind, even though it is the lowest low under the break.
  - **The tool does not do this yet.** It takes the lowest low between the level that was broken and the candle that
    broke it, which on that chart reaches back into the older leg. That rule was already named as mine above; it is
    now known to be wrong where the stretch under the break has its own structure. It has not been changed: a change
    must hold on every chart he has confirmed, not be fitted to this one.
- **Range, on the same chart:** I asked whether the daily is a range now, with price going up and down under the
  level ahead and no closed candle beyond the recent high or low. "Yes, it's a range." The tool says bull there.
