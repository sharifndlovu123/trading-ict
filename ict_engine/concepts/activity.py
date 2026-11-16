"""Market activity before a moment (concept layer: a fact, not a score).

Sharif 2026-11-16: "time is very important … we want to be in the market when price is moving and active, not sit
much when it's a dry consolidation."

    relative_activity(bars_1m, at)  → the range of the last ``mins`` minutes ÷ the median range of the same NY clock
                                      window on the previous ``days`` weekdays (1 = normal for this time of day)
    gate(bars_1m, at, min_rel)      → (ok, why) for a model's ``min_activity`` parameter

Only bars before ``at`` are read (no look-ahead). New-dataset sweep 2026-11-16 (review log #40): entries with
relative activity < 0.6 lost 0.17 R a trade over 675 trades, on six of seven datasets.
"""
from __future__ import annotations

import pandas as pd

QUIET, BUSY = 0.6, 1.5


def _range(bars: pd.DataFrame, end: pd.Timestamp, mins: int) -> float | None:
    w = bars.loc[end - pd.Timedelta(minutes=mins): end - pd.Timedelta(microseconds=1)]
    if len(w) < mins // 2:
        return None
    return float(w["high"].max() - w["low"].min())


def relative_activity(bars_1m: pd.DataFrame, at: pd.Timestamp, mins: int = 60, days: int = 20,
                      min_days: int = 5) -> dict:
    """{"range", "median", "relative", "state"}; ``relative`` is None when there is too little history."""
    now = _range(bars_1m, at, mins)
    past = []
    for k in range(1, days * 2):
        t = at - pd.Timedelta(days=k)                     # the same NY wall-clock time (DST-aware index)
        if t.weekday() >= 5:
            continue
        r = _range(bars_1m, t, mins)
        if r is not None:
            past.append(r)
        if len(past) >= days:
            break
    med = float(pd.Series(past).median()) if len(past) >= min_days else None
    rel = now / med if now is not None and med else None
    state = None if rel is None else "quiet" if rel < QUIET else "busy" if rel > BUSY else "normal"
    return {"range": now, "median": med, "relative": rel, "state": state}


def gate(bars_1m: pd.DataFrame, at: pd.Timestamp, min_rel: float) -> tuple[bool, str]:
    """Pass when the last hour's range is at least ``min_rel`` × normal for this time of day. Too little history to
    judge → pass (the gate never blocks on missing data)."""
    a = relative_activity(bars_1m, at)
    if a["relative"] is None:
        return True, "activity unknown (not enough history)"
    ok = a["relative"] >= min_rel
    return ok, f"last hour's range {a['relative']:.2f}× normal for this time ({'≥' if ok else '<'} {min_rel:g})"
