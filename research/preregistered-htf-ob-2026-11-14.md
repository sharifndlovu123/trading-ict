# Pre-registered: higher-timeframe order blocks as the POI (PD array return)

Written 2026-11-14, before any run. Source: Sharif's trade-review correction (daily NQ OB, Apr 11–15 2024) and
ICT's words (references/personal/ictindex-rulings.md §11). The April 2024 example inspired the rule; it is not
used to score it (selection data ends 2024-06-28 and the rule is scored on all assets, not that week).

## Variants (pd_return; everything else at defaults)
| name | HTF timeframes | arrays | OB confirmed by | OB measured on |
|---|---|---|---|---|
| HTF OB 4h+1d (open, body) | 4h, 1d | ob | close through open | body |
| HTF OB 4h+1d (extreme, body) | 4h, 1d | ob | close beyond extreme | body |
| HTF OB 4h+1d (open, body, lookback 10) | 4h, 1d | ob | close through open | body |
| HTF FVG + OB 15m–1d (open, body) | 15m, 1h, 4h, 1d | fvg, ob | close through open | body |
| HTF daily FVGs added | 15m, 1h, 4h, 1d | fvg | — | — |

## Test
- `uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model pd_return --only HTF
  --assets US100 US500 US30 XAUUSD XAGUSD [--cost futures]`, the standard in-sample / out-of-sample split inside
  2022-01→2024-06.
- **Both cost bases.** A variant counts only if its out-of-sample exp R beats the baseline's on that basis with
  z ≥ 2.0 (5 variants; the same bar used for every earlier variant sweep). Report every variant, winners and losers.
- A winner is a **candidate** for `forward-v2` (its own forward clock), not a new default by itself.
- 2024-07+ is burned for price-only results and is not used.
