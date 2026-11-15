"""A stop on the timeframe of the draw (research/preregistered-htf-stop-2026-11-15.md; named-targets triage: Sharif's
PDH/PWL/PWH targets sat 2.3–22R from the engine's 1m stops and were never reached before them).

For a long (mirror for a short), applied to the frozen plan at the decision with bars at or before it:
    stop   newest confirmed ``tf`` swing low (last 10 days) below the model's stop → that low − stop buffer; none →
           the trade is unchanged
    final  nearest of PDH / PWH beyond TP1, untaken from 00:00 to the decision; else the model's final
TP1 keeps its price (fewer R), entry and expiry unchanged; the cost gate applies to the new risk.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import swings
from ict_engine.data.instruments import cost_at

TFS = ("15m", "1h")
LOOKBACK = timedelta(days=10)
NY = "America/New_York"
DRAWS = {True: ("pdh", "pwh"), False: ("pdl", "pwl")}


def structural_stop(bars_1m: pd.DataFrame, decided: pd.Timestamp, tf: str, beyond: float, long: bool) -> float | None:
    """Price of the newest confirmed ``tf`` swing low (high for a short) beyond ``beyond``, known by ``decided``."""
    hist = bars_1m[(bars_1m.index >= decided - LOOKBACK) & (bars_1m.index < decided)]
    if hist.empty:
        return None
    b = resample(hist, tf)
    b = b[b.close_ts <= decided]
    kind = "swing_low" if long else "swing_high"
    sw = [e for e in swings(b, tf) if e.kind == kind and e.ts <= decided
          and ((e.bottom < beyond) if long else (e.top > beyond))]
    if not sw:
        return None
    e = max(sw, key=lambda e: e.ts)
    return float(e.bottom if long else e.top)


def draw(ctx, bars_1m: pd.DataFrame, decided: pd.Timestamp, long: bool, beyond: float) -> tuple[float, str] | None:
    """Nearest PDH/PWH (PDL/PWL) beyond ``beyond`` and untaken from 00:00 to the decision."""
    d0 = pd.Timestamp(datetime.combine(decided.date(), time(0)), tz=NY)
    seen = bars_1m[(bars_1m.index >= d0) & (bars_1m.index < decided)]
    ok = []
    for n in DRAWS[long]:
        lvl = ctx.levels.get(n)
        if lvl is None or ((lvl <= beyond) if long else (lvl >= beyond)):
            continue
        if not seen.empty and ((seen.high.max() >= lvl) if long else (seen.low.min() <= lvl)):
            continue
        ok.append((float(lvl), n))
    return min(ok, key=lambda c: abs(c[0] - beyond)) if ok else None


def apply(tf: str, plan, bars_1m: pd.DataFrame, ctx, *, stop_buffer: float, asset: str,
          max_cost_r: float | None) -> tuple[bool, str, object]:
    """(keep the trade?, why, plan to trade)."""
    if tf not in TFS:
        raise ValueError(f"stop_tf must be one of {TFS}, got {tf!r}")
    long, decided = plan.side == "long", plan.placed_at
    lvl = structural_stop(bars_1m, decided, tf, plan.stop, long)
    if lvl is None:
        return True, f"no {tf} swing beyond the stop", plan
    stop = lvl - stop_buffer if long else lvl + stop_buffer
    why = f"stop {plan.stop:.2f} → {tf} swing {lvl:.2f}: {stop:.2f}"
    if max_cost_r is not None:
        c = cost_at(asset, plan.entry, decided) / abs(plan.entry - stop)
        if c > max_cost_r:
            return False, f"{why}: cost {c:.2f}R > {max_cost_r:g}R", None
    new = replace(plan, stop=stop)
    d = draw(ctx, bars_1m, decided, long, plan.tp1)
    if d is not None:
        new = replace(new, final_target=d[0], final_name=d[1])
        why += f"; final → {d[1]} {d[0]:.2f}"
    return True, why, new
