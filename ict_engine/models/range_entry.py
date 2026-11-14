"""Premium/discount of the range in play, and a deeper entry on the leg
(research/preregistered-range-in-play-2026-11-14.md; ICT ruling §17; Sharif 2026-11-14: "what matters is the current
trading range we are inside", "it doesn't invalidate the entry at the FVG … but we would like to buy cheaper").

    cheap_half   no trade when the entry lies in the expensive half of the range in play (premium for a long)
    eq_limit     when it does, the limit moves to the range's 50% instead (stop and targets unchanged)
    leg_ote      the limit moves to the 70.5% retracement of the leg (sweep extreme → furthest price before the
                 decision) when that is deeper than the model's entry (stop and targets unchanged)

Range in play at the decision: a live 4h FVG containing the entry, else the 1h dealing range (newest 1h swing high above
the swing high before it = took buyside; newest 1h swing low below the swing low before it = took sellside; entry between
them), else none (trade unchanged). Applied in ``sim.run.run_day`` to the frozen plan at the decision; reads only bars
at or before it. A deeper limit is skipped when it lies beyond the stop or fails the model's cost gate on the new risk.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import swings
from ict_engine.data.instruments import cost_at
from ict_engine.models.entry_quality import _live_htf_fvgs, _upto

MODES = ("cheap_half", "eq_limit", "leg_ote")
OTE = 0.705
H1_LOOKBACK = timedelta(days=10)
LEG_LOOKBACK = timedelta(hours=12)


def dealing_range_1h(bars_1m: pd.DataFrame, decided: pd.Timestamp) -> tuple[float, float] | None:
    """(low, high) of the newest 1h swing high/low that each took the previous one's liquidity, confirmed by ``decided``."""
    hist = _upto(bars_1m, decided - H1_LOOKBACK, decided)
    if hist.empty:
        return None
    b = resample(hist, "1h")
    b = b[b.close_ts <= decided]
    sw = sorted((e for e in swings(b, "1h") if e.ts <= decided), key=lambda e: e.ts)
    hs = [e.top for e in sw if e.kind == "swing_high"]
    ls = [e.bottom for e in sw if e.kind == "swing_low"]
    hi = next((hs[i] for i in range(len(hs) - 1, 0, -1) if hs[i] > hs[i - 1]), None)
    lo = next((ls[i] for i in range(len(ls) - 1, 0, -1) if ls[i] < ls[i - 1]), None)
    return (float(lo), float(hi)) if hi is not None and lo is not None and hi > lo else None


def range_in_play(bars_1m: pd.DataFrame, decided: pd.Timestamp, price: float) -> tuple[float, float, str] | None:
    for g in _live_htf_fvgs(bars_1m, decided, "4h"):
        if g.bottom <= price <= g.top:
            return float(g.bottom), float(g.top), f"4h {g.direction} FVG"
    r = dealing_range_1h(bars_1m, decided)
    if r and r[0] < price < r[1]:
        return r[0], r[1], "1h dealing range"
    return None


def leg(bars_1m: pd.DataFrame, decided: pd.Timestamp, extreme: float, long: bool) -> float | None:
    """Furthest price from the sweep ``extreme`` after the bar that set it, up to the decision."""
    seg = _upto(bars_1m, decided - LEG_LOOKBACK, decided)
    seg = seg[seg.index < decided]
    tol = abs(extreme) * 1e-7
    hit = seg.index[seg.low <= extreme + tol] if long else seg.index[seg.high >= extreme - tol]
    if not len(hit):
        return None
    after = seg[seg.index > hit[-1]]
    if after.empty:
        return None
    return float(after.high.max()) if long else float(after.low.min())


def apply(mode: str, plan, bars_1m: pd.DataFrame, *, stop_buffer: float, asset: str,
          max_cost_r: float | None) -> tuple[bool, str, object]:
    """(keep the trade?, why, plan to trade) — the plan is unchanged unless a deeper limit applies."""
    if mode not in MODES:
        raise ValueError(f"range_entry must be one of {MODES}, got {mode!r}")
    long, entry, decided = plan.side == "long", plan.entry, plan.placed_at
    if mode in ("cheap_half", "eq_limit"):
        r = range_in_play(bars_1m, decided, entry)
        if r is None:
            return True, "no range in play", plan
        lo, hi, name = r
        mid = (lo + hi) / 2
        if (entry <= mid) if long else (entry >= mid):
            return True, f"entry {entry:.2f} in the cheap half of {name} {lo:.2f}-{hi:.2f}", plan
        if mode == "cheap_half":
            return False, f"entry {entry:.2f} in the expensive half of {name} {lo:.2f}-{hi:.2f} (50% {mid:.2f})", None
        new, why = mid, f"limit {entry:.2f} → 50% of {name} {lo:.2f}-{hi:.2f}: {mid:.2f}"
    else:
        extreme = plan.stop + stop_buffer if long else plan.stop - stop_buffer
        far = leg(bars_1m, decided, extreme, long)
        if far is None or ((far <= entry) if long else (far >= entry)):
            return True, "no leg beyond the entry", plan
        new = far - OTE * (far - extreme) if long else far + OTE * (extreme - far)
        if (new >= entry) if long else (new <= entry):
            return True, f"leg OTE {new:.2f} not deeper than entry {entry:.2f}", plan
        why = f"limit {entry:.2f} → leg {extreme:.2f}-{far:.2f} OTE 70.5%: {new:.2f}"
    if (new <= plan.stop) if long else (new >= plan.stop):
        return False, f"{why} is beyond the stop {plan.stop:.2f}", None
    if max_cost_r is not None:
        c = cost_at(asset, new, decided) / abs(new - plan.stop)
        if c > max_cost_r:
            return False, f"{why}: cost {c:.2f}R > {max_cost_r:g}R", None
    return True, why, replace(plan, entry=new)
