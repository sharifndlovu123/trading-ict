# Trade facts — US500 short Fri 22 Sep 2023 10:23 NY
entry 4342.737 · stop 4347.167 · TPs 4332.853 (50%), 4326.661 (50%) · stop to entry after TP1

**Trader's note:** [engine silver_bullet trade · window sb_am · POI 4h FVG 4333.20-4350.29 · bias bear · engine result -1.08 R (stop) · area / liquidity: leg start · decided 10:11 · trigger gap 0.68 points]

## Known at the entry (only bars before it)
- price 4340.25 · ADR 43.14 · risk 0.103 ADR · R:R to TP1 2.23
- engine read: **counter_weekly**, side bear → trade side matches the read: **True**
- clock windows: ny_am_kz, sb_am · news: none near
- scheduled news during the hold window (known in advance): none
- market activity, last 60 min: range 0.326 ADR = **normal** (0.73× the normal for this time of day), net move 0.067 ADR
- current 4h range 4324.169–4466.03: entry at 0.131 from the low = **discount** (WRONG half for a short) · momentum 0.16 ADR/candle
- liquidity taken in the 6 h before: **none** (no sweep before the entry)
- stop vs liquidity: nearest pool on the stop side 1h swing high 4348.06 — stop is SHORT of it by 0.021 ADR (sits at the liquidity)
- TP1 vs liquidity: pools before TP1: none
- pools above: 1h swing high 4348.06 (0.18 ADR); 1h swing high 4365.16 (0.58 ADR); 1h swing high 4373.91 (0.78 ADR); 4h swing high 4394.18 (1.25 ADR)
- pools below: London low 4331.41 (0.20 ADR); Asia low 4324.17 (0.37 ADR); 1d swing low 4256.74 (1.94 ADR); 1w swing low 4103.39 (5.49 ADR)
- arrays near: 1d bullish FVG 4322.26–4334.56; 4h bearish FVG 4333.20–4350.29; 1h bullish FVG 4330.25–4330.75; 1h bearish FVG 4350.10–4350.95; 1w bullish FVG 4322.26–4340.71

<details><summary>engine read statements</summary>

- Monthly: structure broke up — Jun 2023 closed 4444.08 above the Feb 2023 swing high 4195.33 (BOS). Equal highs 4606.94 (Jul 2023 4606.94, Aug 2023 4596.65) = the buyside that leg is drawn to; still resting.
- Order blocks: 1M bearish OB Nov 2022 [not one to use: no aggressive push, failed: closed through its MT, then traded through the body; body 0.54 of its range, 0.89× the mean body; push 1.04×; open crossed only]: body 3874.11–4082.21 (MT 3978.16), after 1M bearish FVG revisited 3905.45 (to 4136.19); premium 0.77 of the dealing range 3635.55–4082.51 = the right place. Draw: the remaining 1M FVG 3068.84–3072.94 (CE 3070.89), liquidity at its edge 3209.14 — not reached yet. | 1M bullish OB Feb 2023 [not one to use: weak body, no aggressive push, no event; holding; body 0.44 of its range, 0.46× the mean body; push 0.61×; closed beyond its high]: body 3961.48–4071.60 (MT 4016.54), no event before it — just a candle; discount 0.08 of the dealing range 3942.35–4817.00 = the right place. | 1w bearish OB wk 24 Jul 2023 [not one to use: no event; holding; body 0.57 of its range, 0.85× the mean body; push 1.92×; closed beyond its low; into 1M bearish IFVG 4550.80–4559.73]: body 4535.78–4580.57 (MT 4558.18), no event before it — just a candle; premium 0.96 of the dealing range 3489.69–4606.94 = the right place. Draw: the remaining 1M FVG 4234.23–4377.37 (CE 4305.80) — reached and respected so far (no body past its midpoint); the current 1M candle (close pending) reached 4326.66 = 35% into it, now 4327.41. | 1w bullish OB wk 14 Aug 2023 [not one to use: no aggressive push; body traded through (no close past MT); body 0.58 of its range, 1.68× the mean body; push 0.67×; closed beyond its high; into 1M bullish FVG 4234.23–4377.37]: body 4370.52–4466.53 (MT 4418.52), after swing low 4377.37 (to 4336.27); discount 0.30 of the dealing range 4336.27–4606.94 = the right place. | 1d bearish OB 14 Sep 2023 [tradeable; holding; body 0.89 of its range, 2.01× the mean body; push 2.70×; closed beyond its low; into 1w bearish FVG 4454.60–4581.00]: body 4469.93–4509.31 (MT 4489.62), after swing high 4490.93 (to 4516.38); premium 0.73 of the dealing range 4429.28–4511.47 = the right place. Draw: the remaining 1M FVG 4234.23–4377.37 (CE 4305.80) — reached by the current candle; the current 1M candle (close pending) reached 4324.17 = 37% into it, now 4340.51. | 1d bearish OB 18 Sep 2023 [not one to use: weak body, no aggressive push, no event; body traded through (no close past MT); body 0.09 of its range, 0.11× the mean body; push 0.44×; closed beyond its low; into 1w bearish FVG 4454.60–4581.00]: body 4452.65–4454.99 (MT 4453.82), no event before it — just a candle; premium 0.67 of the dealing range 4429.28–4466.03 = the right place. Draw: the remaining 1M FVG 4234.23–4377.37 (CE 4305.80) — reached by the current candle; the current 1M candle (close pending) reached 4324.17 = 37% into it, now 4340.51.
- Weekly: bull since 12 Jun 2023. Protected higher low 3489.69 (19.7 ADR away) — until a W close breaks it, moves the other way are shifts inside a bull trend.
- Daily: bear since 16 Aug 2023. Protected lower high 4540.45 (4.6 ADR away) — until a D close breaks it, moves the other way are shifts inside a bear trend.
- 4H: bear since 19 Sep 06:00. Protected lower high 4466.03 (2.9 ADR away) — until a 4H close breaks it, moves the other way are shifts inside a bear trend.
- 1H: bear since 19 Sep 09:00. Protected lower high 4394.18 (1.3 ADR away) — until a 1H close breaks it, moves the other way are shifts inside a bear trend.
- Areas I'm watching: 1w FVG 4322.26–4340.71 (price is inside); 1w IFVG 4308.75–4380.73 (price is inside); 1w FVG 4290.55–4301.07 (below, 0.9 ADR); 1d FVG 4401.55–4416.14 (above, 1.4 ADR); 1d FVG 4322.26–4334.56 (below, 0.1 ADR).
- Liquidity — buyside above: 1h swing high 4348.06 (0.2 ADR), 4h swing high 4394.18 (1.2 ADR), 1d previous day high 4401.55 (1.4 ADR); sellside below: London low 4331.41 (0.2 ADR), Asia low 4324.17 (0.4 ADR), 1d swing low 4256.74 (1.9 ADR).
- Where the play is: Daily bear against the weekly bull: the play sits on the daily — a counter-weekly leg. Expect small grabs (London low 4331.41), not the distant weekly areas; the weekly protected level 3489.69 decides if it becomes more. Price is inside the 1w FVG — respect there (reaction, closes holding) comes first.
- Current range (4H): the fake-out high 4466.03 (it took buyside 4460.89 first, against us) → the low of the move down since, 4324.17 — the distribution our PD arrays come from (momentum: the move ran 3.3 ADR in 21 4H candles). fib of the move: 0 = 4324.17, 0.5 EQ = 4395.10, OTE 0.62–0.79 = 4412.12–4436.24, 1 = 4466.03; price has pulled back to 0.11. Hoping for a premium: sell at an array on the pullback, in the order price meets them: 1h bearish FVG 4332.58–4346.80 (0.06–0.16, shallow — risk: knocked out if price goes deeper); 4h bearish FVG 4333.20–4350.29 (0.06–0.18, shallow — risk: knocked out if price goes deeper); 4h bearish IFVG 4348.55–4373.54 (0.17–0.35, shallow — risk: knocked out if price goes deeper); 1h bearish FVG 4350.10–4350.95 (0.18–0.19, shallow — risk: knocked out if price goes deeper); 1h bearish IFVG 4356.92–4362.51 (0.23–0.27, shallow — risk: knocked out if price goes deeper); 1h bearish FVG 4368.70–4372.67 (0.31–0.34, shallow — risk: knocked out if price goes deeper). Shallow or deep is not right or wrong: shallow risks a knock-out, deep risks missing it — momentum decides. Target beyond the move: the liquidity in the play above.

</details>

## After the entry (hindsight — not knowable at the entry)
- your management: **-1.00 R** — filled Fri 22 Sep 10:23 → stopped Fri 10:31 at 4347.17
- MFE 0.62 R · MAE -1.0 R before the exit · held overnight: False
- same trade, flat 16:55 NY that day: **-1.00 R** — stopped Fri 10:31 at 4347.17
- price went on to 6.04 R in favour (at Fri 15:52) and -3.29 R against within the window
- **where price turned that day (the trade's own swing, to 16:55 NY):** 4357.31 at Fri 11:39 — 3.29 R (0.338 ADR) past our entry, 0.235 ADR beyond our stop; from there it ran 9.33 R (0.96 ADR) our way. Known levels at that price: 1w bullish IFVG 4308.75–4380.73
- **stopped, then TP1 traded at Fri 13:38** — the idea was right, the stop or timing wasn't
- pools price took next: 1h swing high 4348.06 (-1.2 R) Fri 10:31; London low 4331.41 (+2.56 R) Fri 13:38; Asia low 4324.17 (+4.19 R) Fri 14:16