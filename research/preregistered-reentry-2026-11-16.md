# Pre-registered: re-entry after a stop-out, same side, same window (written 2026-11-16, before any code or run)

Models: the 2022 model and MMxM. Sources:
- Review log #3 (2026-11-14, MMxM / SB Sep 16–17 2024): "re-entry after a sweep stop-out inside the window" — open since.
- Trade-handling review (2026-11-16, 24 in-sample trades that moved ≥ 2R our way): on 6 of 14 cut trades Sharif calls
  the call right and the stop "just a loss" / "a sweep took us out"; on 3 he points to the second entry: US100
  2023-01-05 ("after the knock out we would have had another chance to enter … via the 07:45 FVG"), US30 2023-09-27
  ("a second entry could have been done"), US500 2022-03-08 ("kicked out … but it ended up reaching our goal").
- Memory (trade principles): "stopped by a sweep inside the window → valid re-entry in the same direction if the setup
  re-forms."

## Rule (in `sim.run.run_day`; bars at or before each decision only)
The cap stays one trade per window (`max_trades=1`, scope = the window). Param `reentry`:
- `after_stop`: **one extra** trade in that window is allowed when the window's previous **filled** trade exited at
  its **stop** (`exit_reason == "stop"`) and the new setup is on the **same side**, decided after that exit. The new
  setup must re-form on its own (the model's normal gates; nothing is reused from the first trade).
- `any` (control): one extra trade in the window after any filled trade, either side, any exit. It tells whether the
  stop-out condition matters or only the extra trade does.
Everything else (entry, stop, TP1, partials, runner, flat by 16:55, news, costs) is the model's default.

## Variants
| name | reentry |
|---|---|
| re-entry: after a stop, same side | after_stop |
| control: any second trade | any |
2 variants × 2 models = 4 cells.

## Test and decision rule
Futures basis. US100 US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, the variants tool's 70/30 split (OOS from
2023-09-29). Metric: runner R (`runner_r`). The added trades are tagged (`reentry` column) so they can be scored on their
own: they are the only trades that differ from the baseline.
**Pass (per model) = the `after_stop` added trades' OOS mean runner R > 0 with z = mean / se ≥ 2.4 and ≥ 30 OOS added
trades, and their OOS mean ≥ the `any` control's added trades.** The variant's whole-book OOS Δ vs baseline is reported
beside it. Every cell is reported. A pass becomes a forward-v2 candidate; 2024-07+ stays unseen.
