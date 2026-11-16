# 30 late-fill trades reviewed (15 winners, 15 losers)

The trades the `cancel_run_r = 1` option would have dropped on 2022–24 (`research/decisions/2026-11-16-cancel-run.md`). Two reviewers, 15 each. Leads, not evidence.

## What they found
- **No look-ahead** in the bars checked.
- **Late-fill class:** ordinary retrace 21 (10 W / 11 L); stale, move already done 8 (4 W / 4 L); structure broke 0; other 1 (1 W). No class separates winners from losers.
- **"1 R" is noise-sized:** stops of 0.026–0.10 ADR on most trades; median unfilled run about 0.07 ADR for winners and losers alike. In 12 of 15 (batch 1) the decision bar already closed about 1 R from the limit: the option measures how deep the limit sits, not a move that left.
- **Other cancel rules tried on paper** (run ≥ 0.1–0.15 ADR, a time limit, a nearer pool taken, ≥ 80% of the way to TP1, an opposing shift): each cuts winners about as often as losers. A time limit hurts (it drops pre-open orders that the 09:30 fake-out fills and wins).
- **Post-hoc lead (3 of 3 lost):** the unfilled run was rejected at the edge of an opposing 1d / 4h / 1w array.
- **The losses are a stop problem:** 13 of 15 losers were stopped and then TP1 traded; stops sit a fraction of a point beyond the nearest pool.

## Flags
Trigger gaps under one tick (0.05–0.69 points) on six trades; fills, stops and TP1 decided by 0.1–1 point on five; one fill counted in two models (2023-04-19); a decision on the ISM release candle.

## Outcome
The option stays off, and no other cancel rule is proposed.
