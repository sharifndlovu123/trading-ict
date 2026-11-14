# Pre-registered: targets from liquidity pools and from FVGs ahead of price (written 2026-11-14, before any code or run)

Review log #4 (SB Apr 15 2024: "targets too close; aim at PDL/PWL"), #6 (equal highs/lows = the bigger pool; a
single PDH/PDL matters most when an EQ pool sits near it) and #9 (FVGs are liquidity too, when price is already
moving toward them). ICT rulings §12; ICT "inefficiency to liquidity" (Live Tape Reading 2023-03-15).

## Today (baseline)
`model_2022._targets`: TP1 = the nearest untaken level ≥ `min_tp1_r` away among Asia/PDH/PWH (lows mirrored) and
5m/15m swings; final (runner) = the nearest untaken *external* level (Asia, PD, PW) at or beyond TP1. 50% off at
TP1, runner stop at entry (`partial_frac=0.5`, `runner_stop="entry"`).

## Variants (models 2022_model and pd_return, which share `_targets`; everything else at defaults)
| name | TP1 | final (runner) |
|---|---|---|
| targets: runner to strongest pool | unchanged | the strongest untaken pool (`liquidity_pools`, from 1h/4h/1d swings of the last 10 days + PDH/PDL/PWH/PWL, tol 2 bp) beyond TP1; ties → nearer |
| targets: FVGs ahead as TP1 candidates | adds unfilled 1h/4h/1d FVGs **in the trade direction ahead of entry** (a long sees bear FVGs above; near edge = the target) | unchanged |
| targets: both | as row 2 | as row 1 |

"Already moving toward it" (Sharif) is satisfied by construction: candidates lie ahead of entry in the trade
direction, and every model enters only after a displacement in that direction. FVGs behind price or against the
move are never targets. An FVG counts as filled (and drops out) once traded through its far edge before the
decision; one only touched still counts (ICT: price "never breaches the low of candlestick number 1").

## Test and decision rule
2022-01-03→2024-06-28, the variants tool's in-sample/out-of-sample split, assets US100 US500 US30 XAUUSD XAGUSD,
both cost bases (cfd, futures). Measure = expectancy in R **including the runner** (the change is mostly in the
runner), plus the vote rate (TP1 hit) reported beside it. A variant counts only if its out-of-sample exp R beats
that model's baseline on that basis with z ≥ 2.3 (6 model×variant cells, so a stricter bar than 2.0). Report all
cells. A winner becomes a forward-v2 candidate. 2024-07+ unused. Sharif's examples (Apr 2024, Sep–Nov 2026) inspired
the rule and are not used to score it.

## Not in this test
Trendline "phantom" liquidity (not built); the pool left behind by a failed FVG as the draw (needs the IFVG
result first); conditional quarterly expansion (Q4 out of a Q2–Q3 range: needs its own pre-registration).
