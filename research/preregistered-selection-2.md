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

## Result
(to be filled in by the run, unedited)
