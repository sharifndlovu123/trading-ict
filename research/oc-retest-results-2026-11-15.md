# Results: MMxM entry at the retest of the broken original consolidation (run 2026-11-15)

Pre-registration: `preregistered-oc-retest-2026-11-15.md` (21a7929); build 753e7e6. Futures basis; US100 US500 US30
XAUUSD XAGUSD, 2022-01-03 → 2024-06-28; OOS from 2023-09-29. Runner R (50% at TP1). Log: `reports/sweep-oc-retest-2026-11-15.log`.

| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline (FVG at the turn) | 649 | 27% | −0.060 | 237 | 29% [24–35%] | −0.077 ± 0.086 | – | – |
| entry: retest of the broken OC | 300 | 33% | +0.027 | 104 | 32% [24–41%] | −0.110 ± 0.130 | −0.033 | −0.2 |

**Verdict: fail (z −0.2).** The retest entry trades less than half as often. It was slightly positive in-sample
(+0.03 R) but negative out-of-sample (−0.11 R), with no difference from the turn entry.

Reading: mechanically, "wait for the break, then buy the retest of the consolidation" does not beat buying the turn.
Sharif's BTC example (#28) also had what this rule cannot see: a second HTF zone, the first long failing to push
("failed to push directly quick"), and an IFVG inside the consolidation. The retest on its own is not the edge. Whether
it works **as a second trade after a failed turn entry** (his actual sequence) would need its own pre-registration. That
is listed, not tested.
