# Sharif's named targets on triage trades (descriptive, in-sample, 2026-11-15) — selects nothing

Source: the blind triage answers (`reports/reviews/triage-read.jsonl`, in-sample setups 2022-01-03 → 2023-09-28). Where a
note named a target level ("target" theme: PDH, PWL, PWH …), the level was located on the bars before the decision and
checked against the engine's own trade path.

| | result |
|---|---|
| notes naming a target level | 11 |
| reached **before the engine's stop** | **0 of 11** |
| reached by the session close (ignoring the stop) | 1 of 11 |
| distance from the entry, in the engine's R | 2.3–22 R (PDH 2.3–5.7 R; PWL/PWH 5–22 R) |

Reading: the levels Sharif names are sensible higher-timeframe draws. The engine's stops are 1m-structure stops,
though, so a daily or weekly draw sits 2–22 R away and the stop is hit first almost every time. This is a
**timeframe mismatch between stop and target**, not evidence that the levels are wrong. The liquidity-reach study
(`liquidity-reach-2026-11-14.md`) says the same thing more broadly: levels are reached at random-walk rates ≈ 1/(1+d).
So a far target only pays when the stop belongs to the same timeframe as the draw.

Next (option 4 on the list, not yet pre-registered): PDH/PDL/PWH/PWL targets paired with a stop on the matching
timeframe (e.g. beyond the 15m/1h swing), judged on expectancy per trade with the same 70/30 hold-out.
