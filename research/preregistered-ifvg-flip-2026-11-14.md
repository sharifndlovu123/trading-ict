# Pre-registered: the flip after a failed trade (written 2026-11-14, before any code or run)

Sharif (2026-11-14): "there's nothing wrong with being incorrect … it shows a fail turned into a win … you might
think you're right, but if you can see a possible flip side, it can play out … the IFVG was respected." Review log
#2 (IFVG flip, ICT rulings §10). The exit-only version (`invalidate_tf`: leave when the entry FVG fails) was tested
2026-11-13 and hurt; this tests the **other half**: take the opposite trade from the failure.

## Rule
For every trade a model takes (2022_model, mmxm, silver_bullet, cameron, pd_return) that is **stopped out**:
1. **Failure:** the trade's entry FVG (on the model's entry timeframe) has a candle of that timeframe close beyond
   its far edge, at or before the stop-out. It is now an IFVG of the opposite polarity, known at that close.
2. **Retest:** within 90 minutes of the inversion and inside the same session (not after 16:00), price trades back
   to the IFVG's near edge.
3. **Flip trade:** opposite side to the failed trade. Limit entry at the IFVG near edge; stop beyond the IFVG far
   edge, or beyond the failed trade's extreme if that is closer to entry than 0.5× the IFVG height (whichever puts
   the stop further away); TP1 = nearest untaken liquidity ≥ 1R (`_targets`), runner as the model's defaults. The
   daily bias is **not** applied (the flip is a counter-read by definition). One flip per failed trade; no flip of a
   flip.
4. Costs as the model (both bases).

## Test and decision rule
2022-01-03→2024-06-28, the variants tool's in-sample/out-of-sample split, assets US100 US500 US30 XAUUSD XAGUSD,
both cost bases. Pass (per model, per basis) needs both:
- the flip trades' out-of-sample expectancy > 0 R with z ≥ 2.3 (5 models), and
- model + flips beats the model alone in out-of-sample R per day (the flip must add, not just exist).
Also reported, not tested: how often a stopped trade produces a flip, and the flip's vote rate. A pass makes
"model + flip" a forward-v2 candidate. 2024-07+ unused. Sharif's Apr 2024 and Oct 2026 examples inspired it and are
not used to score it.

## Amendment 1 (2026-11-14, before the full run): the flip's stop
A feasibility check on US100 2023-03/04 (in-sample; filter counts only, no performance read) showed that almost
every stopped trade's entry FVG does close through on its own TF, but with the stop at the IFVG's far edge the
risk is only the 1m/5m gap's height: round-trip cost is a median 26–55% of 1R, so the models' cost gate
(≤ 0.1R) blocks ~85% of flips. (As written, the "failed trade's extreme" clause could never move the stop past the
far edge, so the far edge was the stop.) Sharif chose (2026-11-14): **stop beyond the failed move**: for a
failed long, the flip short's stop is the highest high between the long's fill and the inversion close (mirror for a
failed short). Both stop rules are run and reported:

| rule | flip stop |
|---|---|
| far edge (as first written) | the IFVG's far edge |
| failed extreme (Sharif) | beyond the failed trade's extreme from fill to inversion |

10 model × rule cells now, so the pass bar is raised to **z ≥ 2.6** (and model + flips must beat the model alone in
OOS R per day). Everything else unchanged.
