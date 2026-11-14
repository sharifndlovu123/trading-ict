# PD array return: variant sweep (2026-11-14)

`uv run python -m ict_engine.eval.variants 2022-01-03 2024-06-28 --model pd_return --assets US100 US500 US30 XAUUSD XAGUSD --cost {cfd,futures}`
(commit 568a600). Hold-out = the last 30% of 2022–24 (2023-09-29 → 2024-06-28). Full tables:
`reports/variants-pd_return-2022-01-03-2024-06-28{,-futures}.md`.

| Variant | Δ OOS vs baseline, CFD (z) | Δ OOS, futures (z) |
|---|---|---|
| baseline OOS exp R | +0.140 ± 0.102 (n 328) | +0.009 ± 0.058 (n 976) |
| no bias | −0.132 (−1.1) | −0.015 (−0.2) |
| + macros (to 11:10) | −0.022 (−0.2) | −0.002 (−0.0) |
| macros only | +0.286 (+1.1, n 75) | +0.100 (+0.6, n 148) |
| stop beyond array | −0.103 (−0.9) | −0.053 (−0.7) |
| entry at CE | +0.050 (+0.3) | +0.059 (+0.7) |
| arrays 1h+4h only | +0.028 (+0.1) | +0.081 (+0.8) |
| lookback 2 days | +0.037 (+0.2) | +0.012 (+0.1) |
| tp1 cap 2R | −0.086 (−0.7) | −0.087 (−1.2) |
| no cost gate | **−0.614 (−5.6)** | **−0.160 (−2.4)** |

**Reading**
- No variant beats the baseline out-of-sample (all |z| < 2), so the defaults stay as they are.
- The cost gate is the one clear effect, and it **protects**. Without it, tight-stop entries flood in and lose
  (−0.48R CFD, −0.16R futures). This repeats the 2022-model finding.
- In-sample the baseline loses (−0.12 CFD, −0.04 futures). The positive OOS baseline on CFD (+0.14, z 1.4) is a
  sign flip between halves, which is noise, not an edge.
- "Macros only" is the largest positive Δ on both bases but has a small n (75 / 148). It's a hypothesis for the
  forward log, not a default. It isn't a forward-test candidate either: candidates were fixed in
  `forward-test-protocol.md` before this sweep.
- ICT's 2023-11-28 trade at 11:11 stays outside every documented window. No window was invented for it.

## Array types (models.md §6: OB / breaker / mitigation block; commit 62c1cd7)
| Variant | Δ OOS vs FVG baseline, CFD (z) | Δ OOS, futures (z) | In-sample exp R (CFD / futures) |
|---|---|---|---|
| order block | −0.065 (−0.5) | −0.065 (−0.8) | −0.117 / −0.088 |
| breaker | +0.138 (+0.6, n 119) | −0.008 (−0.1) | −0.122 / −0.084 |
| mitigation block | +0.260 (+1.3, n 161) | +0.009 (+0.1) | −0.081 / −0.103 |
| FVG + OB + breaker + MB | −0.019 (−0.1) | −0.025 (−0.3) | −0.106 / −0.047 |

No array type beats the FVG baseline out-of-sample, and all of them lose in-sample on both bases. ICT's own live
examples used FVG-family arrays only, so FVG stays the default. The array is not the lever.
