# Pre-registered: Candle Range Theory as a pattern (written 2026-11-14, before any code or run)

Sharif: "also read into CRT models" → "proceed". Card: `references/patterns.md` (third-party). ICT rulings §16: ICT calls
CRT a Twitter copy of Power of 3 + turtle soup of the previous candle's high/low, valid only with HTF order flow. So
this is a **pattern** test (does the move happen more than chance, after costs?), with the bias filter as ICT's
condition. A pass does not make CRT a model; it becomes a tag/candidate for models.

## Event (per timeframe, from 1m bars, NY time)
- C1, C2 = two consecutive finished candles. **Bearish CRT:** C2.high > C1.high, C2.low ≥ C1.low (one side only),
  C1.low < C2.close < C1.high (closed back inside). Bullish = mirror.
- Known at C2's close. No look-ahead: entry = **market at the open of the first 1m bar after C2's close**.
- Stop = C2's extreme (the sweep wick). TP1 = C1's 50%; if the fill is already past the 50%, TP1 = C1's far end.
  Final = C1's far end. 50% off at TP1, runner stop to entry (engine defaults, `simulate`).
- Time exit = the end of the 3rd candle after C2 (C3–C5; 86–92% of CRTs resolve within 3 candles per the only study
  cited). Costs: `instruments.cost_at` on each basis.

## Cells (12)
| cell | C1 timeframe / time | filter |
|---|---|---|
| 1–2 | 1h, every candle | all / bias agrees |
| 3–4 | 4h, CME grid (02/06/10/14/18/22 NY; our `resample`) | all / bias agrees |
| 5–6 | 4h, FX grid (01/05/09/13/17/21 NY; the grid "1-5-9" assumes) | all / bias agrees |
| 7–8 | 1d (18:00→17:00 trading day) | all / bias agrees |
| 9–10 | "1-5-9": C1 = the 01:00 FX-grid 4h, C2 = 05:00, expansion in 09:00 | all / bias agrees |
| 11–12 | 1H 08→09: C1 = 08:00 1h, C2 = 09:00 | all / bias agrees |

"Bias agrees" = the engine's default bias rule (`prev_day_dol`) for the trading day of the entry, from daily bars
completed before that day, points the trade's way. (Note for the 1d cells: `prev_day` compares C1 and C2 themselves,
so a bearish daily CRT — higher high, higher low — reads "bull" there; reported as is.)

## Data, split, decision rule
US100 US500 US30 XAUUSD XAGUSD, 2022-01-03→2024-06-28 (2024-07+ unused). Split by date as the variants tool: first
70% in-sample, last 30% out-of-sample. Measure: expectancy in R **with the runner** (`runner_r`), and the all-out-at-TP1
R and TP1 hit rate beside it. A cell passes only if OOS expectancy > 0 with **z ≥ 2.6** (12 cells), **≥ 30 OOS trades**,
in-sample expectancy also > 0, **on both cost bases**. Report all cells.

Descriptive only (not scored): the same trade after a one-sided sweep that **closed outside** C1 (fading a breakout),
to see whether "closed back inside" adds anything.
