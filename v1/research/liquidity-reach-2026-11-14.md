# Liquidity reach: which levels does price actually take? (descriptive, in-sample, 2026-11-14)

Script: `research/scripts/liquidity_reach.py` → `reports/liquidity-reach.parquet`. In-sample only (2022-01-03 →
2023-09-28), futures backtests, every filled trade: 2022 model 886, MMxM 562 (the 2022 model takes no silver trades on
futures — all 1,674 silver setups reaching the target gate fail it). For each trade, every untaken level ahead of entry
known at the decision (lookback 20 days): PDH/PDL, PWH/PWL, Asia, London, 15m/1h/4h/1d swings, 1h/4h equal highs/lows,
1h/4h/1d opposite FVGs (near edge, CE, far edge). Median 32 (2022 model) / 44 (MMxM) levels per trade. Selects nothing.

## Result: liquidity is reached at random-walk rates
If price after the entry were a coin flip, the chance of reaching a level d R away before the 1 R stop is 1/(1+d)
(gambler's ruin). Actual vs that baseline, all types pooled:

| distance | 2022 model actual | MMxM actual | random 1/(1+d) |
|---|---|---|---|
| 0–1 R | 72% | 62% | ≈ 65% |
| 1–2 R | 35% | 36% | ≈ 40% |
| 2–3 R | 30% | 25% | ≈ 29% |
| 3–5 R | 22% | 19% | ≈ 20% |
| 5–10 R | 12% | 13% | ≈ 12% |

By type (per-trade averaged excess over 1/(1+d), levels ≤ 10 R): no type is reliably above random. 2022 model: best
1h FVG near edge +2.8 pts (z 2.0), London +2.8 (z 1.0); PDH −5.6 (z −2.1). MMxM: best PDL/PWH +1.3 (z 0.4); 1h equal
highs −6.2 (z −2.5), daily FVG CE −6.3 (z −2.3). With 20 types per model, |z| ≈ 2 is what chance alone produces.

Without the stop, levels are taken often (London 38–55% by the next day's close; PDH/PDL 37–49%) — but not before the
stop more than chance says.

## What it means
- **A target cannot create an edge by itself.** Aiming at a level d R away pays d × P(hit) − (1 − P(hit)) ≈ 0 when
  P(hit) ≈ 1/(1+d), whatever the level is called. That is why every target test so far (liquidity pools, FVG TP1,
  hold, 50% of the 4h range) landed within ±0.2 R: review log #4, #6, #9, #12, #16.
- **The edge has to come from the entry** (side, timing, price) — exactly what Sharif's triage notes correct most:
  "too early" (16), premium of the current range (8), wrong side of the bias (6).
- A TP ladder is still useful for *shaping* (more frequent wins, partials, a runner) but should only be tested on top
  of an entry that has an edge; on today's entries it can only rearrange ≈ 0.

## Freshness split (2026-11-15; ruling §18 "engineered liquidity", review log #21)
Same trades and levels, each level tagged with when it formed (age at the decision). Excess hit rate (before the stop)
over random 1/(1+d), per-trade averaged, levels ≤ 10 R:

| age | 2022 model | MMxM |
|---|---|---|
| < 4 h | +1.3 pts (z 1.1) | −0.7 (z −0.4) |
| 4–12 h | +0.8 (z 0.5) | −0.6 (z −0.4) |
| 12–24 h | −1.6 (z −0.9) | +0.5 (z 0.3) |
| 1–3 d | −0.5 (z −0.2) | −1.1 (z −0.4) |
| > 3 d | −1.7 (z −1.1) | +0.1 (z 0.0) |

By family (equal highs/lows, swings, FVGs) no cell reaches |z| 2. The 2022 model shows a faint fresh-over-old slope
(+1.3 → −1.7 pts), MMxM none. **Fresh, recently built liquidity is not reached more often than old liquidity from these
entries.** Together with the main result, the target side is not where the edge is lost: from today's entries price is
a coin flip in either direction, so any level is a coin flip. The entry (side, timing, curve stage — review log #20–28)
is the lever.
