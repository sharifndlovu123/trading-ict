# Trade rubric — one checklist for before and after a trade

The same ten steps grade a trade after it closes (trade-review) and will gate one before it is placed (a future
pre-trade check). Steps 1–8 can be judged from what was **known at the entry**; 9 is management; 10 attributes the
outcome. Each step gets **pass / partial / fail / n/a**, plus one line of evidence from the fact sheet.

The order follows framework.md: time → bias → premium/discount → HTF POI → trigger. The engine's own evidence is in
brackets (research/review-log.md). It shows which steps cost the most so far, so weigh them accordingly.

| # | Step | Pass when | Fact-sheet evidence |
|---|---|---|---|
| 1 | **Time and activity** | Price is moving, not a dry consolidation (activity "normal" or "busy" for this time of day). Inside a killzone / macro / the window the model trades; no high-impact release within ~30 min unless the plan is the news move | `clock_windows`, `activity`, `news` |
| 2 | **Bias / narrative** | Trade side = the HTF story: monthly chain (BOS → EQs → draw), weekly + daily structure. Rides the wave, doesn't catch a reversal. A counter-HTF trade needs a lower-TF reason *and* a near target | `read_kind`, `side_matches_read`, statements (Monthly / Weekly / Daily / Where the play is) |
| 3 | **Dealing range** | Short from premium / long from discount of the current range (OTE best). Fast moves may only give the shallow array | `range` (fraction, half, OTE), `momentum` |
| 4 | **POI / array** | ONE array that fits the move: an HTF level or a tradeable OB (strong body + aggressive push + an event), or the FVG/IFVG the range offers. Not a stack of arrays [OB-picked engine plans lost in every mode, n 25] | `arrays_near`, statements (OB tags) |
| 5 | **Liquidity before** | A pool was taken against the trade first (the fake-out / Judas / inducement): a session high/low, PDH/PDL, EQs, a swing | `swept_before` |
| 6 | **Trigger** | The array acted for us before entering: displacement away, a new LTF FVG our way, or an IFVG flip; not a blind limit at first touch [touch fill −0.15 R/trade, z −4.3; the first 5m FVG after a touch was not enough: 316/460 stopped beyond the zone] | the trader's note / chart; the fill vs `swept_before` |
| 7 | **Stop** | Beyond the zone / the swing that would make the idea wrong, and **beyond** the nearest pool on that side, not short of it or sitting on it | `levels.stop` (beyond_it, gap_adr, at_liquidity), `risk_adr` |
| 8 | **Targets** | TP1 = the nearest internal pool, front-run (just before it, not just past it), R:R ≥ 1; runner to the HTF draw; no big pool in the way that can stall it | `levels.tp1`, `rr_tp1`, pools above/below |
| 9 | **Management** | Partial at TP1, stop to entry after it (Sharif's practice); **day-only**: flat by 16:55 NY unless the plan is explicitly a swing (Sharif 2026-11-16: "hold a trade for the day and that's it") | `after.own` vs `after.day_only`, `overnight` |
| 10 | **Attribution** | Good process + win = earned · good process + loss = acceptable loss · weak process + win = **luck, don't repeat** · weak process + loss = the lesson | steps 1–9 vs the result |

## Known vs hindsight (the rule that keeps reviews fair)
A "you should have seen it" point must cite a **known** fact: something visible on bars before the entry. What price
did afterwards (pools taken next, MFE, stopped-then-target, how far it ran) goes under **What the market did**. Those
are lessons to test on many trades, not blame for this one. Example: "the stop sat 0.04 ADR beyond the 4h high" is
known. "Price came back to tag it" is hindsight.

## Layers to read on every sheet
- **Time and activity:** the entry hour and whether the last hour was quiet, normal or busy for that time.
- **Price:** the `turn` line (hindsight): where price really turned, how far from our entry and stop, and which known level sat there. That level is "the pricing we should have looked at"; whether it was knowable goes under step 4 or 7.
- **Microstructure:** the order-flow line where it exists (NQ 2024): flow with or against the trade over the approach (60 min) and at the trigger (5 min). A reading aid, not a rule.

## Common gaps to look for
- No sweep before the entry (step 5 fail) on a trade that needed one: entering in the middle of the range.
- Stop short of an obvious pool (EQH/EQL, session extreme) on its side: the pool is the magnet that takes it.
- TP1 just past a pool instead of in front of it: price tags the pool and turns without filling the TP.
- A big pool between the entry and TP1 that was never planned as a partial.
- Counter-HTF side with no lower-TF break (CHoCH is not a term we use; say MSS / BOS on the lower TF).
- An overnight hold that gave back an intraday win (`day_only` R > own R).
- Stopped, then TP1 traded later (`stopped_then_target`): the idea was right and the stop or timing wasn't. Check
  whether a confirmation entry (step 6) would have avoided the stop.
