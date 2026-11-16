# The entry Sharif waits for — from his own saves (2026-11-16)

Source: 24 handling saves (`reports/reviews/handling.jsonl`, port 8767, read for the first time), 4 plan saves (8774), 5 trade saves (8775), 23 re-entry saves (8769). Read only. His words are quoted; the engine's trade on each item is the thing he was commenting on.

## What he says, grouped
**1. Be patient until price reaches the higher-timeframe area** (the most repeated note)
- "sold a bit too early, try a 50% of the 4h fvg at 10am 7th" (US100 8 Mar 2023)
- "sold too early, notice the fvg at 4hr 10am 11th" (US500 14 Mar 2022)
- "the short was way too early, this is back to the premium pricing … we had to be a little more patient, nice FVG found at 10am 19 Jan" (US30 20 Jan 2022)
- "you sold a bit early, the NY session was a better choice here" (US100 13 May 2022)
- "bad trade, very late sell … wait for 1h retest on this OB" (re-entry, US100 8 Aug 2023)
- "short is nice, but you're shorting quite late" (US500 10 Jun 2022)

**2. Then the 15-minute chart has to show momentum**
- "there's a bigger fvg on 4 hour … price reached that area, and we start watching, on the smaller timeframes 15, we see momentum building down; that's where your decision is nice" (US100 26 Sep 2022)
- "no major displacement occurred as yet, wasn't worth any trade. I made a different entry based off the displacement at 8:30 am" (US500 10 Aug 2023)
- "if we get a break higher and a displacement down I'll look to continue downward" (US500 25 Oct 2022)

**3. The side comes from where price is now, not from the daily bias**
- "the no. 1 focus is where we currently are" (US100 8 Jun 2023)
- "the bias may be buying, but we need current structures to support it first. I think you took the bias overall too controlled" (US500 24 Aug 2022: the engine was long, he sold from a 15m order block after a 15m displacement down and a fake push into 15m buyside)
- "wrong bias, we should have been selling here. look at the fvg 15 min 14:30" (US100 3 Feb 2022)
- "buying here was very risky, the momentum is selling heavy … I would have sold instead" (US100 13 Sep 2022)

**4. Entry on the retrace into the gap the displacement left; stop beyond the sweep; partials**
- His own entries: a 15m FVG under 15m equal highs after a 15m BOS (US500 10 Jun 2022); a 15m order block after "displacement" then "fake push" (US500 24 Aug 2022); a 5m FVG after the 08:30 displacement (US100 13 Sep 2022).
- Stops: "beyond the sweep extreme" every time; where he moved the engine's stop it was 2.3× wider (median of 7).
- Targets: swing highs/lows, two or three of them (50% / 25% / 25%); his first target was 2.2 R away (median) against the engine's 2.0.
- "if we took our partials we would have won here" (US100 20 Dec 2022)

**5. A failed area flips**
- "if price breaks below this level, the OB, and retests it below, we are looking to sell to reach our stop" (US500 29 Apr 2022) — the flip leg of the engine plan.

**6. Losses he accepts**: "nice this was just a loss", "we just got swept out by a minor liq grab, but nice eye" (5 of the 13 losing trades).

## What was already tested, piece by piece (all on the 2022 model or MMxM; none passed)
Entry on 5m / 15m (#timeframes), entry inside a 4h FVG (#14, nested), sweep then displacement, premium/discount of the range in play, a limit at the 50% / the OTE, re-entry after a stop (#32–33), a 15m displacement setting the side (#31), stops on 15m / 1h swings. Each was a gate or a change on a setup that still **starts from a 1-minute sweep and shift**.

## What has not been tested: the whole sequence, starting from the area
The PD-array-return model (`ict_engine/models/model_pd_return.py`) is built in his order — the area first, then the reaction — but with a 1m trigger within 30 minutes, the daily bias, and the near edge as "reached". Configured to his recipe (variants `recipe: …` in `ict_engine/eval/variants.py`):

| His words | Setting |
|---|---|
| the 4h / 1h FVG is the area | `htf_tfs=("1h", "4h")` (+ order blocks in one variant) |
| be patient: its 50% | `return_level="ce"` (new option, off by default) |
| watch the 15 for momentum | `trigger_tf="15m"`, up to 4 hours after the area is reached (`trigger_wait_min=240`); a 5m version with 2 hours |
| where we currently are, not the daily bias | `use_bias=False` (the side is the area's direction, confirmed by the 15m gap) |
| NY was the better choice | `windows=("ny_am_kz", "ny_pm_kz")` |
| stop beyond the sweep extreme | `stop_mode="reaction"` (the default): beyond the extreme made between reaching the area and the 15m gap |
| partials at the first swing | defaults: TP1 = the nearest untaken liquidity ≥ 1 R, 50% off, runner at breakeven |

## Test
In-sample, three indices, 2022-01-03 → 2024-06-28, futures cost: the model's baseline against each recipe variant and the full recipe. A variant is worth a pre-registration only if it beats the baseline pooled **and on at least 2 of the 3 indices**, with enough trades (≥ 30 an index). 2021 is the clean year for whatever qualifies.

What this cannot capture yet: the side flipping against the area (his sells from a 15m order block while the area was bullish), which is the engine plan's flip leg; and his reading of "displacement" by eye.

## Result
_(appended when the run finishes)_
