# Results: premium/discount of the range in play, and a deeper entry on the leg (2026-11-15)

Pre-registration: `preregistered-range-in-play-2026-11-14.md` (written before code). Build `f288984`. Futures basis;
US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, 70/30 split (OOS from 2023-09-29); measure = expectancy with
the runner (`runner_r`). Pass = OOS Δ vs the model's baseline with z ≥ 2.4 and ≥ 30 OOS trades. Log:
`reports/sweep-range-2026-11-14.log`.

**0 of 6 cells pass.** Best: 2022 model leg OTE 70.5%, +0.40 R, z +1.1.

| model | variant | IS n | IS exp R | OOS n | OOS win | OOS exp R | Δ vs base | z |
|---|---|---|---|---|---|---|---|---|
| 2022 model | baseline | 953 | −0.023 | 304 | 36% | +0.023 | – | – |
| 2022 model | range: entry in the cheap half | 576 | +0.003 | 180 | 35% | −0.015 | −0.038 | −0.2 |
| 2022 model | range: limit at the 50% | 627 | +0.015 | 194 | 36% | +0.020 | −0.003 | −0.0 |
| 2022 model | leg: limit at OTE 70.5% | 292 | +0.192 | 84 | 30% | +0.419 | +0.395 | +1.1 |
| MMxM | baseline | 649 | −0.060 | 237 | 29% | −0.077 | – | – |
| MMxM | range: entry in the cheap half | 499 | −0.036 | 177 | 29% | −0.020 | +0.057 | +0.4 |
| MMxM | range: limit at the 50% | 530 | −0.046 | 188 | 29% | −0.027 | +0.050 | +0.4 |
| MMxM | leg: limit at OTE 70.5% | 326 | +0.006 | 88 | 14% | −0.016 | +0.061 | +0.3 |

## Reading
- **Range-in-play cheap half (gate or 50% limit)**: about 0 on both models. The larger range price sits in does not, on
  its own, separate trades.
- **2022 model leg OTE** is the only rule positive on *both* halves (IS +0.19 R vs −0.02; OOS +0.42 R vs +0.02), but it
  fills under a third of the trades (84 of 304) and the spread is wide (± 0.33 R). Not a pass; the strongest lead so far.
- **MMxM leg OTE** does not help (win rate 14%: the fixed price TP1 stays, but deep fills are mostly the losing pullbacks).
- **Curve stage (review log #20–21)**: the promised early/late split does not apply cleanly — MMxM's default entry is by
  construction the first leg off the reversal point (early stage), and the 2022 model has no curve. So the early-stage
  case was tested (MMxM: OTE no help) and the late-stage case (shallow entries in later consolidations) was not. A
  stage-conditional rule needs its own definition and pre-registration.
- Sharif 2026-11-15: cheap-half entries are safe only in certain situations; liquidity at the key time may be taken *or*
  added; time matters more than zones. The unconditional rules here ignore all three.
