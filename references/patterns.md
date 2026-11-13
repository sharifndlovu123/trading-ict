# ICT Patterns

A **pattern** is a recognisable price event, often tied to a time of day, that tells us what price is likely to do next. It is *not* a trade on its own: it has no fixed entry, stop and target. Models (`models.md`) use patterns as steps or confirmation.

- The engine detects every occurrence and logs whether the expected follow-through happened (**hit rate**). Pattern hit rates are reported separately from model votes.
- **Patterns and models work together.** Each model card lists the patterns it requires or prefers, and every model trade records which patterns were present. That lets us measure, e.g., Silver Bullet win rate *with* a Unicorn vs *without* — the pattern's real contribution to the model.
- All times are New York local time (DST-aware).
- Source priority: ICT's direct words (Twitter Spaces, livestreams, transcripts; "Michael" = ICT) > reference PDFs > third-party write-ups. Contradictions are settled on https://ictindex.io.

Card fields: **When** · **What happens** · **Detect** · **Expect next** · **Source**

---

## Reversal patterns

### Turtle Soup
- **When:** any killzone; strongest at a HTF PD array.
- **What happens:** price runs an obvious old high/low (stop hunt), fails to continue, and reverses back into the range. ICT: "a false breakout pattern… my version of a reversal pattern."
- **Detect:** wick or brief close beyond a liquidity level (old high/low, equal highs/lows, PDH/PDL, session high/low) → close back inside the range.
- **Expect next:** aggressive move away from the swept level toward the opposite side of the range.
- **Source:** ICT 2024 Mentorship Lecture #5 (9 Aug 2024); 2016 Mentorship Month 1; 2017 Mentorship Month 12. Origin: Raschke & Connors, *Street Smarts*.

### Judas Swing
- **When:** 00:00–05:00 (London), around the 00:00 open; also at 09:30 on index futures.
- **What happens:** a false run against the day's true direction that sets the London high or low of the day. Bullish: Asian range high is tripped, then price drops below the 00:00 open and the Asian range low (≈10–20 pips on FX), then reverses.
- **Detect:** HTF bias set → price trades through the 00:00 open against bias → takes the Asian range high/low on that side → displaces back.
- **Expect next:** the swing extreme holds as the day's high/low; price expands in the bias direction, often into the NY session.
- **Source:** ICT 2017 Forex Market Maker Primer — "Understanding the ICT Judas Swing"; Tape Reading Livestream 23 Jan 2024; ICT Bible p. 14.

## Entry patterns

### Unicorn
- **When:** any killzone; ICT highlights it after sell-side is taken at the 09:30 open.
- **What happens:** a fair value gap forms at the same location as a breaker (breaker: low → high → lower low, for bullish).
- **Detect:** breaker block and FVG overlap in price.
- **Expect next:** strong expansion away; ICT calls it "one of the strongest algorithmic entry patterns" and links it to stage 2 of a market maker model.
- **Source:** ICT ES Futures Review 9 Jan 2023; General Market Commentary 14 Nov 2025; 2026 Lecture Series 14 Jul 2026.

### SMT Divergence
- **When:** at a liquidity sweep, inside a killzone.
- **What happens:** one correlated market takes a swing low (high) and the other doesn't.
- **Detect:** pairs — NQ/ES/YM; gold/silver; DXY vs Euro index (inverse: one takes a low while the other fails to take its high).
- **Expect next:** the market that failed to sweep leads the reversal.
- **Source:** ICT Bible p. 11–12; ICT uses NQ vs ES lows (2025 Lecture Series, 8 Apr 2025).

## Time-of-day patterns

### Algorithmic macros
- **When:** 20-minute windows, e.g. 09:50–10:10 and 10:50–11:10.
- **What happens:** "a short list of directives the algorithm will run" to seek liquidity or rebalance an inefficiency.
- **Detect:** within the window, price runs a liquidity level or trades into an open FVG.
- **Expect next:** after the macro, price heads for the opposing liquidity; 09:50–10:10 often sets up the run into the 11:00 lunch hour.
- **Source:** ICT Mentorship 2023 — "Algorithmic Price Delivery & Time Macros Intro" (Jul 2023); Live Tape Reading 6 Mar 2023. Other macro times: to research.

### Opening range (09:30)
- **When:** 09:30 equities open; first 20–30 minutes.
- **What happens:** the opening range forms; liquidity taken outside its high/low hints at the next target.
- **Detect:** high/low of 09:30–10:00; which side gets run first; opening range gap vs settlement.
- **Expect next:** ICT: wait the first 30 minutes, then trade inside the 10 o'clock hour.
- **Source:** Time Macros Intro (Jul 2023); Live Tape Reading 6 Mar 2023.

### London sets the high or low of the day
- **When:** 00:00–05:00.
- **What happens:** ICT: "between midnight New York time and 5 a.m. … there's going to be a high or low form for the daily range."
- **Detect:** which extreme of the day so far formed in London.
- **Expect next:** the other extreme forms later in the day, usually NY.
- **Source:** "Understanding the ICT Judas Swing" (2017).

### Friday retracement (TGIF context)
- **When:** Friday, from the 09:30 open into 13:30–14:00.
- **What happens:** price retraces 20–30% of the week's range, either after a Judas swing at 09:30 or after a lunchtime high/low of the week. The tradable version is a model card (`models.md` → TGIF).
- **Source:** ICT Mentorship 2023 — T.G.I.F. Setup (Jun 2023).

---

## From Sharif's Notion notes

Cleaned sources in `personal/notion/` (each section links its Notion page and screenshots). Third-party patterns are marked; they're tracked, not trusted.

### Three drives vs single run-up (ICT, 2022 Mentorship EP 5)
- **When:** pre-08:30 swings on 15m, read on 5m.
- **What happens:** three drives into a high → it need not break it; a single run-up → expect a trade above the high.
- **Expect next:** displacement the other way, FVG, return into it, continuation.

### 08:30 fake move (ICT, 2022 Mentorship)
- **When:** around the 08:30 release. **What happens:** a move before/at the release, then the real move the other way. If price already rallied into 08:30, the news may push it lower.

### Opening range gap — three cases (ICT, `pd-arrays.md`)
- **When:** 09:30 vs previous RTH close (~16:14). Cases: gap *with* bias → fills, then leaves in bias direction (2 STDV of the gap often near the day's high); gap *against* bias → fills, consolidates, false run, reverses; weekly objective already met → fills and nothing happens.

### SMT picks the market (ICT, Twitter Spaces)
- **When:** long into an FVG, 10:00–11:00. Trade the index whose 1m makes a higher low while the other makes a lower low (mirror for shorts). ES/NQ SMT is stronger; YM often diverges (Trading Extras). Extends **SMT Divergence** above.

### Wick stacking (ICT livestream, Trading Extras)
- A retest into an earlier wick that does *not* reach the wick's 50% → stronger push; a place to add. Tracked on all trades.

### Turtle soup speed check (ICT, Core Content)
- A sweep must be followed by a fast move away. If price consolidates after the sweep it is building equilibrium, not reversing. Refines **Turtle Soup**.

### Weekly high/low day (ICT, `bias.md`)
- Bullish week: weekly low tends to form Sun–Wed, highest odds Tuesday London → Wednesday 07:00. Log day + killzone of every weekly high/low.

### NFP week (ICT — "Michael's tips", Trading Extras)
- **When:** NFP weeks. Mon–Wed beat Thu–Fri; NFP Monday 09:00–09:30 impulsive; limp Monday → strong move at Tuesday 09:30. ICT says "test it" — tag NFP weeks and measure.

### Third-party (tracked only)
- **Zeussy MSS:** push into a SIBI makes the intermediate high; a BISI move breaks it; price returns into the BISI (`setups.md`).
- **TAPDA:** a PD array revisited at the same time of day it formed should hold; failure = first sign of a change in state of delivery (`trading-extras.md`).
- **True opens (Quarterly Theory):** optional premium/discount references — already in `framework.md` §5.

## To research
- Other macro windows beyond 09:50–10:10 and 10:50–11:10
- Asian range rules (size limits, which killzone uses it)
- NY lunch (NYL) behaviour and exact hours
- Weekly profiles (PO3 Fractal Study slides)
