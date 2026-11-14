"""Target modes for the 2022 model and PD return (research/preregistered-liquidity-targets-2026-11-14.md + amendment 1).

    default   the models' own targets (``model_2022._targets``)
    pool      runner (final) → the strongest untaken pool beyond TP1 (1h/4h/1d swings + equal highs/lows of the last
              10 days and PDH/PDL/PWH/PWL, merged within 2 bp; ties → nearer)
    fvg_tp1   TP1 may also be the near edge of an unfilled 1h/4h/1d FVG of the *opposite* polarity ahead of entry
              (a long aims at a bearish FVG above: price reprices into the inefficiency, ICT "inefficiency to
              liquidity"); filled = traded through its far edge before the decision
    both      fvg_tp1 + pool
    hold      runner → the nearest higher-timeframe draw ≥ 3R (PDH/PDL, PWH/PWL, a 4h/1d pool, the near edge of an
              unfilled 4h/1d FVG ahead), held to the session close (16:55 NY futures, 16:10 CFD)
    eq_hold   TP1 → the 50% of the 4h dealing range (newest confirmed 4h swing high and low) when it lies ahead by at
              least the minimum TP1, else unchanged; runner as ``hold`` (research/preregistered-nested-fvg-2026-11-14.md)

Every candidate is built from bars at or before the decision (no look-ahead); a level counts only while untaken.
"""

from __future__ import annotations

import os
from datetime import datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import Level, equal_levels, fvgs, liquidity_pools, swing_levels, swings

MODES = ("default", "pool", "fvg_tp1", "both", "hold", "eq_hold")
NY = "America/New_York"
LOOKBACK_DAYS = 10
TOL_BP = 2.0
HOLD_MIN_R = 3.0
CTX_HIGH, CTX_LOW = ("pdh", "pwh"), ("pdl", "pwl")


def session_close(day) -> pd.Timestamp:
    """Flat before the close: 16:55 NY on futures (CME halts 17:00), 16:10 on CFDs (index CFDs halt 16:15)."""
    futures = os.environ.get("ICT_COST_BASIS", "futures") == "futures"
    return pd.Timestamp(datetime.combine(day, time(16, 55) if futures else time(16, 10)), tz=NY)


def _hist(bars_1m: pd.DataFrame, decided: pd.Timestamp) -> pd.DataFrame:
    i0 = bars_1m.index.searchsorted(decided - timedelta(days=LOOKBACK_DAYS), side="left")
    i1 = bars_1m.index.searchsorted(decided, side="right")
    return bars_1m.iloc[i0:i1]


def _untaken(hist: pd.DataFrame, lv: Level, decided: pd.Timestamp) -> bool:
    seg = hist[(hist.index > lv.valid_from) & (hist.index <= decided)]
    return seg.empty or (lv.price > float(seg.high.max()) if lv.side == "high" else lv.price < float(seg.low.min()))


def pools(hist: pd.DataFrame, decided: pd.Timestamp, ctx, tfs: tuple[str, ...], long: bool, entry: float) -> list:
    """Untaken pools ahead of entry on the trade's side: (price, name, strength)."""
    side = "high" if long else "low"
    tol = entry * TOL_BP / 1e4
    levels = [Level(n, ctx.levels[n], side, hist.index[0]) for n in (CTX_HIGH if long else CTX_LOW) if n in ctx.levels]
    for tf in tfs:
        bars = resample(hist, tf)
        bars = bars[bars.close_ts <= decided]
        sw = [e for e in swings(bars, tf) if e.ts <= decided]
        levels += [lv for lv in swing_levels(sw) + equal_levels(bars, sw, tol) if lv.side == side and lv.valid_from <= decided]
    live = [lv for lv in levels if _untaken(hist, lv, decided)]
    out = []
    for p in liquidity_pools(live, tol):
        if (p.price > entry) if long else (p.price < entry):
            out.append((float(p.price), "pool " + "+".join(p.members[:3]), int(p.strength)))
    return out


def fvg_draws(hist: pd.DataFrame, decided: pd.Timestamp, tfs: tuple[str, ...], long: bool, entry: float) -> list:
    """Near edges of unfilled opposite-polarity FVGs ahead of entry: (price, name)."""
    out = []
    for tf in tfs:
        bars = resample(hist, tf)
        bars = bars[bars.close_ts <= decided]
        for g in fvgs(bars, tf):
            if g.ts > decided or g.direction == ("bull" if long else "bear"):
                continue
            near, far = (g.bottom, g.top) if long else (g.top, g.bottom)
            if not (near > entry if long else near < entry):
                continue
            seg = hist[(hist.index > g.ts) & (hist.index <= decided)]
            filled = (not seg.empty) and (float(seg.high.max()) >= far if long else float(seg.low.min()) <= far)
            if not filled:
                out.append((float(near), f"{tf} FVG"))
    return out


def range_eq(hist: pd.DataFrame, decided: pd.Timestamp) -> tuple[float, float, float] | None:
    """(50%, low, high) of the 4h dealing range: the newest confirmed 4h swing high and swing low before ``decided``."""
    bars = resample(hist, "4h")
    bars = bars[bars.close_ts <= decided]
    sw = [e for e in swings(bars, "4h") if e.ts <= decided]
    hs = [e for e in sw if e.kind == "swing_high"]
    ls = [e for e in sw if e.kind == "swing_low"]
    if not hs or not ls:
        return None
    hi, lo = max(hs, key=lambda e: e.ts).top, max(ls, key=lambda e: e.ts).bottom
    return ((hi + lo) / 2, lo, hi) if hi > lo else None


def apply(mode: str, *, entry: float, stop: float, long: bool, tp1: float, tp1_name: str, final: float,
          final_name: str, bars_1m: pd.DataFrame, decided: pd.Timestamp, ctx, day, min_tp1: float,
          edge: float | None = None):
    """(tp1, tp1_name, final, final_name, time_exit) under ``mode``. ``min_tp1`` = the model's minimum TP1 distance
    (price); ``edge`` = a level TP1 must lie beyond (the 2022 model's arm), else the entry."""
    if mode not in MODES:
        raise ValueError(f"target mode must be one of {MODES}, got {mode!r}")
    if mode == "default":
        return tp1, tp1_name, final, final_name, None
    sign = 1 if long else -1
    risk = abs(entry - stop)
    beyond = lambda px, ref: sign * (px - ref) > 0
    hist = _hist(bars_1m, decided)
    if mode in ("fvg_tp1", "both"):
        ref = entry if edge is None else (max(entry, edge) if long else min(entry, edge))
        cands = [(px, n) for px, n in fvg_draws(hist, decided, ("1h", "4h", "1d"), long, entry)
                 if abs(px - entry) >= min_tp1 and beyond(px, ref)]
        if cands:
            px, n = min(cands, key=lambda c: abs(c[0] - entry))
            if abs(px - entry) < abs(tp1 - entry):
                tp1, tp1_name = px, n
        if abs(final - entry) < abs(tp1 - entry):
            final, final_name = tp1, tp1_name
    if mode in ("pool", "both"):
        ps = [p for p in pools(hist, decided, ctx, ("1h", "4h", "1d"), long, entry) if beyond(p[0], tp1)]
        if ps:
            px, n, _ = max(ps, key=lambda p: (p[2], -abs(p[0] - entry)))
            final, final_name = px, n
    if mode == "eq_hold":
        r = range_eq(hist, decided)
        ref = entry if edge is None else (max(entry, edge) if long else min(entry, edge))
        if r is not None and beyond(r[0], ref) and abs(r[0] - entry) >= min_tp1:
            tp1, tp1_name = r[0], f"4h range 50% ({r[1]:.2f}-{r[2]:.2f})"
        if abs(final - entry) < abs(tp1 - entry):
            final, final_name = tp1, tp1_name
    if mode in ("hold", "eq_hold"):
        draws = [(px, n) for px, n, _ in pools(hist, decided, ctx, ("4h", "1d"), long, entry)]
        draws += fvg_draws(hist, decided, ("4h", "1d"), long, entry)
        draws = [(px, n) for px, n in draws if abs(px - entry) >= HOLD_MIN_R * risk and beyond(px, tp1)]
        if draws:
            final, final_name = min(draws, key=lambda d: abs(d[0] - entry))
        return tp1, tp1_name, final, final_name, session_close(day)
    return tp1, tp1_name, final, final_name, None
