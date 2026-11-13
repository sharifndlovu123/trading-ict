# Pre-registered selection #2: model × asset × window, measured costs (semi-blind)

Written 2026-11-13, before the selection query was run.

## Disclosure (why this is "semi-blind", not blind)
The 2024-07 → 2026-11 test period has been looked at more than once:
- Selection #1 used it.
- Earlier on 2026-11-13, at commit 0f2bfad, I printed which family × asset × window buckets were > 0 in **both**
  periods (2022 model US100 NY AM/PM, Cameron US30 NY PM, MMxM US30 London, MMxM US500 NY PM).

The rule below does not name any bucket. It is selection #1's rule adapted mechanically. But the choice to add
the asset dimension was made after seeing that table, so a pass here is **weaker evidence than a blind test**.
The only clean confirmation left is forward data: days after 2026-11-12, live or paper.

## Rule
- **Selection data:** store runs at commit **0f2bfad** (measured spreads; current defaults), day ≤ 2024-06-28
  (2022-01-03 → 2024-06-28). Traded setups only.
- **Buckets:** model family × asset × time window. Assets are separate because measured costs now differ by
  asset and by session.
- **Keep a bucket if all of these hold:**
  - n ≥ 40 traded (lower than #1's 60 because the buckets are about 5× smaller);
  - exp R > 0;
  - both halves by date (early/late) > 0;
  - **z_cl ≥ 1.0**, where z_cl is the z-score using the se clustered by day (new in `store.leaderboard`).
- **Test:** trade only the kept buckets on 2024-07-01 → 2026-11-12 (same commit and defaults).
  - Report pooled exp R ± se_cl, and per-bucket results.
  - **Pass** = pooled exp R > 0. **Edge** = pooled z_cl ≥ 2.
- **Comparison:** all buckets, unselected, on the same test period.
- One shot: whatever the result, the rule is not changed and re-run on this test period.
- If nothing passes the filter, that is the result ("no bucket qualifies").

## Result (run 2026-11-13, commit 5f33441 rule on 0f2bfad runs): FAIL

- 26 buckets had n ≥ 40 in 2022–24. **3 kept:**
  - Silver Bullet US30 sb_pm: +0.36R, n 72, z_cl 1.6
  - 2022 model US100 NY AM: +0.28R, n 92, z_cl 1.9
  - Cameron US30 NY AM: +0.16R, n 185, z_cl 1.3
- **Test (2024-07 → 2026-11), kept pooled: −0.115 ± 0.080R (n 341, z_cl −1.4).** Unselected, all buckets:
  −0.098 ± 0.022R (n 4683, z_cl −4.4). The selection did slightly worse than no selection.
- Per bucket on test: 2022 model US100 NY AM +0.02 (n 106); Cameron US30 NY AM −0.17 (n 182);
  SB US30 sb_pm −0.20 (n 53).
- Reading: the second failure in a row. Even with measured costs, asset-level buckets and clustered z, past
  bucket performance did not predict the next period. 2022 model US100 NY AM is the only bucket picked by both
  selections that stayed ≥ 0 out of sample, but at +0.02R it is not an edge. Choosing *when* to trade these
  entries does not fix them. The lever is the entries themselves: direction (39% of losses had the wrong bias)
  and the setup logic.
