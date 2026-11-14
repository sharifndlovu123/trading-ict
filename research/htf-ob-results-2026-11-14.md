# Results: HTF order blocks as the PD-return POI (pre-registered 2026-11-14)

Run once, exactly as `research/preregistered-htf-ob-2026-11-14.md`: pd_return, 2022-01-03→2024-06-28, US100 US500
US30 XAUUSD XAGUSD, both cost bases, `variants --only HTF --workers 8`. Pass = out-of-sample exp R beats the
baseline with z ≥ 2.0 on a basis.

## Result: all five fail on both bases
Best: OB 4h+1d (open, body) on CFD costs, +0.088 R vs baseline, z +0.3 (64 OOS trades). On futures costs the same
variant is −0.130 R (z −0.8). No variant is above z 0.3 anywhere; "FVG + OB 15m–1d" is the worst on both bases
(z −1.1 / −1.3). Adding daily FVGs changes almost nothing (it adds ~1% more trades).

## What it means
- Order blocks as the entry array do not improve PD return. Fewer trades (OB-only cuts n by ~75%) at the same or
  lower win rate. Confirming on a close through the open (Sharif's/ICT's rule) vs the extreme makes no reliable
  difference.
- Mixing OBs into the FVG list dilutes it: more trades, lower expectancy.
- Defaults unchanged (`ob_confirm="extreme"`, `ob_measure="range"`, no OB arrays). The OB code stays for the
  IFVG + OB variants (IFVG pre-registration) and for review.

## Raw tables
=== cfd
| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 1019 | 26% | -0.124 | 328 | 31% [26%–36%] | +0.140 ± 0.102 | +0.000 | +0.0 |
| HTF OB 4h+1d (open, body) | 259 | 24% | -0.177 | 64 | 27% [17%–38%] | +0.228 ± 0.302 | +0.088 | +0.3 |
| HTF OB 4h+1d (extreme, body) | 216 | 24% | -0.144 | 58 | 22% [14%–35%] | +0.068 ± 0.321 | -0.071 | -0.2 |
| HTF OB 4h+1d (open, body, lookback 10) | 310 | 23% | -0.189 | 79 | 25% [17%–36%] | +0.187 ± 0.273 | +0.047 | +0.2 |
| HTF FVG + OB 15m-1d (open, body) | 1399 | 27% | -0.118 | 427 | 30% [26%–34%] | -0.001 ± 0.077 | -0.141 | -1.1 |
| HTF daily FVGs added | 1027 | 26% | -0.125 | 331 | 31% [26%–36%] | +0.129 ± 0.101 | -0.011 | -0.1 |
=== futures
| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 2625 | 28% | -0.040 | 976 | 28% [25%–31%] | +0.009 ± 0.058 | +0.000 | +0.0 |
| HTF OB 4h+1d (open, body) | 582 | 24% | -0.108 | 184 | 21% [16%–28%] | -0.121 ± 0.150 | -0.130 | -0.8 |
| HTF OB 4h+1d (extreme, body) | 465 | 24% | -0.105 | 165 | 22% [17%–29%] | -0.036 ± 0.167 | -0.045 | -0.3 |
| HTF OB 4h+1d (open, body, lookback 10) | 688 | 24% | -0.107 | 223 | 21% [16%–27%] | -0.113 ± 0.136 | -0.122 | -0.8 |
| HTF FVG + OB 15m-1d (open, body) | 3515 | 29% | -0.041 | 1303 | 27% [25%–30%] | -0.089 ± 0.047 | -0.098 | -1.3 |
| HTF daily FVGs added | 2630 | 28% | -0.039 | 981 | 28% [26%–31%] | +0.012 ± 0.058 | +0.003 | +0.0 |
