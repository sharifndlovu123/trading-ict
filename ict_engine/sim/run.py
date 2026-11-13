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
    return replace(plan, partial_frac=getattr(params, "partial_frac", 0.5),
                   runner_stop=getattr(params, "runner_stop", "entry"))


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
    for s in setups:
        if s.plan is None:
            continue
        why = news_cal.news_block(s.decided_at, getattr(params, "news_blackout", None),
                                  getattr(params, "fomc_day", "trade"))
        if why:
            s.gates.append(Gate("news", False, why))
            s.plan = None
            continue
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
    return setups


def run_range(bars_1m: pd.DataFrame, start: date, end: date, asset: str, params=model_2022.Params(),
              max_trades: int = 1, cap_scope: str | None = None) -> list[Setup]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.extend(run_day(bars_1m, d, asset, params, max_trades, cap_scope))
        d += timedelta(days=1)
    return out
