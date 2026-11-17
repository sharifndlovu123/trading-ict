"""Higher-timeframe draw after a break of structure (concept layer: facts, no score).

Sharif (2026-11-16, gold): the monthly FVG became interesting only because of the monthly BOS and the equal lows it
left — "once that happened we were interested in lower levels". The chain, bearish (bullish mirrors):

  1. BOS: a candle CLOSES below the latest confirmed swing low (a wick is not a break).
  2. Equal lows (relative): two or more candle lows within ``tol`` of each other, below the broken swing low, with
     nothing traded below the cluster between them — the sellside the new leg is drawn to. Candle lows, not only
     fractal swings: Nov 2025 3,928 / Jun 3,941 / Jul 3,959 on gold monthly, where Nov is not a 3-bar swing.
  3. Draw: beyond those lows, the nearest remaining FVG on that side (one traded right through is used up).

    bos_draw(bars, tf, as_of)   → the latest BOS with its equal lows/highs (taken or not, when) and the draw beyond.

Only bars closed by ``as_of`` are used (no look-ahead).
"""
from __future__ import annotations

import pandas as pd

from ict_engine.concepts.events import fvgs, swings


def _closed(bars: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    return bars[(bars["close_ts"] if "close_ts" in bars else bars.index) <= as_of]


def _breaks(b: pd.DataFrame, tf: str) -> list[dict]:
    """Every close through the latest confirmed swing on either side (known at that close), oldest first."""
    cts = b["close_ts"] if "close_ts" in b else pd.Series(b.index, index=b.index)
    sw = swings(b, tf)
    out = []
    for j in range(len(b)):
        t = cts.iloc[j]
        known = [e for e in sw if e.ts < t and e.origin_ts < b.index[j]]
        for kind, bear in (("swing_low", True), ("swing_high", False)):
            ks = [e for e in known if e.kind == kind]
            if not ks:
                continue
            e = max(ks, key=lambda x: x.origin_ts)
            seg = b.loc[e.origin_ts:].iloc[1:]
            seg = seg[seg.index <= b.index[j]]
            thru = seg[seg.close < e.bottom] if bear else seg[seg.close > e.top]
            if len(thru) and thru.index[0] == b.index[j]:            # the first close through it
                out.append({"direction": "bear" if bear else "bull", "level": float(e.bottom if bear else e.top),
                            "swing": e.origin_ts, "candle": b.index[j], "close": float(b.close.iloc[j]), "known": t})
    return out


def _equal(b: pd.DataFrame, bos: dict, tol: float) -> dict | None:
    """Relative equal lows (highs) beyond the broken level, at least one formed at or after the BOS candle."""
    bear = bos["direction"] == "bear"
    x = b.low if bear else b.high
    pos_bos = b.index.get_loc(bos["candle"])
    best = None
    for j in range(pos_bos, len(b)):
        for i in range(j):
            a, c = float(x.iloc[i]), float(x.iloc[j])
            if abs(a - c) > tol or not ((max(a, c) < bos["level"]) if bear else (min(a, c) > bos["level"])):
                continue
            between = x.iloc[i + 1:j]
            edge = min(a, c) if bear else max(a, c)
            if len(between) and ((between.min() < edge - 1e-9) if bear else (between.max() > edge + 1e-9)):
                continue
            mem = [k for k in range(i, j + 1) if abs(float(x.iloc[k]) - edge) <= tol]
            if best is None or len(mem) > len(best) or (len(mem) == len(best) and mem[-1] > best[-1]):
                best = mem
    if not best:
        return None
    px = [float(x.iloc[k]) for k in best]
    lvl = min(px) if bear else max(px)
    after = b.iloc[best[-1] + 1:]
    hit = after[after.low < lvl] if bear else after[after.high > lvl]
    return {"prices": [round(p, 2) for p in px], "candles": [b.index[k] for k in best], "level": round(lvl, 2),
            "taken": None if hit.empty else {"candle": hit.index[0],
                                             "extreme": round(float(hit.low.iloc[0] if bear else hit.high.iloc[0]), 2)}}


def _draw(b: pd.DataFrame, tf: str, bear: bool, beyond: float) -> dict | None:
    """The nearest remaining FVG beyond ``beyond`` (below for bear); one traded right through is used up."""
    out = []
    for g in fvgs(b, tf):
        if g.direction != ("bull" if bear else "bear"):
            continue
        after = b[b.index > g.origin_ts].iloc[1:]
        used = (after.low < g.bottom).any() if bear else (after.high > g.top).any()
        if not used and ((g.top < beyond) if bear else (g.bottom > beyond)):
            out.append(g)
    if not out:
        return None
    g = max(out, key=lambda x: x.top) if bear else min(out, key=lambda x: x.bottom)
    reached = b[b.index > g.origin_ts].iloc[1:]
    reached = (reached.low <= g.top).any() if bear else (reached.high >= g.bottom).any()
    return {"fvg": (round(float(g.bottom), 2), round(float(g.top), 2)), "ce": round(float(g.ce), 2),
            "edge": round(float(g.top if bear else g.bottom), 2), "reached": bool(reached)}


def bos_draw(bars: pd.DataFrame, tf: str, as_of: pd.Timestamp, tol_frac: float = 0.1) -> dict | None:
    """The latest BOS on ``tf`` known by ``as_of``, the equal lows/highs beyond it and the draw past them.
    ``tol`` = ``tol_frac`` × the mean range of the last 14 bars (as ``ob_context._event``)."""
    b = _closed(bars, as_of)
    if len(b) < 5:
        return None
    tol = tol_frac * float((b.high - b.low).tail(14).mean())
    bos, eq = None, None
    for x in _breaks(b, tf):
        # a close through a member of the live equal lows is that liquidity being delivered, not a new break
        if bos and eq and x["direction"] == bos["direction"] and x["swing"] in eq["candles"]:
            continue
        bos, eq = x, _equal(b, x, tol)
    if bos is None:
        return None
    bear = bos["direction"] == "bear"
    beyond = eq["level"] if eq else bos["level"]
    return {"tf": tf, "bos": bos, "equal": eq, "draw": _draw(b, tf, bear, beyond)}
