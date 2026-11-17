# Breakers hidden by a minor swing: `merge` option (2026-11-16)

**Source.** Sharif's two 1h breakers on US100, saved from the live sheet (`reports/reviews/live.jsonl`):
- 28,130.31–28,191.61, the entry area of his gap trade (buy, Thu 12 Nov 10:03 at 28,153.8);
- 28,178.65–28,246.68, the alternative entry of his BOS trade (sell, Fri 13 Nov).

**What the engine did.** `breaker_blocks` found neither. It reads swings three at a time in strict low / high / low order. On 12 Nov the swings were low (00:00) / high (04:00, 28,209) / high (07:00, 28,205) / low (08:00, 27,912): the minor lower high at 07:00 broke the order, so the breaker was never formed. Friday is the mirror case.

**Change.** `breaker_blocks(..., merge=True)` also reads the swings with same-kind neighbours collapsed to the most extreme one. **Off by default**: no model or map result changes. With it on, both of his breakers are found and known only after the breaking candle closes (12 Nov 10:00; 13 Nov 10:00). US500 12 Nov was already found without it. On US100 1h, 2–16 Nov 2026, the count of breakers + mitigation blocks goes from 24 to 38.

**Still different from his reading.** He marks the **body of the last candle** before the leg (12 Nov 04:00 body 28,129.8–28,191.9; his mark 28,130.3–28,191.6). The engine's block is the whole run of same-colour candles with wicks (28,038.7–28,209.2), about three times as wide. Sharif confirmed "body of the last candle" → option `block="body"` (off by default, because the frozen forward recipe uses the default block): US100 gives 28,129.8–28,191.9 and 28,171.1–28,242.9 against his 28,130.3–28,191.6 and 28,178.7–28,246.7.

**Not tested.** Whether a breaker entry pays. Two examples are not evidence; turning `merge` on in `pd_return` or the liquidity map needs an in-sample run and a 30-trade review first.

Tests: `tests/test_events.py::test_merge_finds_the_breaker_behind_a_minor_lower_high` (hidden without merge, found with it, nothing known early, merge only adds).
