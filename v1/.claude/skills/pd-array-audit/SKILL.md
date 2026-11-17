---
name: pd-array-audit
description: Verify that the engine's PD arrays (FVG, IFVG, volume imbalance, order block, breaker, NWOG) are found correctly and actually used — re-derive each from its timeframe's candles, check nothing comes from the future, and score the engine against the zones Sharif drew in his review pages (match / partial / other TF / other kind / missing / found but filtered off the map). Use whenever a detector or the liquidity map changes, when a review or pattern result hinges on an array type (e.g. "OB plans lose — is the OB even right?"), when someone asks whether arrays are being detected, used, or labelled correctly, or before trusting any finding that depends on PD arrays.
---

# PD-array audit

Every plan, stop and "area considered" sits on a PD array. If an array is drawn wrong, missing, or dropped before the plan sees it, every result built on it is suspect: a losing pattern may be a detection bug rather than a bad idea. This skill checks two separate things:
- **found correctly**: the detectors;
- **used**: what reaches the liquidity map, the read and the plan.

## Run it

```bash
uv run python research/scripts/pd_audit.py --out research/pd-audit/<YYYY-MM-DD>.md \
    [--sources topdown,liqmap,reentry,plans,trades] [--limit N]
```

It takes about 3 minutes for ~100 zones and writes a `.csv` alongside with one row per zone. It only reads `reports/reviews/*.jsonl`; never write there.

## What it checks

1. **Definition.** Every area on the liquidity map at each review moment is re-derived from its timeframe's own candles: the edges must come from a real three-candle gap (FVG/IFVG) or body gap (VI), with the same formation candle. The map rounds prices to 2 decimals, so a tolerance of 0.006 is allowed. Zero-width slivers are flagged.
2. **Timing.** Nothing on the map formed at or after the moment. An IFVG counts only once its close-through has happened (daily and weekly gaps are judged on their own closes, ruling §10).
3. **Agreement with Sharif.** Each zone he drew (FVG / gap / IFVG / order block / breaker, with its TF) is looked up among all detector outputs at that moment, on every TF from 5m to 1w. A zone counts as found only if the engine array formed within 5 candles of the drawing's left edge. The same price from a much older candle is labelled *same price, other candle*, not a match.
   - **match / partial:** overlap (IoU) ≥ 0.5 / ≥ 0.2, same TF and kind.
   - **other TF / other kind:** the engine sees it, but labels it differently from him. This is a definition disagreement; settle it with ictindex.io and the rulings.
   - **same price, other candle / missing:** the detector didn't produce his array. Look at the chart.
   - **on the map = false while found:** a usage filter dropped it (distance from price, top-N per side, lifecycle). The plan can't pick an array that never reaches the map.

## Reading the result

His marks are the reference, but they're a sample (around 100 zones, mostly FVGs on 1d/1w). Report each kind × TF row with its n and don't generalise from 2 breakers.

When the audit flags something, open the chart before concluding. The review pages show the moment (e.g. port 8774/8775 or the liqmap/topdown pages), or render bars with `research/scripts/liqmap_build.py --at <ASSET> <date> <time>`. Then decide whether the detector, the filter, or the drawing is off.

Watch for two traps:
- A missing on the map is not automatically a bug. The map is meant to be selective; it becomes a gap when he **uses** the array (entry or target) and the plan can't see it.
- Treat a finding that rests on few zones as a lead.

## Write-up

The report goes to `research/pd-audit/<date>.md`. Add at the top:
- **Detection:** found exactly / anywhere, per kind, with the weak kinds named.
- **Usage:** how many found arrays never reach the map, by TF and kind, and which filter drops them (check `ict_engine/concepts/liquidity_map.py`: `PER_SIDE`, `max_adr`/`REACH`, `TOPDOWN.min_area_adr`, lifecycle).
- **Definition issues:** the list from the check, grouped.
- **Recommendations:** each one concrete (which function, what to change) and tagged *bug fix* vs *behaviour change*. Hand them to the `change-gate` skill; don't edit engine code from here.

In chat, give the found rate, the usage rate, the top 2–3 problems, and the report path.

## Ground rules
- Follow `CLAUDE.md`. Detectors are concepts: detected, not scored.
- ictindex.io decides definitions; rulings are in `references/personal/ictindex-rulings.md`.
- Never edit `reports/reviews/`.
- Never change detector or map code while a sweep or backtest is running.
