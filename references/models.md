# ICT Models

One card per **model**: a complete trade recipe the engine can open, close and score.
Concepts (FVG, OB, NWOG…) and strategies (daily bias, weekly profile, PO3 narrative) are *not* models and live elsewhere; a model only references them.

- All times are New York local time (DST-aware).
- **Params** are values the sources disagree on. The engine tests each variant and the vote decides.
- Source priority: ICT's direct words (Twitter Spaces, livestreams, transcripts; "Michael" = ICT) > reference PDFs > third-party write-ups. Contradictions are settled on https://ictindex.io.
- Stops and "Invalid if" rules not stated by a source are engine defaults, open to change.

Card fields: **Time** · **Setup** (sequence that must happen, in order) · **Entry** · **Stop** · **Target** · **Invalid if** · **Patterns** · **Params** · **Source**

- **A vote is a winning trade:** the model said "open here, close here" and price reached the close — its **earliest close (TP1)** — before the stop. One win = one vote. Runner-to-final-target is reported separately.
- **Every model obeys `framework.md`:** time window first, then daily bias, then price in discount (buys) / premium (sells) of both dealing ranges, then a HTF POI, then the entry trigger. An entry FVG outside a POI never opens a trade. Entry, stop and TP1 types are picked from framework.md §7–8.
- **Patterns** (`patterns.md`) are separate but linked: *required* patterns must occur for the model to fire; *tracked* patterns are logged on every trade so we can compare win rates with and without them.

---

## 1. Silver Bullet

- **Time:** entry must be taken inside 03:00–04:00, 10:00–11:00 or 14:00–15:00.
- **Setup:** draw on liquidity identified before the hour → displacement → FVG. The FVG may form *before* the hour; only the entry must be inside it.
- **Entry:** limit inside the FVG.
- **Stop:** beyond the displacement swing.
- **Target:** nearest liquidity in the direction of the trade (e.g. relative equal highs/lows).
- **Invalid if:** no entry fill before the hour ends.
- **Patterns:** tracked — Unicorn, SMT divergence, Turtle Soup at the swept level, algorithmic macro 09:50–10:10 / 10:50–11:10.
- **Framework rule:** the setup must *offer* at least **10 points (handles) on indices, 15 pips on FX** to the draw on liquidity. That is the potential move, not the target; ICT banks 5 handles in his own example. The trade may be held beyond the hour.
- **Gold / silver minimum:** ICT gives none. Default = the same share of the asset's average daily range (14-day ADR) that 10 points is of ES's ADR; fixed-dollar variants are tested beside it.
- **Params:** gold/silver minimum (ADR-scaled vs fixed); entry level in FVG (proximal / CE / distal); strict variant where FVG must form inside the hour.
- **Source:** ICT 2023 Mentorship — reviews of 12 Apr, 23 May, 26 May, 9 Jul 2023; ICT Silver Bullet lesson on minimum trade framework (via ictindex.io).

## 2. 2022 Model

- **Time:** inside a killzone (see `killzones` in the rulebook).
- **Setup:** HTF point of interest → liquidity sweep → market structure shift with displacement → FVG left by the displacement.
- **Entry:** in the FVG.
- **Stop:** beyond the swept liquidity.
- **Target:** HTF FVG, order block, or external high/low.
- **Invalid if:** MSS happens without displacement (no FVG).
- **Patterns:** required — Turtle Soup (the liquidity sweep). Tracked — SMT divergence, Unicorn.
- **Params:** entry level in FVG (proximal / CE / distal); minimum R (2 or 3).
- **Source:** third-party write-ups (Tradezella, LuxAlgo); confirm against ICT transcripts.

## 3. Market Maker Buy Model (MMBM) — Sell Model (MMSM) is the mirror

- **Time:** smart money reversal inside a killzone.
- **Setup:** original consolidation → sell-side curve stepping lower through redistribution areas → reaches HTF discount PD array → market structure break up → stage 1 / stage 2 re-accumulation.
- **Entry:** OTE, FVG or bullish order block during stage 1 or 2. ICT: look directly across from the sell-side redistribution area; up-close candles there are the stage-2 entry.
- **Stop:** below the reversal low.
- **Target (terminus):** the original consolidation high / relative equal highs.
- **Invalid if:** close back through the reversal low; return leg fails to displace through the first interior consolidation; price reclaims the original consolidation from the wrong side.
- **Patterns:** tracked — Unicorn (ICT: the stage-2 entry), SMT divergence at the reversal, Turtle Soup at the reversal low/high.
- **Params:** framing timeframe (H1 / H4 / D1); stage 1 vs stage 2 entry.
- **Source:** ICT Charter Price Action Model 6 (Jan 2024); Market Maker Model PDF p. 2–7.
- **Engine (mechanical v1, `ict_engine/models/model_mmxm.py`):**
  1. *Original consolidation*: `oc_bars` (4) framing bars (15m) whose total range ≤ `oc_range_mult` (2.5) × the median framing-bar range. Its high is the terminus.
  2. *Curve*: price closes below the OC, never trades back above the OC high, reaches at least one OC-width below it, and steps lower through ≥ `min_steps` (1) framing swing highs below the OC low (redistribution = internal targets).
  3. *SMR*: the reversal low runs PDL / Asia low / PWL or trades into a valid 1h/4h bullish FVG (`poi` gate).
  4. *Shift*: bullish MSS on the entry TF (1m) within 120 min of the low.
  5. *Entry*: stage 1 = deepest displacement FVG in the leg off the low; stage 2 = first displacement FVG after a close back above the lowest redistribution high. Limit at the FVG proximal.
  6. *Pricing*: entry in discount of OC high ↔ reversal low. *Stop*: beyond the reversal low. *TP1*: nearest untaken curve level ≥ 1R. *Final*: OC high.
  Variants (`python -m ict_engine.eval.variants … --model mmxm`): stage 2, 1h framing, 5m entries, TP1 cap 2R, 2 steps, no POI, no bias.

## 4. Power of 3 Day (classic buy / sell day)

- **Time:** Judas swing forms in London or NY killzone; reference = 00:00 open.
- **Setup:** bullish bias → price trades *below* the 00:00 open (Judas swing) → reverses. Bearish: mirror above the open.
- **Entry:** at or below the 00:00 open while the low forms (bull); at or above while the high forms (bear).
- **Stop:** beyond the Judas swing extreme.
- **Target:** opposite daily liquidity (PDH/PDL, session high/low).
- **Invalid if:** price closes beyond the Judas extreme before the killzone ends.
- **Patterns:** required — Judas Swing. Tracked — London sets high/low of day, SMT divergence.
- **Params:** which killzone; target choice.
- **Source:** ICT Bible p. 13–14.

## 5. Optimal Trade Entry (OTE)

- **Time:** inside a killzone.
- **Setup:** liquidity taken → MSS with displacement → retracement of that leg.
- **Entry:** 62–79% retracement; 70.5% is the sweet spot.
- **Stop:** 100% of the leg.
- **Target:** 0, −1, −1.5 extensions (some use −2).
- **Invalid if:** retracement exceeds 100%.
- **Patterns:** tracked — Turtle Soup before the leg, SMT divergence.
- **Params:** lower bound 61.8 vs 62; extension target.
- **Source:** third-party write-ups (LuxAlgo); 2022 Content "fibonacci settings" slide still to transcribe.

## 6. PD array return (order block / breaker / mitigation block)

Three variants of one model: price returns to a PD array and reacts.

| Variant | Entry | Stop | Invalid if |
| --- | --- | --- | --- |
| Order block | OB high (bull) / low (bear) | Beyond the OB | Close through its mean threshold (50%) |
| Breaker | Return to the breaker | Beyond the stop-hunt high/low | Close back through the breaker |
| Mitigation block | Return to the block | Beyond the lower high / higher low | Close back through the block |

- **Time:** inside a killzone.
- **Target:** next external liquidity.
- **Patterns:** tracked — Unicorn (breaker + FVG), Turtle Soup.
- **Params:** require FVG above (bull OB) / below (bear OB); require OB near dealing-range 50%.
- **Source:** ICT Bible p. 16–26.
- **Live-execution form (built: `ict_engine/models/model_pd_return.py`, 2026-11-14).** All 6 of ICT's live
  PD-array-return trades (`tests/cases/ict_live_exec.yaml`) used FVG-family arrays (BISI / FVG / IFVG / VI on
  15m–4h), not OB / breaker / mitigation blocks. "HTF PD arrays draw price; LTF PD arrays give the timing"
  (framework.md §5). Mechanics:
  1. A 15m/1h/4h FVG is still valid (§9).
  2. Price returns to it inside a window.
  3. A 1m FVG forms in the reaction; buy limit at its near edge.
  4. Stop at the reaction extreme (variant: beyond the array).
  5. TP1 = nearest untaken liquidity ≥ 1R.
  6. One trade per window.
  The OB / breaker / mitigation variants above are still to build.

---

## 7. TGIF (Friday retracement)

- **Time:** Friday; entry from the 09:30 open, or 13:30–14:00 if no Judas swing at the open.
- **Setup:** the week has trended → on Friday, a false run at 09:30 (Judas) traps traders near the week's high (low), or the high (low) of the week forms around lunch.
- **Entry:** after the false run, in the direction back into the weekly range.
- **Stop:** beyond the high (low) of the week.
- **Target:** retracement of 20–30% of the weekly range (graded: 20%, 25%, 30%).
- **Invalid if:** price makes a new weekly extreme after entry.
- **Patterns:** required — Judas Swing at 09:30 *or* a lunchtime weekly extreme. Tracked — Turtle Soup at the weekly high/low.
- **Params:** target level within 20–30%; entry window.
- **Source:** ICT Mentorship 2023 — T.G.I.F. Setup (Jun 2023); ICT calls it "a day-based algorithmic ICT trading model".

---

## To research (ictindex.io first)

- **Unicorn** as a stand-alone model (currently a pattern in `patterns.md`)
- **SMT reversal** as a stand-alone model — pairs: NQ/ES/YM, gold/silver, DXY/Euro index

## Additions from Sharif's Notion notes (to fold into cards after review)

Sources in `personal/notion/`; ICT unless marked.
- **Silver Bullet (#1):** windows **03:00–04:00, 10:00–11:00, 14:00–15:00** confirmed; **15:00–16:00** as an optional fourth window, scored separately (never 14:00–16:00 as one window) (ruling: `personal/ictindex-rulings.md`). Stop: structural by default; NQ variants fixed 20 handles at 2R, and 12 handles. No "50 handles" stop rule (that was a daily goal of ICT's son). One trade per day — see `framework.md` §10. Sharif's own variant: trade 09:30–11:00, and 14:00–15:30 only when the AM objective wasn't reached; partial only at the first objective (`setups.md`).
- **2022 Model (#2):** sequence = opposing short-term liquidity taken first, then the wanted side, then displacement + BOS + FVG ("secret handshake"); entry on 1–2m; TP1 near the day range's equilibrium (2022 Mentorship). Track IFVG-instead-of-FVG and NDOG/NWOG present (Study Setups database).
- **MMBM/MMSM (#3):** ICT Mentorship 2023 MM lectures ("Michael" = ICT) — stop above the high that rebalanced the imbalance; a broken stop reads as a purge; minimum 15m; works fractally on weekly/daily. Zeussy (third-party) adds the MSS pattern in `patterns.md`.
- **Macro 10:50–11:10 (live exec):** bullish bias → long, TP at the previous day high. Candidate parameter for the macro pattern, or a small model.
- **Candidate model — Cameron's Model (ICT, Twitter Space: taught to his son Cameron; `setups.md` §5):** draw = a nearby hourly/intraday candle high that price is already running to (none visible → 15m); trigger = a 1m/5m swing low taken (even by a tick) and rejected, and the next candle closes up; entry = FVG one timeframe lower (5m → 1m). Target = that high. Sell-side collected at the low supports a faster run. Not stated in the source, so the engine defaults apply: stop beyond the swept low; time = the standard windows, scored per bucket (time-first). One trade per day (Cameron rules, ruling #1). Ready to build.
- **Standard-deviation projection:** −2 / −2.5 / −4 SD of the manipulation leg — a TP type (`framework.md` §7) and reversal-zone pattern, not a model.
