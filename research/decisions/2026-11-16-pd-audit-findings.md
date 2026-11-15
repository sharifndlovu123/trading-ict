# PD-array audit findings (2026-11-16) through the change gate
Source: pd-array-audit, `research/pd-audit/2026-11-16.md` (105 zones Sharif drew, 50 review moments)

## 1. Zero-width volume imbalances on the map — **bug fix, done**
- Evidence: the audit's definition check flagged 5 map areas (1h/4h VIs) with top == bottom after rounding, e.g. US500 2022-05-28 00:30, 2022-09-29 04:14. A sliver like this could take one of the 3 gap slots per side.
- Witnesses: pd-array-audit flags it; the code contradicts its own intent (`TOPDOWN.min_area_adr`: slivers aren't areas); pattern-finder and trade-review are silent (no trait depends on it).
- Change: `ict_engine/concepts/liquidity_map.py` gap loop skips gaps < 0.01 wide (rounded edges equal). Test first: `tests/test_liquidity_map.py::test_no_zero_width_areas_on_real_data` (failed before, passes after). Suite: 498 passed.
- Effect: the cached plan reads (`reports/cache/pins-*.pkl`) were built before the fix. The change only removes slivers, so the effect should be tiny; it gets picked up at the next `plan_build.py --all`.

## 2. Arrays he uses never reach the map (28 of 98 found) — **measure first**
- Evidence: 9 on 15m/5m (the map has no TF below 1h, by design) and 19 on 1h–1w dropped by `PER_SIDE["gap"]` = 3 nearest per side, `max_adr`/`REACH` and lifecycle filters.
- Witnesses: pd-array-audit says it's a usage gap. Pattern-finder can't judge it yet (no trait for "array off the map"). Fable FF / sweep: the plan's TP1 is too far and its arrays too coarse (4H-range plans lose), which is consistent with arrays missing near price. No disagreement, but no outcome evidence either.
- Next: add a trait `array_on_map` (or the rank of the picked array) to the plan sim and run pattern-finder; separately measure a variant map with `PER_SIDE["gap"]` 3 → 5 and 15m arrays for entries only. Becomes an option only if that separates wins.

## 3. Breakers read as order blocks (2 of 4) — **needs Sharif / ictindex**
- Evidence: on re-mmxm-US500-20230215 (4h) and re-2022_model-US100-20230828 (15m), the engine finds an OB at his breaker. Its breaker needs swing low → swing high → a lower low that takes the first low → a close above the high (Bible pp.19–26); there, the sequence isn't complete on that TF.
- Decision: no code change on n = 4. Ask Sharif which sequence he saw, and check ictindex if the definitions differ.
