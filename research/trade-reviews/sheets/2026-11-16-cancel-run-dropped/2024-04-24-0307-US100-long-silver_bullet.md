# Trade facts — US100 long Wed 24 Apr 2024 03:07 NY
entry 17589.664 · stop 17580.437 · TPs 17605.408 (50%), 18180.089 (50%) · stop to entry after TP1

**Trader's note:** [engine silver_bullet trade · window sb_london · POI 1h FVG 17580.17-17584.22 · bias bull · engine result -1.05 R (stop) · area / liquidity: leg start · decided 03:04 · trigger gap 1.71 points]

## Known at the entry (only bars before it)
- price 17596.1 · ADR 301.38 · risk 0.031 ADR · R:R to TP1 1.71
- engine read: **counter_weekly**, side bear → trade side matches the read: **False**
- clock windows: london_kz, london_sweet_spot, sb_london · news: none near
- scheduled news during the hold window (known in advance): GDP Thu 25 Apr 08:30 (high); Jobless claims Thu 25 Apr 08:30 (medium)
- market activity, last 60 min: range 0.082 ADR = **normal** (0.93× the normal for this time of day), net move 0.035 ADR
- order flow (CME futures trades): aligned imbalance last 5 min 0.123, last 60 min 0.051 (> 0 = flow with the trade); volume 1.1× normal for this hour
- current 4h range 16969.61–18335.47: entry at 0.454 from the low = **discount** (right half for a long) · momentum 0.12 ADR/candle
- liquidity taken in the 6 h before: buyside Asia high 17581.44 at 21:19; buyside 4h swing high 17593.70 at 22:07
- stop vs liquidity: nearest pool on the stop side last 4 h low 17580.69 — stop is beyond it by 0.001 ADR (sits at the liquidity)
- TP1 vs liquidity: pools before TP1: none
- pools above: 1h equal highs 17608.19 (0.04 ADR); 4h swing high 17614.39 (0.06 ADR); 1h swing high 17634.88 (0.13 ADR); 4h swing high 17802.90 (0.69 ADR)
- pools below: Asia low 17548.12 (0.16 ADR); 1h swing low 17452.62 (0.48 ADR); 1h swing low 17218.66 (1.25 ADR); 1h swing low 17175.81 (1.39 ADR)
- arrays near: 4h bullish FVG 17516.59–17583.30; 1d bearish FVG 17614.39–17622.02; 1h bullish volume imbalance 17561.01–17561.20; 4h bearish FVG 17634.88–17710.68; 1h bearish volume imbalance 17639.20–17639.84

<details><summary>engine read statements</summary>

- Monthly: structure broke up — Nov 2023 closed 15934.59 above the Jul 2023 swing high 15933.21 (BOS).
- Order blocks: 1M bearish OB Jul 2023 [not one to use: weak body, no aggressive push, no event, failed: closed through its MT, then traded through the body; body 0.59 of its range, 0.74× the mean body; push 0.32×; closed beyond its low]: body 15174.53–15770.78 (MT 15472.65), no event before it — just a candle; premium 0.92 of the dealing range 10431.57–15933.21 = the right place. Draw: the remaining 1M FVG 13258.70–14207.82 (CE 13733.26) — reached and respected so far (no body past its midpoint). | 1M bullish OB Oct 2023 [not one to use: weak body; holding; body 0.34 of its range, 0.62× the mean body; push 2.17×; closed beyond its high]: body 14387.80–14826.37 (MT 14607.08), after 1M bullish FVG revisited 14207.82 (to 14053.89); discount 0.29 of the dealing range 14053.89–15933.21 = the right place. | 1w bullish OB wk 11 Mar 2024 [not one to use: weak body, no event, wrong half, no HTF level, failed: closed through its MT, then traded through the body; body 0.32 of its range, 0.53× the mean body; push 1.61×; closed beyond its high]: body 17826.47–17983.73 (MT 17905.10), no event before it — just a candle; premium 0.84 of the look-back 15061.74–18465.80 = the wrong half. | 1w bearish OB wk 18 Mar 2024 [not one to use: no aggressive push, no HTF level; holding; body 0.73 of its range, 1.58× the mean body; push 0.29×; closed beyond its low]: body 17845.42–18324.69 (MT 18085.06), after equal highs 18418.09 (to 18465.80); premium 0.91 of the dealing range 14053.89–18465.80 = the right place. Draw: the remaining 1M FVG 16167.89–16173.22 (CE 16170.55) — not reached yet. | 1d bearish OB 16 Apr 2024 [not one to use: weak body, no event, wrong half, no HTF level; holding; body 0.01 of its range, 0.02× the mean body; push 1.66×; closed beyond its low]: body 17711.19–17713.75 (MT 17712.47), no event before it — just a candle; discount -0.76 of the dealing range 17759.22–17820.34 = the wrong half. Draw: the remaining 1M FVG 16968.39–17164.21 (CE 17066.30) — reached by the current candle; the current 1M candle (close pending) reached 16969.61 = 99% into it — past its midpoint, now 17592.19. | 1d bullish OB 19 Apr 2024 [not one to use: no aggressive push; holding; body 0.83 of its range, 2.17× the mean body; push 0.68×; closed beyond its high; into 1M bullish FVG 16968.39–17164.21]: body 17033.59–17391.80 (MT 17212.69), after swing low 17118.69 (to 16969.61); discount 0.17 of the dealing range 16969.61–18392.99 = the right place. Draw: the remaining 1d FVG 17614.39–17622.02 (CE 17618.20) — not reached yet.
- Weekly: bull since 15 May 2023. Protected higher low 14053.89 (11.8 ADR away) — until a W close breaks it, moves the other way are shifts inside a bull trend.
- Daily: bear since 14 Apr 2024. Protected lower high 18392.99 (2.6 ADR away) — until a D close breaks it, moves the other way are shifts inside a bear trend.
- 4H: bear since 02 Apr 06:00. Protected lower high 18335.47 (2.5 ADR away) — until a 4H close breaks it, moves the other way are shifts inside a bear trend.
- 1H: bull since 23 Apr 09:00. Protected higher low 17144.59 (1.5 ADR away) — until a 1H close breaks it, moves the other way are shifts inside a bull trend.
- Areas I'm watching: 1w FVG 16906.59–17283.62 (below, 1.0 ADR); 1d IFVG 17530.00–17896.53 (price is inside); 1d FVG 17820.34–17949.35 (above, 0.7 ADR); 1d IFVG 17403.30–17456.35 (below, 0.5 ADR).
- Liquidity — buyside above: 1h equal highs 17608.19 (0.0 ADR), 4h swing high 17614.39 (0.1 ADR), 1d previous week high 18180.09 (1.9 ADR); sellside below: 1h swing low 17452.62 (0.5 ADR), 1d previous day low 17144.59 (1.5 ADR), 1d previous week low 16969.61 (2.1 ADR).
- Where the play is: Daily bear against the weekly bull: the play sits on the daily — a counter-weekly leg. Expect small grabs (1h swing low 17452.62), not the distant weekly areas; the weekly protected level 14053.89 decides if it becomes more. Price is inside the 1d IFVG — respect there (reaction, closes holding) comes first.
- Current range (4H): the fake-out high 18335.47 (it took buyside 18278.92 first, against us) → the low of the move down since, 16969.61 — the distribution our PD arrays come from (momentum: the move ran 4.5 ADR in 37 4H candles). fib of the move: 0 = 16969.61, 0.5 EQ = 17652.54, OTE 0.62–0.79 = 17816.44–18048.64, 1 = 18335.47; price has pulled back to 0.46. Hoping for a premium: sell at an array on the pullback, in the order price meets them: 4h bearish IFVG 17466.41–17621.11 (0.36–0.48, shallow — risk: knocked out if price goes deeper); 1h bearish IFVG 17482.58–17621.11 (0.38–0.48, shallow — risk: knocked out if price goes deeper); 4h bearish IFVG 17485.59–17727.54 (0.38–0.55, around EQ); 1h bearish IFVG 17485.59–17646.79 (0.38–0.50, shallow — risk: knocked out if price goes deeper); 4h bearish FVG 17634.88–17710.68 (0.49–0.54, around EQ); 1h bearish IFVG 17652.32–17709.56 (0.50–0.54, around EQ). Shallow or deep is not right or wrong: shallow risks a knock-out, deep risks missing it — momentum decides. Target beyond the move: the liquidity in the play above.

</details>

## After the entry (hindsight — not knowable at the entry)
- your management: **-1.00 R** — filled Wed 24 Apr 03:07 → stopped Wed 03:17 at 17580.44
- MFE 0.68 R · MAE -1.0 R before the exit · held overnight: False
- same trade, flat 16:55 NY that day: **-1.00 R** — stopped Wed 03:17 at 17580.44
- price went on to 10.89 R in favour (at Thu 16:05) and -44.82 R against within the window
- **where price turned that day (the trade's own swing, to 16:55 NY):** 17528.37 at Wed 05:51 — 6.64 R (0.203 ADR) past our entry, 0.173 ADR beyond our stop; from there it ran 14.09 R (0.43 ADR) our way. Known levels at that price: 4h bullish FVG 17516.59–17583.30; 1d bearish IFVG 17530.00–17896.53; 4h bullish FVG 17500.51–17525.40; session so far low 17525.40
- **stopped, then TP1 traded at Wed 08:31** — the idea was right, the stop or timing wasn't
- pools price took next: Asia low 17548.12 (-4.5 R) Wed 05:35; 1h equal highs 17608.19 (+2.01 R) Wed 08:32; 4h swing high 17614.39 (+2.68 R) Wed 08:32; 1h swing high 17634.88 (+4.9 R) Wed 09:39; 1h swing low 17452.62 (-14.85 R) Wed 12:10; 1h swing low 17218.66 (-40.21 R) Thu 09:12