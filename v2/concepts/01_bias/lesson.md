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

## Links

Drafted on 20 Nov 2026 from what he had already said in this lesson; the when / then wording is mine. He read them
the same day: "perfect".

| Comes to mind when | Then look for | Status |
|---|---|---|
| a chart is opened for a read | the bias on each timeframe first, from the highest down: the break that set it, the level behind it, the level ahead | stated by Sharif, 17 Nov 2026 |
| a candle body closes through the level behind | a change of bias on that candle's own timeframe | stated by Sharif, 17 Nov 2026 |
| only a wick goes through a level | no break: the level still stands | stated by Sharif, 18 Nov 2026 |
| a new swing forms against the bias | the level behind: while no body has closed through it, nothing has changed | stated by Sharif, 17 Nov 2026 |
| the level ahead is not broken | no change: the bias is still the one the last break set | stated by Sharif, 17 Nov 2026 |
| the candles make a break hard to judge | the line chart: whether the bodies made a higher high or a lower low | stated by Sharif, 19 Nov 2026 |
| a close beyond a level is marginal | the same level one timeframe down, where the close may be clean | stated by Sharif, 19 Nov 2026 |
| a high or low is being weighed | which timeframe it turned: the ones above the chart being read are stronger, about two up | stated by Sharif, 19 Nov 2026 |
| the bias has just changed | the pullback the break was built on, as the new level behind | stated by Sharif, 19 Nov 2026 |
| price swings between its most recent important high and low and no body closes beyond either | a range building: a moment inside the bias, not a change of it | stated by Sharif, 20 Nov 2026 |
| a low or high inside a range goes only a little past the edge and price comes straight back | equal lows or equal highs at that edge, not a break | stated by Sharif, 20 Nov 2026 |
| a range is building | the chance of a break above or below, which could change the bias on that timeframe | stated by Sharif, 20 Nov 2026 |

## Range (taught 20 Nov 2026, with a drawing of his own)

He drew one "in simple terms", and made it tricky on purpose: a low, then the highest high, then many swings between
the two with no order to them; one later low goes just under the bottom edge and comes straight back; the last high
stops just under the top edge.

- **What it is** (19 Nov 2026): "Range is consolidative: price isn't really bearish or bullish, or it's eating
  important lows but then it eats important highs, it's almost confused; and it gets to a point where that most recent
  high and most recent low is a range, and nothing is breaking it; it's stuck in that middle area going up and down
  but never breaking it."
- **The tricky part:** "Notice how it nearly broke, it just smidged the bottom; those are situations where it can be
  confusing, and that's an EQL." A low that goes only a little past the edge has joined it as an equal low. On his
  drawing he wrote "failed to break this low".
- **What ends it:** I asked whether it is a body closing clearly beyond an edge, as for bias. "Same as break for bias."
- **A range is a moment, not a third bias.** "What you'll notice more often is that a bias on a higher timeframe could
  be bullish, but there's a range building, or vice versa with bearish but a range is building now. A range is more
  like a moment."
- **What it can point to:** "When there's a range, it can also indicate the possibility of a break below or above;
  can dictate the possible bias change, depending on timeframe perspective, which we discussed already."

**What this settles.** On the chart where he first said "it's a range" and then "it's bull", both were true: the bias
is bull (the bodies made a higher high and the level behind stands), and the moment is a range (since that high,
price has swung between it and the low below with no body beyond either). He: "yes, this makes much more sense."

**How it is said in a read (mine):** the bias per timeframe stays bull or bear; where a range is building, that is
added with its two edges. "Range" does not replace the bias.

### Shown back on real charts, and corrected (20 Nov 2026)
I looked for ranges on charts I had not read and showed him several. "You're getting it." Then, on a weekly he
pointed me to, I marked two stretches as ranges and he corrected one:

- **Making highs is not a range.** "B isn't a range really; notice how it was making highs." Each new top there went
  clearly above the last, while the lows looked flat. That is price moving up with deep pullbacks. A range makes no new
  highs and no new lows.
- **A sweep is not an equal high.** I had marked two highs as equal that were far apart. "The EQHs you marked… those
  are clearly not; the wicks are separated from each other quite far"; the first high "swept it quite deep enough, the
  second sweep was already too deep"; "that EQH you marked is way too big." I had judged by feel and not used his
  eye's measure (lesson 02). Checked afterwards against the tool: five of six equal sets I had drawn by hand in two
  days were not equal.
- **Where to look for one.** "With range it's often harder to see it on higher timeframes, but if you're on 4-hourly
  and using a small timeframe, you'll find ranges easier."
- **It lasts.** Of the stretch that was a range: "notice how price was inside that range for some time too."

**The test I gave back, which he confirmed ("that's correct"):**
1. Find the most recent important high and low.
2. Price has turned at least a few times between them, over some time.
3. No high clearly above the top and no low clearly below the bottom, judged by his eye's measure for "very close".
   A smidge within that measure is an equal high or low.
4. It ends with a body closing beyond an edge.

**No tool yet.** "A few times" and "some time" are not numbers he has given, so the tool still gives only the bias.
It stays read by eye, with the test above.

## Open questions for him
- Range for a machine: how many turns are "a few", and how long is "some time". The rest of the test is confirmed.
- Some of the lower-timeframe examples I showed him had a low clearly under the bottom edge; by the confirmed test
  those stopped being ranges at that candle. He has not looked at each one.
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
  - **The tool, fixed the same day.** While the bias is bear, a close above a significant high made after the low
    of the fall names the pullback under that high; if the level behind is then closed through, that pullback's low is
    the new level behind (the mirror for a fall). If a later candle closes back through the pullback, it is dropped
    and the old reading (the low the move came from) stands. How the pullback is found is mine; that it is the
    pullback and not the lowest low is his.
  - Run once on ten instruments and five timeframes after the change, nothing tuned: 46 of 50 readings are the same
    as before, including every reading he has confirmed, and the chart he asked about now puts the level behind where
    he marked it. The other three that moved are small shifts on charts he has not looked at.
- **Range, on the same chart:** I asked whether the daily is a range now, with price going up and down under the
  level ahead and no closed candle beyond the recent high or low. "Yes, it's a range." The tool says bull there.
  - Why it is tricky, in his words: "Daily is bullish; one thing that would make it range as a possibility is the BOS
    at daily: it exists, but notice how it isn't so powerful, so to us daily does range, but at the same time it did
    technically break the high."
- **Read bias on a line chart (19 Nov 2026):** "Maybe to make your life easier, when looking at bias, try using line
  chart. It focuses on body only, and body is strength."
  - **My mistake, and his correction.** I looked at the line chart and called that break weak, because the closes
    were only a little above the old highest close. He: "But notice, on line chart, that's a clearer BOS; this would
    show higher high, and it's bodies talking." On closes the new high is plainly above the old one: a higher high
    made by bodies. The candle chart was the confusing one, because the old high there was a wick.
  - **And it settles the range question on that chart.** After seeing the levels drawn: "With the line chart approach,
    this is strength; in this instance, it's not range, it's bull." So his earlier "yes, it's a range" was the candle
    chart's reading; on closes the same daily is bull, which is also what the tool says. When the candles look like a
    range and the line chart shows the bodies making a higher high, the line chart decides. (The last sentence is
    mine.)
  - The tool can now read this way (`as_line`, tests beside it). It is an option, not the default.
  - Mine, from running it once on five charts (nothing tuned): read mechanically on closes, the tool turns more
    often than he does, and on one weekly he had confirmed as bull it says bear. So for now the line chart is for the eye, to
    see whether the bodies made a higher high or a lower low; the tool's line reading is not trusted yet.
