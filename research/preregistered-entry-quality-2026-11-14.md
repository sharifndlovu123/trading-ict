# Pre-registered: entry quality (sweep, then an aggressive move; no entry into chop) — written 2026-11-14, before any code or run

Sharif's batch-2 notes: "just because it's 8am doesn't mean we must enter, we need a sweep, an aggressive move to show
some movement"; "if we see too much consolidation within a key zone, and no aggressive pushes against it, it's not so
valid … we want sharp movement in the direction we want to reach and we expect to enter through a retracement";
"markets are tougher during consolidations"; "a patient play would have been better". ICT rulings §14 (defer the entry
until displacement proves the turn; a range stores orders, it is not a place to enter).

## Gates (each off by default; on in its variant only)
| gate | passes when |
|---|---|
| sweep then displacement | in the 60 min before the decision: a sweep of a session or swing level on the side opposite the trade, **then** a displacement candle (`displacement_mask`, 5m) in the trade direction, in that order |
| no chop in the zone | of the last 12 five-minute candles before the decision, **fewer than 6** trade inside the model's entry zone (its entry FVG, or the POI it returned to) |

## Variants (all five models; everything else at defaults)
"entry: sweep then displacement", "entry: no chop in the zone", "entry: both".

## Test and decision rule
2022-01-03→2024-06-28, the variants tool's in-sample/out-of-sample split, assets US100 US500 US30 XAUUSD XAGUSD, both
cost bases. A cell (model × variant × basis) counts only if its out-of-sample exp R beats that model's baseline with
**z ≥ 2.6** (15 cells per basis) and it has **≥ 30 out-of-sample trades**. Report all. A pass = forward-v2 candidate.
2024-07+ unused. Sharif's batch-2 trades inspired the gates and are not used to score them.
