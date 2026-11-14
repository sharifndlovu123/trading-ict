# Pre-registered: higher-timeframe IFVGs (failed FVGs) as the POI, inverted on their own timeframe's close

Written 2026-11-14, before any code or run. Source: Sharif's trade-review notes and drawings on the daily NQ chart,
Mar–Apr 2024 (2022-model trade of 2024-04-16), plus ICT rulings §10 (failed FVG → inversion) and §12 (liquidity).

## The narrative Sharif showed (daily NQ; engine-verified prices)
1. Bullish daily FVG 18289.25–18526.75 (Mar 20–21 2024). The bias was bullish; it was a buy zone.
2. The Apr 4 session **closed** below it (18072.5): the FVG failed → bearish IFVG.
3. The failure left sellside liquidity: equal lows ×3 at 18051.5 (Apr 3/4/9).
4. Price returned into the IFVG (Apr 11 high 18518.75, above its CE 18408): respected → validated.
5. A daily OB formed inside it (body 18184–18485.5), confirmed by the Apr 12 close through its open.
6. Price broke lower and cleared the equal lows (Apr 15).

## Engine change (before testing)
`inversions()` today flips any FVG on the first **1m** body close beyond its far edge. For a daily FVG that is
two days early here (Apr 2 09:17). New option: invert on a **close of the FVG's own timeframe** (the daily
close), timed at that candle's close (no look-ahead).

## Variants (pd_return; everything else at defaults)
| name | HTF TFs | arrays | IFVG inverted on | lookback days |
|---|---|---|---|---|
| HTF IFVG 4h+1d (tf close) | 4h, 1d | ifvg | own-TF close | 10 |
| HTF IFVG 4h+1d (1m close) | 4h, 1d | ifvg | 1m close (control) | 10 |
| HTF IFVG + OB 4h+1d (tf close; OB open, body) | 4h, 1d | ifvg, ob | own-TF close | 10 |
| HTF FVG + IFVG 15m–1d (tf close) | 15m, 1h, 4h, 1d | fvg, ifvg | own-TF close | 10 |

## Test and decision rule
Same as research/preregistered-htf-ob-2026-11-14.md: 2022-01-03→2024-06-28, its in-sample/out-of-sample split,
assets US100 US500 US30 XAUUSD XAGUSD, both cost bases. A variant counts only if its out-of-sample exp R beats the
baseline on that basis with z ≥ 2.0. Report all. Winner = forward-v2 candidate. 2024-07+ unused. The Apr 2024
example inspired the rule and is not used to score it.

## Not in this test (next pre-registration)
Targets from liquidity pools (TP1 nearest pool, runner to the strongest pool in the bias direction), and the
"pool left behind by the failed FVG" as the draw.

## Amendment 1 (2026-11-14, before any code or run): the IFVG as a counter-bias leg
Sharif: "bias was buying, it was just sellers' turn. The FVG was invalidated but changed to an IFVG and was
validated, showing respect for it." The higher-timeframe bias stayed bullish; the failed daily FVG marked a sell
**leg** inside it, aimed at the liquidity the failure left behind (the equal lows). The current bias gate would block
that short. Added variant:

| name | HTF TFs | arrays | IFVG inverted on | bias gate | lookback days |
|---|---|---|---|---|---|
| HTF IFVG 4h+1d (tf close, overrides bias) | 4h, 1d | ifvg | own-TF close | an IFVG trade may go against the daily bias | 10 |

"Overrides" is limited to IFVG arrays; every other array still needs the bias. Same test and pass bar as above
(5 variants now, z ≥ 2.0 out-of-sample, both cost bases).
