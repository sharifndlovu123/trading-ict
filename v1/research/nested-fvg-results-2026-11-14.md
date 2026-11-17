# Results: nested FVG entries, no trades inside a daily FVG, TP1 at the 4h range's 50% (2026-11-14)

Pre-registration: `preregistered-nested-fvg-2026-11-14.md` (written before any code or run). Futures basis; US100 US500
US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, 70/30 split (OOS from 2023-09-29); measure = expectancy with the runner
(`runner_r`). Pass = OOS Δ vs the model's baseline with z ≥ 2.4 and ≥ 30 OOS trades. Log:
`reports/sweep-nested-fvg-2026-11-14.log`.

**0 of 6 cells pass.** Best: 2022 model "50% of the 4h range" +0.19 R, z +1.2.

| model | variant | OOS n | OOS win | OOS exp R | Δ vs base | z |
|---|---|---|---|---|---|---|
| 2022 model | baseline | 304 | 36% | +0.023 | – | – |
| 2022 model | loc: entry FVG inside a 4h FVG | 102 | 37% | +0.023 | +0.000 | +0.0 |
| 2022 model | loc: not inside a daily FVG | 272 | 36% | +0.075 | +0.052 | +0.4 |
| 2022 model | targets: 50% of the 4h range, runner to the HTF draw | 356 | 28% | +0.214 | +0.191 | +1.2 |
| MMxM | baseline | 237 | 29% | −0.077 | – | – |
| MMxM | loc: entry FVG inside a 4h FVG | 51 | 29% | −0.172 | −0.094 | −0.5 |
| MMxM | loc: not inside a daily FVG | 204 | 30% | −0.065 | +0.012 | +0.1 |
| MMxM | targets: 50% of the 4h range, runner to the HTF draw | 238 | 27% | −0.053 | +0.025 | +0.2 |

## Reading
- **Nested 4h FVG** keeps a third (2022 model) / a sixth (MMxM) of trades with no better result out-of-sample. The
  2022 model's in-sample +0.10 R (vs −0.02) did not hold — the classic in-sample mirage.
- **Not inside a daily FVG** drops ~12% of trades; the rest are about the same.
- **50% target** is the only direction worth a second look (2022 model +0.19 R, win rate 36% → 28% because the
  first target is further). Not significant.
- **The range was the wrong one.** The test used the newest confirmed 4h swing high/low. Sharif (2026-11-14, sample 1,
  review log #19): premium/discount is relative to **the current trading range price is inside** — the leg being
  retraced, or the HTF FVG itself — and ICT's dealing range must have taken liquidity on both sides (ruling §17). A
  retest with the right range is a new pre-registration, not a re-run of this one.
