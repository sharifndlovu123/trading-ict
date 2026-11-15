# Results: two-sided liquidity → follow the side price shows (2026-11-16)

Pre-registration: `preregistered-gravitation-2026-11-16.md` (3da4be1). Script: `research/scripts/gravitation_test.py`
→ `reports/gravitation-calls.parquet`. US100 US500 US30 XAUUSD, 2022-01-03 → 2024-06-28, 08:30 NY.

**Fail.** The signal (first 15m displacement 08:30–12:00 closing beyond the range since 00:00) picks the pool that
trades first 77–79% of the time — exactly what distance alone predicts once price has moved toward that pool.

| | calls | hits | expected by distance | edge | z |
|---|---|---|---|---|---|
| in-sample (→ 2023-09-28) | 900 | 708 (79%) | 701.8 (78%) | +6.2 | 0.56 |
| **OOS (2023-09-29 →)** | **401** | **310 (77%)** | **316.9 (79%)** | **−6.9** | **−0.99** |

- Days: 2,572; two-sided (both top-down pools within 1.5 ADR) 1,891 (74%); a signal by 12:00 on 1,335; 34 with neither /
  both pools in the same minute.
- When the signalled pool was the **farther** one at the signal close: hit 40% IS (88 calls), 29% OOS (45) — below a
  coin; the displacement does not out-pull distance.
- 321 of 1,301 calls had the signal candle itself take the pool (p = 1). Without them: IS 497 vs 490.8 (z 0.56), OOS
  200 vs 206.9 (z −0.99) — same answer.
- Per asset: z between −0.32 and +0.39; none stands out.

## Reading
A 15m displacement through the overnight range is not the "something" Sharif waits for, or it carries no information
beyond where price already is. Two-sided liquidity is the normal case (74% of days), so the waiting rule needs a
sharper trigger. Next: his own words for what shows the side (top-down review, 1H step), then a new pre-registration.
