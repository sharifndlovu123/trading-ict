"""Run a model over days — stages 4→8 glued together.

One open order/trade at a time; after ``max_trades`` filled trades the rest of
the setups in the same scope are logged with a failed ``cap`` gate. Scope
"window" (default: ``max_trades`` per time window — each killzone is judged on its
own, as the leaderboard ranks per time bucket) or "day" (ruling #1: one trade per
day — the Silver Bullet rule).
A newer setup cancels a pending order that has not filled by its decision time.
Scheduled news (``params.news_blackout`` / ``params.fomc_day``, off by default) blocks a setup
with a failed ``news`` gate before it is placed — one rule for every model.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.context import build_context
from ict_engine.data.instruments import cost_at
from ict_engine.models import model_2022
from ict_engine.news import calendar as news_cal
from ict_engine.models.registry import module_for
from ict_engine.models.base import Gate, Result, Setup
from ict_engine.sim.simulate import simulate

NY = "America/New_York"


def manage(plan, params):
    """Attach the model's trade management (partial at TP1, runner stop) to a frozen plan."""
    if plan is None:
        return None
    runner_stop = getattr(params, "runner_stop", "entry")
    until = None
    if runner_stop.startswith("trail_"):                     # the trailed runner rides to the session close
        from ict_engine.models.targets import session_close
        until = session_close(plan.placed_at.date())
    return replace(plan, partial_frac=getattr(params, "partial_frac", 0.5), runner_stop=runner_stop, runner_until=until)


def run_day(bars_1m: pd.DataFrame, day: date, asset: str, params=model_2022.Params(),
            max_trades: int = 1, cap_scope: str | None = None, ctx=None) -> list[Setup]:
    cap_scope = cap_scope or getattr(params, "cap_scope", "window")      # a model may define its own (SB: day)
    if cap_scope not in ("day", "window"):
        raise ValueError(f"cap_scope must be 'day' or 'window', not {cap_scope!r}")
    if ctx is None:
        try:
            ctx = build_context(bars_1m, day)
        except ValueError:
            return []
    setups = sorted(module_for(params).find_setups(bars_1m, day, asset, params, ctx), key=lambda s: s.decided_at)
    close = pd.Timestamp(datetime.combine(day, time(16)), tz=NY)
    busy_until, filled, prev = None, {}, None
    counter = getattr(params, "counter_after", None)
    tp1_hits: list[tuple[str, pd.Timestamp]] = []      # (side, when TP1 traded) of today's filled trades
    for s in setups:
        if s.plan is None and counter and s.would_plan is not None:
            admit_counter(s, counter, bars_1m, ctx, tp1_hits)
        if s.plan is None:
            continue
        why = news_cal.news_block(s.decided_at, getattr(params, "news_blackout", None),
                                  getattr(params, "fomc_day", "trade"))
        if why:
            s.gates.append(Gate("news", False, why))
            s.plan = None
            continue
        gate = getattr(params, "entry_gate", None)
        if gate:
            from ict_engine.models import entry_quality
            ok, why = entry_quality.check(s, bars_1m, ctx, gate)
            s.gates.append(Gate("entry_quality", ok, why))
            if not ok:
                s.plan = None
                continue
        rmode = getattr(params, "range_entry", None)
        if rmode:
            from ict_engine.models import range_entry
            ok, why, plan = range_entry.apply(rmode, s.plan, bars_1m, stop_buffer=getattr(params, "stop_buffer", 0.0),
                                              asset=asset, max_cost_r=getattr(params, "max_cost_r", None))
            s.gates.append(Gate("range", ok, why))
            if not ok:
                s.plan = None
                continue
            s.plan = plan
        stf = getattr(params, "stop_tf", None)
        if stf:
            from ict_engine.models import htf_stop
            ok, why, plan = htf_stop.apply(stf, s.plan, bars_1m, ctx, stop_buffer=getattr(params, "stop_buffer", 0.0),
                                           asset=asset, max_cost_r=getattr(params, "max_cost_r", None))
            s.gates.append(Gate("stop_tf", ok, why))
            if not ok:
                s.plan = None
                continue
            s.plan = plan
        scope = "day" if cap_scope == "day" else (s.tags.get("window") or "day")
        # A newer setup replaces a pending order that has not filled yet (stale limit is cancelled).
        if prev is not None and s.decided_at < busy_until and (
                prev.result.filled_at is None or prev.result.filled_at > s.decided_at):
            if prev.result.filled_at is not None:
                filled[prev_scope] -= 1
            prev.result = Result(exit_at=s.decided_at, exit_reason="cancelled")
            busy_until = None
        if filled.get(scope, 0) >= max_trades:
            label = "daily cap" if scope == "day" else f"{scope} cap"
            s.gates.append(Gate("cap", False, f"{label} {max_trades} reached"))
            s.plan = None
            continue
        if busy_until is not None and s.decided_at < busy_until:
            s.gates.append(Gate("cap", False, "previous trade still open"))
            s.plan = None
            continue
        s.plan = manage(s.plan, params)
        s.result = simulate(s.plan, bars_1m, close, cost=cost_at(asset, s.plan.entry, s.plan.placed_at))
        busy_until = s.result.exit_at or s.plan.expires_at
        prev, prev_scope = s, scope
        if s.result.filled_at is not None:
            filled[scope] = filled.get(scope, 0) + 1
            if s.result.vote:
                t = tp1_time(s.plan, bars_1m, s.result.filled_at)
                if t is not None:
                    tp1_hits.append((s.side, t))
    return setups


COUNTER_MODES = ("tp1", "draw")


def tp1_time(plan, bars_1m: pd.DataFrame, filled_at: pd.Timestamp) -> pd.Timestamp | None:
    """First 1m bar at or after the fill that trades to TP1."""
    seg = bars_1m[(bars_1m.index >= filled_at) & (bars_1m.index <= plan.expires_at + timedelta(hours=8))]
    hit = seg.index[seg.high >= plan.tp1] if plan.side == "long" else seg.index[seg.low <= plan.tp1]
    return hit[0] if len(hit) else None


def admit_counter(s: Setup, mode: str, bars_1m: pd.DataFrame, ctx, tp1_hits) -> None:
    """Counter-bias second trade (research/preregistered-counter-bias-2026-11-15.md): a setup whose ONLY failed gate is
    the daily bias is admitted once the day's bias-direction move is delivered — ``tp1``: a same-model trade in the bias
    direction reached TP1 before this decision; ``draw``: price traded through the previous day's level on the bias
    side (bear → below PDL, bull → above PDH) since 18:00 the evening before. Bars before the decision only."""
    if mode not in COUNTER_MODES:
        raise ValueError(f"counter_after must be one of {COUNTER_MODES}, got {mode!r}")
    failed = [i for i, g in enumerate(s.gates) if not g.passed]
    if len(failed) != 1 or s.gates[failed[0]].name != "bias":
        return
    bias_side = "short" if s.side == "long" else "long"
    if mode == "tp1":
        when = [t for side, t in tp1_hits if side == bias_side and t < s.decided_at]
        if not when:
            return
        why = f"bias-side trade reached TP1 at {when[0]:%H:%M}"
    else:
        lvl = ctx.levels.get("pdl" if bias_side == "short" else "pdh")
        if lvl is None:
            return
        start = pd.Timestamp(datetime.combine(s.day - timedelta(days=1), time(18)), tz=NY)
        seg = bars_1m[(bars_1m.index >= start) & (bars_1m.index < s.decided_at)]
        through = seg.index[seg.low < lvl] if bias_side == "short" else seg.index[seg.high > lvl]
        if not len(through):
            return
        why = f"daily draw {'PDL' if bias_side == 'short' else 'PDH'} {lvl:.2f} traded at {through[0]:%H:%M}"
    i = failed[0]
    s.gates[i] = Gate("bias", True, f"{s.gates[i].detail}; counter-bias admitted: {why}")
    s.plan = s.would_plan


def run_range(bars_1m: pd.DataFrame, start: date, end: date, asset: str, params=model_2022.Params(),
              max_trades: int = 1, cap_scope: str | None = None) -> list[Setup]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.extend(run_day(bars_1m, d, asset, params, max_trades, cap_scope))
        d += timedelta(days=1)
    return out
