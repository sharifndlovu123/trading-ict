# Pre-registered: MMxM entry at the retest of the broken original consolidation (written 2026-11-15, before any code or run)

Model: MMxM only (the original consolidation exists only there). Source: Sharif, review log #28 (BTC 1m Dec 4 2023, an
outside-sample illustration). The first long at the turn closed at breakeven ("failed to push directly quick"). After
the displacement broke back above the original consolidation, "take note of the retest of the consolidation": the
broken consolidation, now support, was the "low-risk entry zone", and price ran from there to buyside. Linked: #20 (the
cycle doesn't always reach the original consolidation; bias decides). Blind triage "entry too early" ×16 (#18).

## Rule — entry mode `oc_retest` (buy model; the sell model is the mirror)
Everything upstream is unchanged: the original consolidation (OC), the sell-side curve, the reversal low at an HTF array
that purges liquidity, and the MSS. Then (1m bars, no bar after the decision):
1. **Break:** the first 1m close above the OC high after the MSS.
2. **Proof:** after the break, price reaches OC high + R, where R = OC high − (OC low − stop buffer). The **decision** is
   the close of the bar that first reaches it, and must happen before 16:00.
3. **Plan, frozen at the decision:** a limit buy at the **OC high**; stop at OC low − stop buffer (the retest has failed
   if price comes back through the whole consolidation); TP1 = entry + 2 R (the 2022 model's validated TP1 cap);
   final = the nearest context buyside level (Asia high, PDH, PWH) beyond TP1 that is untaken at the decision, else
   TP1. Same 50% partial at TP1 and runner rule as the baseline.
4. The order lives until 16:00 that day (Sharif's retest filled about 2 h after the break, in the lunch hour). The time
   gate applies to the decision.

Gates: time, bias, POI + purge (unchanged), target (TP1 ≥ 1 R by construction), cost (`max_cost_r` on the new
risk). The **pricing gate is not applied** in this mode. The baseline judges the entry against the curve
equilibrium, but the OC high is the top of the curve, so every retest would fail it. Sharif's ruling (§17): an entry in
the expensive half is not invalid. The window cap and the no-overlap rule apply as usual.

## Test and decision rule
One cell: variant **"entry: retest of the broken OC"** = MMxM defaults with `entry="oc_retest"`. Futures basis; US100
US500 US30 XAUUSD XAGUSD, 2022-01-03 → 2024-06-28, the variants tool's 70/30 split (OOS from 2023-09-29). Measure:
expectancy with the runner (`runner_r`), with vote rate and fills beside it. **Pass = OOS Δ vs the MMxM baseline with
z ≥ 2.4 and ≥ 30 OOS trades.** A pass becomes a forward-v2 candidate. Only then would "FVG entry, then a second trade on
the OC retest" be tested, as its own pre-registration.
