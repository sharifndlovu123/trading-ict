# Sessions: when a trade is looked for

Confirmed by Sharif on 19 Nov 2026, during the show-back of lesson 03. First taught on 16 Nov 2026, before the
rebuild; on 19 Nov I read my old note back to him and he confirmed it ("yes it's right") and added to it. **Confirmed in use
on 20 Nov 2026:** a read of a chart I had not seen, made inside the London morning with the session named from the
start: "so far so good, your read is solid."

**All times are New York time.**

## Why sessions exist
- "Remember the sessions I gave you, and told you we focus on these specific sessions, from this time to this time,
  and we really look for trades within that time; that's locked time, to avoid trading in consolidative markets."
- **The rule:** "Never look for a trade outside of those times."

## Clock times are rules here, and only here
"Don't lock training to specific times BUT, when it comes to sessions it's a must, because time is key for sessions
and when to trade." A time taken from an example chart (when a sweep happened that day) is never a rule. The session
times below are rules: they define when a trade is looked for.

## His own times (the ones a trade is looked for in)
"The times I've marked myself are the times I like, because of what I see on the chart."

| Session | His times | How it is used |
|---|---|---|
| Asian | | Never traded, unless holding a trade from the late New York session |
| London morning | from 2:00 a.m. | Trades are kept here. "London session is good but it tends to be less volatile on average" |
| New York morning | from 9:30 a.m.; his windows 8:20 to 9:00, 9:20 to 10:00 and 10:20 to 11:00 a.m. | Trades are kept here. "NY morning is king" |
| New York PM | "totally from 1 p.m. to 4 p.m."; "the sweet spot… is 2 p.m. to 4 p.m." | "Avoid trading New York PM session unless you're holding a trade or closing it off there" |

- "We try mark our sweet spots more."
- About an hour before a session: point out what is interesting (bias, areas, liquidity); when the session begins,
  watch what price does. (From the 16 Nov teaching, confirmed with the rest on 19 Nov.)
- Outside these times the chart is still read top to bottom, so that what is resting and what was swept is known when
  a window opens. No entry is looked for. (This sentence is mine; he confirmed the rule it follows from.)

## Opening, holding and closing (his answers, 19 Nov 2026)
- "You're allowed to open a trade during the session, and entries during kill zones is very nice."
- "The hour before a session is for you to start looking and analysing things such as higher TF, bias, what's price
  trying to do; but your entries or trigger mode should only initiate within the kill zones / special times we
  mentioned. There's reasons we mentioned them: they tend to favour us more and have more volatile movements."
- "You can keep trades open as long as you like, but try not overhold and reach end of the trading day… at the end
  of the day our close should be close."
- A trade from London can carry into New York. His example: a sell found in London with a bearish bias, targets hit,
  runners left; in the New York session "we're watching and we consider selling again; there's nothing wrong with
  that."
- Runners: "try to have a trailing stop; don't trail for TP 1, you'll normally get knocked out early if you do so;
  and don't trail until the trade range you're currently focusing on is hit."

## The reference definitions he gave beside his own (ICT's, as he pasted them)
| Session | Whole session | Narrower window |
|---|---|---|
| Asian | about 7:00 p.m. to 5:00 a.m. | the Asian range is 8:00 p.m. to midnight; its active window is often given as 6:00 to 9:00 p.m. |
| London | roughly 2:00 a.m. to 10:00 or 11:00 a.m. | kill zone 2:00 to 5:00 a.m. (also defined as 1:00 to 5:00 a.m. in a later lesson) |
| New York morning | 8:30 to 11:00 a.m. | kill zone 7:00 to 10:00 a.m. |
| New York PM | 1:00 to 4:00 p.m. | |

His own times sit inside these. His are the ones used for looking for a trade; these name the sessions and say how
wide they run.

## A rhythm inside the New York morning (to be learned by watching; not a rule)
"From 8:30 we are seeing the early move, from 9:30 we are seeing the move play out, from 10:00 we normally missed it
and are catching the continuation. But don't be fixed to this… sometimes we will have a weird day where price reaches
an important area we have, and price driving into that area might be the 8:30 to 9:30, and the sell from that
important area could be anywhere from 10:00. And when I say these specific times, just be fluid with it; maybe it
might happen at 10:05."

On my unconfirmed link about the early move: "this is just to keep in mind; as I said, that pattern can change, but
it's good to be aware of it. When we backtest you will notice, if you skip 8:30 and start looking just before 9:30
it might be a bit easier, because some trickery has already been pushed out."

## The tool and its tests (20 Nov 2026)
`sessions.py`, tests `test_sessions.py`, beside this file. He asked whether sessions need a tool and tests; they do,
because "is this a time to look for an entry?" is a question with one right answer.

- `stance(minute)` says what may be done at a minute of the New York clock: **entry** (inside a kill zone or one of
  his windows), **manage** (the New York PM session or the Asian hours: hold or close only), or **read** (anything
  else: read the chart, look for no trade).
- `his_window`, `kill_zone`, `sessions` and `pm_sweet_spot` answer the smaller questions; `new_york_clock` turns a
  moment into the New York clock, right in summer and in winter.
- Every clock time in the code is one of his definitions above. No candles or prices are read.

**Mine, not his, and named in the code:** joining the kill zones and his own windows into one answer; taking the later
of the two ends he gave for London; using the commonly used London kill zone and not the wider one from the later
lesson; where the Asian hours and London overlap, London decides; saying nothing about the day of the week.

The tests check every edge of every window, the overlap, and the clock on both sides of the clock change. They do not
use price scales or timeframes, because the tool reads none; the context check was taught that a clock-only tool is
tested this way (with tests of its own, so that a tool that reads prices cannot use the same door).

## Links

| Comes to mind when | Then look for | Status |
|---|---|---|
| everything lines up for an entry | whether the moment is inside one of his session times; outside them no trade is looked for | stated by Sharif, 19 Nov 2026 |
| a session is about an hour away | what is interesting from the top down: bias, areas, liquidity resting and liquidity already swept | stated by Sharif, 19 Nov 2026 |
| the New York PM session has begun | only managing or closing a trade already open | stated by Sharif, 19 Nov 2026 |
| a move starts early in the New York morning | whether it is the early move, with the real move still to come: to keep in mind, the pattern can change | stated by Sharif, 19 Nov 2026 |

## Open questions for him
- "End of the trading day" for closing: the exact time he means.
- Whether a trade may be opened anywhere inside a session ("you're allowed to open a trade during the session") or
  only inside a kill zone or one of his windows ("your entries or trigger mode should only initiate within the kill
  zones / special times"). The tool takes the second.
- "About an hour before a session": before which start, for New York.
