# Pre-registered: power of 3, sell above the opening price, buy below it (daily and weekly)

Written 2026-11-14, before any code or run. Source: Sharif ("higher time play… can formulate what we could expect
for the week, it links to the power of 3"); references/PO3 - Fractal Study.pdf; models.md §4 (PO3 day).
Inspiring example (not scored): NQ week of 2024-04-15: open 18151 (Sun 18:00); Monday 09:16 high 18350.75
(+200, the week's high, inside the daily IFVG + OB 50%); then −1237 to Friday's low; closed −972.

## Rule
PO3: in a bearish period price first runs **above** its opening price (manipulation) and then distributes lower;
mirror for bullish. So a short is taken only while price is **above** the period's opening price, a long only
**below** it.
- Daily open: 00:00 NY (midnight open, already in the day context as `midnight_open`).
- Weekly open: the first trade of the week (Sunday 18:00 NY).

## Variants (applied to each model at its defaults: 2022_model, cameron, mmxm, silver_bullet, pd_return)
| name | gate |
|---|---|
| PO3 daily open | entry above the midnight open for shorts / below for longs |
| PO3 weekly open | same with the weekly open |
| PO3 daily + weekly | both |

## Test and decision rule
2022-01-03→2024-06-28, the standard in-sample/out-of-sample split, assets US100 US500 US30 XAUUSD XAGUSD, both cost
bases. 3 variants × 5 models = 15 comparisons per basis: a variant counts only if its out-of-sample exp R beats that
model's baseline with z ≥ 2.6 (Bonferroni for 15, one-sided 5 %). Report all. Winners are forward-v2 candidates.
2024-07+ unused.

## Later (needs the IFVG/OB work first)
A weekly narrative: which side of the week the HTF arrays and liquidity point to (e.g. a respected daily IFVG above
and an equal-lows pool below = bearish week), gating trades by it rather than by the daily bias alone.
