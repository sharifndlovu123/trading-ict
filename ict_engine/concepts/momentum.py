"""Where price is now on the intraday timeframes (concept layer: facts, not a score).

Sharif's notes on the engine's trades (2026-11-16): "the no. 1 focus is where we currently are", "the bias may be
buying, but we need current structures to support it first", "momentum is selling heavy, I would have sold instead";
and on entries far from the area: "you're shorting quite late".

    tf_state(bars_1m, at, tf)         → "bull" | "bear" | "neutral": the structure rule (context.weekly_structure_state:
                                        closes through the protected swing) on the completed ``tf`` candles before ``at``
    side_vs_structure(states, long)   → "with" | "against" | "split" for a trade side against several timeframes
    adr(bars_1m, at)                  → the mean daily range of the 20 completed trading days before ``at``
    dist_from_area(entry, lo, hi)     → 0 inside the area, else the distance to its nearer edge

Only bars before ``at`` are read, and a candle still forming is never used (no look-ahead).
"""
from __future__ import annotations

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import weekly_structure_state

SPAN = {"15m": pd.Timedelta(minutes=15), "1h": pd.Timedelta(hours=1), "4h": pd.Timedelta(hours=4)}
HISTORY = pd.Timedelta(days=75)


def tf_state(bars_1m: pd.DataFrame, at: pd.Timestamp, tf: str) -> str:
    past = bars_1m[(bars_1m.index >= at - HISTORY) & (bars_1m.index < at)]
    if past.empty:
        return "neutral"
    f = resample(past, tf)
    f = f[f.index + SPAN[tf] <= at]                      # completed candles only
    if len(f) < 20:
        return "neutral"
    return weekly_structure_state(f)[0]


def side_vs_structure(states: dict[str, str], long: bool) -> str:
    want = "bull" if long else "bear"
    other = "bear" if long else "bull"
    if states and all(s == want for s in states.values()):
        return "with"
    if states and all(s == other for s in states.values()):
        return "against"
    return "split"


def adr(bars_1m: pd.DataFrame, at: pd.Timestamp, days: int = 20) -> float | None:
    from ict_engine.concepts.liquidity_map import _daily
    past = bars_1m[(bars_1m.index >= at - pd.Timedelta(days=days * 2 + 10)) & (bars_1m.index < at)]
    if past.empty:
        return None
    d = _daily(past)
    d = d[d.close_ts < at - pd.Timedelta(minutes=1)]
    if len(d) and d.index[-1] >= (at + pd.Timedelta(hours=6)).normalize():
        d = d.iloc[:-1]                                  # the trading day still running
    return float((d.high - d.low).tail(days).mean()) if len(d) else None


def dist_from_area(entry: float, lo: float, hi: float) -> float:
    return max(0.0, lo - entry, entry - hi)
