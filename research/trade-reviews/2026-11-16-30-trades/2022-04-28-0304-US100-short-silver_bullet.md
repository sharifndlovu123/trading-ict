# US100 short — Thu 28 Apr 2022 03:04 NY · −1.00 R (stopped 03:12) · day-only −1.00 R

Engine silver-bullet trade, in-sample. Fact sheet: `../sheets/2026-11-16-30-trades/2022-04-28-0304-US100-short-silver_bullet.md`.

## What they tried to do
London silver bullet short inside the 1h bearish FVG 13172.80–13249.91, with everything bear (read aligned). Entry 13232.48, stop 13245.95 (0.25 above the session high), TP1 13210.96, runner to the Asia low 13131.38.

## What happened
MFE +0.86 R, stopped 03:12 as price ran PDH 13256.20 in the same minute. TP1 traded at 08:30 (GDP), the Asia low at 09:44 (+7.5 R). Then price rallied to 13541.09 by 15:25 and fell 52 R from there by Friday.

## Checklist
| # | Step | Grade | Evidence (known at entry) |
|---|---|---|---|
| 1 | Time and activity | pass | sb_london / london_sweet_spot, 03:04; activity normal (1.47×, lively); GDP is 5.4 h away |
| 2 | Bias / narrative | pass | read aligned, side bear; W / D / 4H / 1H all bear |
| 3 | Dealing range | fail | 0.286 of the 4h range 12806.83–14294.10 = discount; price inside the 1w bullish FVG 13183.32–13312.89 |
| 4 | POI / array | partial | 1h bearish FVG, a shallow array (0.25–0.30 of the range); the 4h bearish FVG 13270.26–13428.15 was the next one up |
| 5 | Liquidity before | partial | buyside Asia high and two 1h swing highs taken (22:40–02:43), but PDH 13256.20 was 24 pts above and untaken |
| 6 | Trigger | partial | proxy: entry 13 pts under a session high still rising into PDH |
| 7 | Stop | fail | 13.5 pts (0.034 ADR), 10 pts (0.026 ADR) SHORT of PDH 13256.20 |
| 8 | Targets | pass | TP1 with nothing in front; runner front of the Asia low; R:R 1.6 |
| 9 | Management | n/a | stopped before TP1 |
| 10 | Attribution | fail | right side, stop under the obvious pool = the lesson |

Step 6 is a proxy.

## Price we should have looked at
- **The turn on the sheet** (13541.09 at 15:25) came 12 h later, after the trade's own targets had already traded: a different swing (the NY afternoon rally). It was at known levels (1d IFVG 13488.12–13821.24, 4h bearish FVG 13504.46–13614.01, 1h swing high 13524.90), 0.79 ADR above our entry.
- **The trade's own level, known at entry:** PDH 13256.20, 0.060 ADR above the entry and 0.026 ADR beyond the stop, with the 4h bearish FVG 13270.26–13428.15 starting 14 pts above it (0.096 ADR above the entry). Price took PDH at 03:12; the exact high after that is not on the sheet.
- **Where to price it:** sell after the PDH raid, at the 4h FVG's low 13270.26, stop above the raid high. Selling 24 pts under an untaken PDH with a 13-pt stop put the stop in the raid.

## What they missed / should have seen (known at the entry)
- PDH one stop-size above the entry; "stop vs liquidity" on the sheet only saw the session high.
- A short in the discount, inside a weekly bullish FVG.

## What the market did (hindsight — lessons to test, not blame)
- Stopped, then TP1 and the Asia low (+7.5 R) the same morning.

## Verdict
**lesson loss.** The idea paid; the stop was inside the PDH raid.

## For the engine
- "Stop vs liquidity" should look at every pool within 0.05 ADR beyond the stop (PDH here), not only the nearest; `stop_beyond_pool_adr` then moves the stop or waits for the raid. Also a risk floor: test `min_risk_adr` 0.06–0.08.
