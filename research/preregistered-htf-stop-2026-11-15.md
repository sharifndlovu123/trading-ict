# Pre-registered: a stop on the timeframe of the draw — wider structural stop + daily/weekly target (written 2026-11-15, before any code or run)

Models: the 2022 model and MMxM. Sources:
- `named-targets-triage-2026-11-15.md` (in-sample): none of Sharif's 11 named targets (PDH, PWL, PWH) was reached
  before the engine's stop, which was 1m structure 2.3–22 R away; 1 was reached by the close. That points to a
  stop/target timeframe mismatch.
- `liquidity-targets-results-2026-11-14.md`: aiming the runner at the HTF draw *with the 1m stop* changed nothing
  (0 of 8). This test changes the stop.
- Sharif's practice (memory: partials): close a portion at TP1, run the rest to the big target.

## Rule (bars at or before the decision only), applied to the frozen plan in `sim.run.run_day`
For a long (the short is the mirror):
1. **Structural stop:** take the newest confirmed swing low of the stop timeframe (15m or 1h; last 10 days, confirmed
   by the decision) that lies **below** the model's stop. New stop = that low − the model's stop buffer. If there is
   none, the trade is unchanged.
2. **Draw:** final = the nearest of PDH, PWH (long) / PDL, PWL (short) beyond TP1 that is untaken from the day start
   (00:00) to the decision. Otherwise the model's own final stays.
3. **TP1 keeps its price**; it is now fewer R. Entry and order expiry are unchanged, and so are the 50% partial at TP1,
   the runner stop and the flat-by-16:55 exit. The cost gate (`max_cost_r`) is checked on the new risk.

## Variants (everything else at the model's defaults)
| name | stop timeframe |
|---|---|
| stop: 15m swing + daily draw | 15m |
| stop: 1h swing + daily draw | 1h |

2 variants × 2 models = 4 cells.

## Test and decision rule
Futures basis only. US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, the variants tool's 70/30 split (OOS
from 2023-09-29). Measure: expectancy in R of the **new** risk, with the runner (`runner_r`); R per unit risked is
the fair comparison when stop sizes differ. Vote rate is reported beside it. **Pass = OOS Δ vs that model's baseline
with z ≥ 2.4 and ≥ 30 OOS trades.** Every cell is reported. A pass becomes a forward-v2 candidate.
