# US30 short — Fri 15 Nov 2024 10:19 NY · engine +0.42 R (time exit 16:00) · sheet +0.35 R · day-only +0.35 R
Engine pd_return trade, confirmation run of `recipe4b` on 2024-07 → 2026-11 (FAILED; `research/preregistered-recipe4b-2024H2-2026.md`). Facts: `research/trade-reviews/sheets/2026-11-16-recipe4b-confirm/2024-11-15-1019-US30-short-pd_return.md`; row in `reports/recipe4b-confirm-US30.parquet`. Entry 43521.46 · stop 43704.65 · TP1 41638.14 (previous week low, 10.28 R = 3.93 ADR) · risk 0.38 ADR · ADR 479.52. Decided 10:14, filled 10:19.

## Checklist
| # | Step | Grade | Evidence (1–8 known at the entry; 9–10 use the outcome) |
|---|---|---|---|
| 1 | Time and activity | pass | ny_am_kz, sb_am; last hour normal (1.15×), net 0.13 ADR; retail sales 109 min earlier |
| 2 | Bias / narrative | fail | weekly, daily, 4H bull; only the 1H bear (since 12 Nov); read side bull; inside a 1d bullish FVG 42273.64–43637.24 |
| 3 | Dealing range | pass | 0.66 of the 4h range 41638.14–44493.32: premium, in the OTE |
| 4 | POI / array | fail | "1h FVG 43631.95–43632.94" is 1 pt wide (0.002 ADR), formed 00:00–02:00; price wicked 24 pts past its far edge at 07:56–08:30. Not an area |
| 5 | Liquidity before | fail | none in the 6 h before (sheet) |
| 6 | Trigger | pass | 09:45 candle body 0.119 ADR (5.6×), gap 29.5 pts (0.061 ADR): a real push down after the open |
| 7 | Stop | pass | 0.10 ADR above the 08:30 high 43656.70 = 43704.65: above two 1h swing highs, the Asia high 43678.20 and a 1h bearish FVG |
| 8 | Targets | fail | TP1 = PWL 41638.14: 10.3 R, 3.9 ADR; the 4h bullish FVG 42977.70–43365.11 starts 0.33 ADR under the entry |
| 9 | Management | pass | flat at 16:00, +0.42 R; MFE +0.97 R at 12:53, nothing banked |
| 10 | Attribution | partial | no area, impossible target; the 15m push was real + small win = partly luck |

## Market conditions
Known before the day: **consolidating**, backdrop **bull**, volatility **normal** (1.15× its 1-year median), 20-day efficiency 0.08, a scheduled high-impact US release that day. Retail sales day, vol 1.15×, consolidating, bull. A modest down day: RTH range 0.62 ADR, net −0.28 ADR; low 43343.70 at 12:53 inside the 4h bullish FVG, then sideways. A drift day; the release moved little. Day type: **quiet/grind** (the day's range and direction are hindsight).

## Does this look like Sharif's recipe?
- **Area:** no: one point wide and already traded through.
- **15m momentum:** yes.
- **Early or late:** entry 0.23 ADR under the "area".
- **Target:** nothing he would set: 3.9 ADR away on a day trade.
- **What he would most likely say:** "there's no area here; the momentum is fine but where is the first swing to take partials?" (my reading, not his words).
- **Verdict:** not.

## Why it won
**Right side on a mild down-drift, paid by the clock.** The 15m push after the open was real and the retrace entry turned inside the 15m gap. With TP1 3.9 ADR away the result is whatever 16:00 gave: +0.42 R of a +0.97 R best.

## Price we should have looked at
43545.00 at 11:18: 0.049 ADR against the entry, 0.333 ADR inside the stop, inside the 15m trigger gap (43521.46–43550.93). Known at the entry.

## Realism
- Area formed 00:00–02:00, 50% reached 07:56 with four 1m bars up to 23.8 pts past the far edge (no 1m close beyond): a 1-pt "gap" that "fresh" still accepts. Reaction high 43656.70 at 08:30; stop matches.
- 15m gap candles 09:30 / 09:45 / 10:00, complete at 10:14 = decided_at; gap 29.46 pts re-derived. No look-ahead.
- Fill bar 6.7 pts through: stands.
- **TP1 rule:** no pool ≥ 1 R nearer than the PWL (session low was 0.5 R), so the target is 10.3 R: the trade can only end at the stop or the clock.

## Verdict
**lucky win** — most useful change: a minimum area width; a fallback target (e.g. 1.5–2 R or 0.5 ADR) when the nearest pool ≥ 1 R is beyond the day.

## For the engine
- Across the 81: trades with TP1 > 1 ADR away (time exits by construction): count and R.
- One trade is a lead, not evidence; nothing is re-tuned on 2024-07 → 2026-11.
