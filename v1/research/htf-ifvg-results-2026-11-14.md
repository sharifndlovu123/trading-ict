# Results: HTF IFVGs (failed FVGs) as the PD-return POI (pre-registered 2026-11-14, + amendments 1–2)

Run once, exactly as `research/preregistered-htf-ifvg-2026-11-14.md`: pd_return, 2022-01-03→2024-06-28, US100
US500 US30 XAUUSD XAGUSD, both cost bases, code bd9109e. Pass = out-of-sample exp R beats the baseline with z ≥ 2.0.

## Result: all six fail on both bases
| variant | CFD Δ (z) | futures Δ (z) |
|---|---|---|
| IFVG 4h+1d, own-TF close | −0.028 (−0.1) | −0.140 (−0.8) |
| IFVG 4h+1d, 1m close (control) | −0.154 (−0.5) | −0.163 (−1.0) |
| IFVG + OB 4h+1d | −0.031 (−0.1) | −0.118 (−0.9) |
| FVG + IFVG 15m–1d | −0.125 (−1.0) | −0.097 (−1.3) |
| IFVG 4h+1d, overrides bias ("sellers' turn") | −0.195 (−0.8) | −0.235 (−1.8) |
| IFVG + OB 1d+1w+1M | +0.056 (+0.2) | −0.108 (−0.7) |

## What it means
- **An IFVG on its own isn't a better place to wait for a PD-return entry than the plain FVGs.** Every variant
  has fewer trades and a lower OOS win rate (17–25% vs 28–31%).
- **Own-TF close beats 1m close on both bases** (CFD +0.111 vs −0.015 R; futures −0.131 vs −0.154 R), as Sharif's
  examples say, but the gap is far inside the noise (≈45–170 OOS trades each). The engine keeps the own-TF close
  as the IFVG default (`ifvg_close="tf"`) because it is the correct definition, not because it was shown to pay.
- **The counter-bias "sellers' turn" leg was the worst variant** (futures −0.226 R OOS, z −1.8; it looked best
  in-sample). Taking every IFVG against the daily bias does not work; Sharif's leg is a selective read (one that
  was respected and had EQLs to run), not "any IFVG beats the bias".
- Not tested here, and the better match to Sharif's point: the **flip after our own failed trade**
  (`preregistered-ifvg-flip-2026-11-14.md`), next.

Defaults unchanged (no IFVG arrays in pd_return).

## Raw tables
=== cfd
| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 1019 | 26% | -0.124 | 328 | 31% [26%–36%] | +0.140 ± 0.102 | +0.000 | +0.0 |
| HTF IFVG 4h+1d (tf close) | 207 | 24% | -0.096 | 45 | 22% [13%–36%] | +0.111 ± 0.331 | -0.028 | -0.1 |
| HTF IFVG 4h+1d (1m close) | 235 | 24% | +0.052 | 54 | 17% [9%–29%] | -0.015 ± 0.305 | -0.154 | -0.5 |
| HTF IFVG + OB 4h+1d (tf close; OB open, body) | 422 | 25% | -0.162 | 108 | 25% [18%–34%] | +0.108 ± 0.201 | -0.031 | -0.1 |
| HTF FVG + IFVG 15m-1d (tf close) | 1347 | 26% | -0.141 | 426 | 29% [25%–34%] | +0.014 ± 0.077 | -0.125 | -1.0 |
| HTF IFVG 4h+1d (tf close, overrides bias) | 323 | 26% | +0.009 | 80 | 21% [14%–31%] | -0.055 ± 0.214 | -0.195 | -0.8 |
| HTF IFVG + OB 1d+1w+1M (tf close; OB open, body) | 199 | 20% | -0.218 | 59 | 25% [16%–38%] | +0.196 ± 0.278 | +0.056 | +0.2 |
=== futures
| variant | IS n | IS win | IS exp R | OOS n | OOS win [95%] | OOS exp R ± se | Δ OOS vs base | z |
|---|---|---|---|---|---|---|---|---|
| baseline | 2625 | 28% | -0.040 | 976 | 28% [25%–31%] | +0.009 ± 0.058 | +0.000 | +0.0 |
| HTF IFVG 4h+1d (tf close) | 430 | 27% | -0.003 | 143 | 21% [15%–28%] | -0.131 ± 0.170 | -0.140 | -0.8 |
| HTF IFVG 4h+1d (1m close) | 508 | 26% | +0.076 | 167 | 19% [13%–25%] | -0.154 ± 0.155 | -0.163 | -1.0 |
| HTF IFVG + OB 4h+1d (tf close; OB open, body) | 923 | 26% | -0.052 | 306 | 22% [18%–27%] | -0.109 ± 0.113 | -0.118 | -0.9 |
| HTF FVG + IFVG 15m-1d (tf close) | 3402 | 28% | -0.066 | 1268 | 27% [24%–29%] | -0.088 ± 0.048 | -0.097 | -1.3 |
| HTF IFVG 4h+1d (tf close, overrides bias) | 700 | 28% | +0.045 | 233 | 20% [15%–25%] | -0.226 ± 0.119 | -0.235 | -1.8 |
| HTF IFVG + OB 1d+1w+1M (tf close; OB open, body) | 425 | 21% | -0.137 | 158 | 21% [15%–28%] | -0.099 ± 0.146 | -0.108 | -0.7 |

[exited with code 0]
