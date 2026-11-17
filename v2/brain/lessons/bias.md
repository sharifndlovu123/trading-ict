# Bias

Confirmed by Sharif on 17 Nov 2026 on three charts I had not seen: the dollar index per timeframe ("well done"), the
FTSE daily ("you see the bias properly now") and the DAX weekly ("perfect, now you've got it").

## His words
- "Just because you made a new swing upward doesn't mean you're bullish; what about the HTF higher low, which is significant."
- "What you saw was smaller pieces of the puzzle. Don't forget the stronger pieces which actually move it all."
- "Price failed to break the second upper BOS, so it's still in the first BOS level, because if the BOS below gets broken then it's a change."
- "Key areas are the bigger picture; the tricky part was 'level below: break = change'."
- "Higher TF highs and lows have higher importance."
- "Don't look at that task's exact values, understand why I put lines where I put them... because if I give you a different chart you'll be confused."

## How to read it
State it per timeframe first (bull / bear / range), highest timeframe first. For each, name:
1. **the break** that put the bias where it is: a close through a significant high or low;
2. **the level behind it**: the swing that break was built on. A close through it is the change; nothing else is;
3. **the level ahead**: breaking it continues the trend and moves the level behind up to the newest pullback; failing at it changes nothing.
Everything between the levels is the smaller pieces: pullbacks, ranges, one side building.

## The code and the test of it
`engine/bias.py`, tests `tests/test_bias.py` (hand-built candles). It takes "significant" to mean a swing of the
timeframe above. That is my way of putting his "higher TF highs and lows have higher importance" into code; he has not
confirmed that wording.

Run once on the charts he confirmed, 17 Nov 2026 (a check; nothing was tuned to them):
| Chart | Code against the confirmed hand read |
|---|---|
| DAX | all five timeframes agree; the weekly gives the same levels (October's low behind, the November high ahead) |
| Dollar index | all five agree on direction; the weekly's levels differ from the hand read |
| FTSE | weekly: code says bull, hand read said range. Daily: both bull, but the code puts the level behind at March's low and his own mark is May's low |

## Open questions for him
- How he decides "range" (he uses it often; the code cannot say it).
- Whether "a swing of the timeframe above" is the right meaning of significant, given the FTSE daily difference.
- US100 weekly on 17 Nov 2026: the level behind (July's low) was closed under by a small amount. A change, or too marginal?
