# Liquidity

Taught by Sharif on 17 Nov 2026, starting from the cleaned references and worked on the DAX (weekly, daily, hourly).
He closed the lesson with "that's it, we are good". Its sub-part is `alt-liquidity.md` (imbalances price is drawn to).

**Standing:** taught and confirmed. First marks on the DAX: "okay not bad", with one correction. Then tested on a
chart I had not marked (the FTSE, 17 Nov 2026: liquidity from the weekly down, then alt-liquidity): "nice, you found
content well enough, I'm happy." No eyes code yet (see "Open" below for why).

## What liquidity is
ICT (rulings §12, §18; 2022 mentorship; core content):
- Buy stops rest above old highs (buyside), sell stops below old lows (sellside). "Price only respects where the actual liquidity is."
- Equal or smooth highs / lows are the larger pool: "a larger pool of liquidity… a stronger draw."
- The market builds liquidity, then takes it. "We don't rush in there and just go short because it went above old highs. We're looking for some specific signature."
- After external liquidity is swept, expect internal. After a pool is reached, expect a retracement or consolidation.

Sharif ("my references should be accounted for, they are clear and concise as well as ICT's own"):
- Liquidity = trendlines, equal highs / lows, single levels (previous day / week highs and lows).
- Single levels line up with a nearby equal pool; once the pool is eaten price follows on to the single level.
- Pools are where others take profit, so target them.
- "The market will always create and kill liquidity."

## How to read it (taught on the chart, his words)
1. **Relative to now.** "Draw it based on what you see right now." "Show me liquidity relative to now." A level that
   was liquidity for an earlier price is not liquidity now, even if today's candles cross it again. (My mistake: I
   marked the 5 November low as "eaten today"; it had been run the day after it formed. He: "that's valid, but it's
   valid for when price was at that price.")
2. **From the weekly down.** "Start from weekly, I know it's far up but it's important, that's another hint to bias,
   but remember relative to where we are now." What was just taken and what is left close by says something about the
   bias. (On the DAX: the buyside above had just been taken; what was left close by was sellside below, and the larger
   weekly pool sat on the level behind the weekly bias.)
3. **Not on its own.** Asked whether to think of liquidity independently or this way, his suggestion is this way:
   top-down, beside the bias, relative to now. One simple definition of what it is; which liquidity matters comes
   from the reading.
4. **Original liquidity first, alt-liquidity second** (order of importance; see `alt-liquidity.md`).

## From the FTSE test (his answers)
- Highs that have not been eaten stand as resting liquidity, even when they were made months apart: "the weekly equal
  highs have not been eaten" (July's high with two November highs, drawn as one pool).
- He wants the NWOG and NDOG drawn, not only mentioned, even when small ("for NWOG I don't see it").
- Mine, not his: when a feed has no 4:59 p.m. print (the FTSE stops at 16:00 / 16:14 on this feed), I used the last
  print before the close. He accepted the marks; he did not rule on the method.

## How to pick it out on the chart (his answers, 18 Nov 2026)
- **Equal highs / lows:** "just relatively close to each other; you could put a straight line at one point and the
  other point may not hit it but it's very close by."
- **Eaten or not decides what stays, not distance.** "Focus on if it was eaten first; if it wasn't eaten keep it."
  "If it was eaten it's no longer as useful to us, or if it's swept, it might be important for that current price where
  it's nearby, but if it's not and it's far off in the past, it doesn't help us with old data if it's already eaten."
- **"Eaten" and "swept" are the same thing** (he: "one thing I keep saying, it's 'eaten', 'swept', same thing"). So the sentence above is one rule, not a rule with an exception: liquidity that has been eaten is used up; if that happened near where price is now it can still matter for the present, and if it is far off in the past it does not help.
- **Intraday:** "relative to where price currently is, we look at previous day and previous week for highs or lows
  that were left uneaten."
- **Trendline liquidity: skipped.** "The alt-liquidity tends to eat trendline liq either way."

## The tools and their tests (18 Nov 2026)
`liquidity.py` (old highs and lows and whether each was eaten; what is resting; what the present move ate; equal
highs / lows; the previous day's and week's high and low) and `alt_liquidity.py` (see `alt-liquidity.md`). Tests:
`test_liquidity.py`, `test_alt_liquidity.py`, hand-built candles only.

Run once on the FTSE, the chart he confirmed (a check; nothing was tuned to it): the same weekly and daily picture
as the hand read (buyside 10,964 / 10,980 / 10,991 as one group; sellside 10,511 / 10,526 then 10,364; last week's
low resting; yesterday's low eaten; the hourly BISI under last week's low as the draw; the 9 November daily BISI
traded through). **One difference:** by hand I called the daily lows of 10 to 13 November "eaten today"; the tool
does not list them, because it only counts a low that is a turn (lower than the candle before and after), and those
lows rose one after another. Whether a plain previous daily low counts as liquidity beyond "the previous day" is
his to say.

Choices that are mine, not his (named in the code): what makes an "old high" (a turn); a wick beyond a level is
enough to eat it; "very close by" is a distance the caller passes in, with no built-in number; equal highs are
joined neighbour to neighbour.

**Left to the reading, on purpose (no code):** single levels lining up with a nearby equal pool, pools as targets,
reading from the weekly down, the hint to bias, and original liquidity before alt-liquidity. These belong to the
top-down process (the eyes), which is built later.

## Open
- Taught live earlier in the week but only in v1 notes, to be re-confirmed before they enter: liquidity created
  against an area, swept into an area, equal highs / lows as sub-groups, matching the timeframe of a pool to the
  candles that judge it.
- "Very close by" as a measure: left to the caller for now; to be settled when the eyes are built and he can see what it picks.
