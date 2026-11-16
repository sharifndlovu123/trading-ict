# Trade facts — US30 short Fri 21 Jan 2022 03:05 NY
entry 34779.289 · stop 34800.007 · TPs 34660.279 (50%), 34444.709 (50%) · stop to entry after TP1

**Trader's note:** [engine silver_bullet trade · window sb_london · POI 1h FVG 34766.80-35135.30 · bias bear · engine result -1.09 R (stop) · area / liquidity: leg start · decided 03:00 · trigger gap 8.92 points]

## Known at the entry (only bars before it)
- price 34752.04 · ADR 428.4 · risk 0.048 ADR · R:R to TP1 5.74
- engine read: **ltf_pullback**, side bull → trade side matches the read: **False**
- clock windows: london_kz, london_sweet_spot, sb_london · news: none near
- scheduled news during the hold window (known in advance): none
- market activity, last 60 min: range 0.326 ADR = **busy** (2.29× the normal for this time of day), net move 0.192 ADR
- current 1d range 34662.72–36954.289: entry at 0.051 from the low = **discount** (WRONG half for a short) · momentum 0.45 ADR/candle
- liquidity taken in the 6 h before: sellside Asia low 34547.70 at 21:47; buyside Asia high 34695.24 at 00:45
- stop vs liquidity: nearest pool on the stop side session so far high 34799.76 — stop is beyond it by 0.001 ADR (sits at the liquidity)
- TP1 vs liquidity: pools before TP1: none
- pools above: 1h swing high 35340.30 (1.37 ADR); previous day high 35490.00 (1.72 ADR); 1h swing high 35505.28 (1.76 ADR); 4h swing high 35549.29 (1.86 ADR)
- pools below: Asia low 34444.71 (0.72 ADR); previous month low 33949.70 (1.87 ADR); 1d swing low 33814.22 (2.19 ADR); 1w swing low 33528.50 (2.86 ADR)
- arrays near: 1h bearish FVG 34766.80–35135.30; 4h bearish FVG 34718.23–35238.22; 1d bearish IFVG 34805.79–35207.30; 1h bullish volume imbalance 34613.20–34613.73; 1h bullish FVG 34594.80–34606.75

<details><summary>engine read statements</summary>

- Monthly: structure broke up — Oct 2021 closed 35840.72 above the Aug 2021 swing high 35628.30 (BOS). Equal highs 36683.28 (Nov 2021 36560.78, Dec 2021 36683.28) = the buyside that leg is drawn to; still resting.
- Order blocks: 1M bullish OB Sep 2021 [not one to use: no event, wrong half, failed: a close through its MT; body 0.79 of its range, 1.45× the mean body; push 1.87×; closed beyond its high]: body 33901.29–35410.22 (MT 34655.75), no event before it — just a candle; premium 0.71 of the dealing range 33612.20–35091.30 = the wrong half. | 1M bullish OB Nov 2021 [not one to use: no event, wrong half; holding; body 0.65 of its range, 1.26× the mean body; push 1.66×; traded through its high]: body 34495.23–35889.73 (MT 35192.48), no event before it — just a candle; premium 0.64 of the dealing range 34429.23–35628.30 = the wrong half. | 1w bullish OB wk 13 Dec 2021 [not one to use: no aggressive push, no event, no HTF level; body traded through (no close past MT); body 0.65 of its range, 1.30× the mean body; push 1.26×; closed beyond its high]: body 35421.20–36029.16 (MT 35725.18), no event before it — just a candle; discount 0.35 of the dealing range 35270.71–36560.78 = the right place. | 1w bearish OB wk 27 Dec 2021 [not one to use: no aggressive push, no HTF level; holding; body 0.52 of its range, 0.85× the mean body; push 0.37×; traded through its low]: body 35968.75–36389.70 (MT 36179.22), after swing high 36560.78 (to 36954.29); premium 0.84 of the dealing range 33528.50–36683.28 = the right place. Draw: the remaining 1M FVG 32081.24–32963.30 (CE 32522.27), liquidity at its edge 33026.75 — not reached yet. | 1d bullish OB 10 Jan 2022 [not one to use: weak body, no aggressive push, failed: closed through its MT, then traded through the body; body 0.27 of its range, 0.84× the mean body; push 0.90×; closed beyond its high; into 1w bullish FVG 36065.00–36108.72]: body 36060.26–36237.72 (MT 36148.99), after 1d bullish FVG revisited 35874.25 (to 35640.29); discount 0.39 of the dealing range 35640.29–36954.29 = the right place. Draw: the remaining 1d FVG 36384.30–36402.70 (CE 36393.50) — reached and respected so far (no body past its midpoint). | 1d bearish OB 12 Jan 2022 [not one to use: weak body, no aggressive push; holding; body 0.22 of its range, 0.37× the mean body; push 1.10×; closed beyond its low; into 1w old high 36210.30]: body 36255.77–36320.73 (MT 36288.25), after 1d bearish FVG revisited 36384.30 (to 36512.50); premium 0.80 of the dealing range 35640.29–36454.77 = the right place. Draw: the remaining 1M FVG 32081.24–32963.30 (CE 32522.27), liquidity at its edge 33026.75 — not reached yet.
- Weekly: bull since 10 Aug 2020. Protected higher low 33528.50 (2.9 ADR away) — until a W close breaks it, moves the other way are shifts inside a bull trend.
- Daily: bull since 14 Oct 2021. Protected higher low 34662.72 (0.2 ADR away) — until a D close breaks it, moves the other way are shifts inside a bull trend.
- 4H: bear since 14 Jan 06:00. Protected lower high 36512.50 (4.1 ADR away) — until a 4H close breaks it, moves the other way are shifts inside a bear trend.
- 1H: bear since 20 Jan 15:00. Protected lower high 35490.00 (1.7 ADR away) — until a 1H close breaks it, moves the other way are shifts inside a bear trend.
- Areas I'm watching: 1w IFVG 35300.09–35550.20 (above, 1.3 ADR); 1w FVG 33106.77–33270.72 (below, 3.5 ADR); 1d IFVG 34805.79–35207.30 (above, 0.1 ADR).
- Liquidity — buyside above: 1h swing high 35340.30 (1.4 ADR), 1d previous day high 35490.00 (1.7 ADR), 1w swing high 36954.29 (5.1 ADR); sellside below: Asia low 34444.71 (0.7 ADR), 1d previous month low 33949.70 (1.9 ADR), 1d swing low 33814.22 (2.2 ADR).
- Where the play is: Weekly and daily bull, the 4H against them: a lower-TF pullback reaching for lower-TF sellside (Asia low 34444.71) — the higher TF should be respected at an area, then bull resumes toward 1d previous day high 35490.00.
- Current range (D): the fake-out low 34662.72 (it took sellside 35377.75 first, against us) → the high of the move up since, 36954.29 — the distribution our PD arrays come from (momentum: the move ran 5.3 ADR in 12 D candles). fib of the move: 0 = 36954.29, 0.5 EQ = 35808.50, OTE 0.62–0.79 = 35533.52–35143.95, 1 = 34662.72; price has pulled back to 0.96 — past the OTE, the range is at risk. Hoping for a discount: buy at an array on the pullback, in the order price meets them: none left between price and the fake-out. Shallow or deep is not right or wrong: shallow risks a knock-out, deep risks missing it — momentum decides. Target beyond the move: the liquidity in the play above.

</details>

## After the entry (hindsight — not knowable at the entry)
- your management: **-1.00 R** — filled Fri 21 Jan 03:05 → stopped Fri 05:22 at 34800.01
- MFE 5.73 R · MAE -1.0 R before the exit · held overnight: False
- same trade, flat 16:55 NY that day: **-1.00 R** — stopped Fri 05:22 at 34800.01
- price went on to 27.15 R in favour (at Fri 16:12) and -5.58 R against within the window
- **where price turned that day (the trade's own swing, to 16:55 NY):** 34895.0 at Fri 11:23 — 5.58 R (0.27 ADR) past our entry, 0.222 ADR beyond our stop; from there it ran 32.74 R (1.58 ADR) our way. Known levels at that price: 1h bearish FVG 34766.80–35135.30; 4h bearish FVG 34718.23–35238.22; 1d bearish IFVG 34805.79–35207.30
- **stopped, then TP1 traded at Fri 06:24** — the idea was right, the stop or timing wasn't
- pools price took next: Asia low 34444.71 (+16.15 R) Fri 10:22