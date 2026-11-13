# Direction diagnosis (2026-11-13, commit 0f2bfad runs, measured spreads)

Question: 39% of unseen-period losses were labelled "bias wrong" and 31% "wrong side". Is direction the lever?
Data: tests 1–4 use **2022-01-03 → 2024-06-28 only** (3,146 traded setups, 5 assets, 4 models). The gross/net
split also shows the unseen period, which was already burned (see `preregistered-selection-2.md`).
Scratch scripts: `direction_diag.py`, `stophunt_diag.py` (session scratchpad; results summarised here).

## Findings
1. **The daily bias call is good.** `prev_day_dol` calls the day's first previous-day level correctly 62–67% of
   the time (US100 67%, US500 66%, US30 66%, gold 63%, silver 62%), against 51–55% for always-bull: an edge of
   12–17 points, on every asset (`eval.bias --split`).
2. **Trades already follow it.** 85% of trades are on the bias side. Aligned trades average ≈ 0R
   (−0.01 / −0.02R), whether or not the bias target (PDH or PDL) was already taken at decision time. Per-model
   splits flip sign, which looks like noise. Weak exception: both PDH and PDL already taken → −0.19R
   (n 153, z_cl −1.6).
3. **Direction carries real information.** Taking the opposite side of every trade would be far worse:
   −0.89R (2022 model), −0.39R (Cameron), −0.19R (MMxM), −0.12R (SB). That is the `cf_flip` counterfactual.
4. **No stop-hunt signature.** After a stop-out, price later reaches entry + 2R in 42% of 2022-model and
   Cameron losses. But measured symmetrically (3R legs from the stop, which one comes first), our way vs against
   is a coin flip: 36/37%, 37/36%, 26/24%, 29/29%. So re-entering after a stop has no edge, and neither does a
   1.5× wider stop (`cf_wide_stop`: −0.03 to +0.00R).
5. **The edge, if any, is smaller than the cost.** Average spread ≈ 0.06–0.07R per trade.

   | Model | Gross 2022–24 | Gross unseen |
   |---|---|---|
   | 2022 model | +0.10R | +0.01R |
   | Cameron | +0.07R | −0.04R |
   | Silver Bullet | +0.02R | −0.08R |
   | MMxM | −0.01R | +0.00R |

   No model's gross edge held into the unseen period.

## Reading
- Direction is **not** the main lever: the bias is right two days in three, trades follow it, and flipping
  destroys value.
- The "bias wrong" and "wrong side" loss labels describe how a trade ended, not a cause we can fix.
- The entries have about zero gross edge out of sample, and a spread of about 0.065R/trade turns that negative.
- The planned **IFVG flip** (ruling §10) is deprioritised. A failed FVG mostly coincides with a stop-out, and
  after a stop-out direction is a coin flip (finding 4), so flipping at that point has no expected edge before
  costs.

## What would move it
- **Fidelity:** check the coded entries against ICT's own executions (`tests/cases/ict_live_exec.yaml`,
  day packs) before more statistics. A rule that isn't ICT's rule can't be judged as ICT's.
- **Cost in R:** larger structures (wider risk) shrink the spread's share. Only 2022–24 data can be used to
  pick them.
- **Forward test:** freeze the rules and log every setup from 2026-11-13 on. It is the only clean test left.
