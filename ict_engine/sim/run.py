"""Run a model over days — stages 4→8 glued together.

One open order/trade at a time; after ``max_trades`` filled trades the rest of
the day's setups are logged with a failed ``cap`` gate (ruling #1: one trade
per day by default).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.context import build_context
from ict_engine.models import model_2022
from ict_engine.models.base import Gate, Setup
from ict_engine.sim.simulate import simulate

NY = "America/New_York"
COST = {"US100": 1.0, "US500": 0.5, "US30": 2.0}     # round-trip spread + slippage, price units (v1 guess)


def run_day(bars_1m: pd.DataFrame, day: date, asset: str, params=model_2022.Params(),
            max_trades: int = 1) -> list[Setup]:
    try:
        ctx = build_context(bars_1m, day)
    except ValueError:
        return []
    setups = sorted(model_2022.find_setups(bars_1m, day, asset, params, ctx), key=lambda s: s.decided_at)
    close = pd.Timestamp(datetime.combine(day, time(16)), tz=NY)
    busy_until, filled = None, 0
    for s in setups:
        if s.plan is None:
            continue
        if filled >= max_trades:
            s.gates.append(Gate("cap", False, f"daily cap {max_trades} reached"))
            s.plan = None
            continue
        if busy_until is not None and s.decided_at < busy_until:
            s.gates.append(Gate("cap", False, "previous order/trade still active"))
            s.plan = None
            continue
        s.result = simulate(s.plan, bars_1m, close, cost=COST.get(asset, 0.0))
        busy_until = s.result.exit_at or s.plan.expires_at
        if s.result.filled_at is not None:
            filled += 1
    return setups


def run_range(bars_1m: pd.DataFrame, start: date, end: date, asset: str, params=model_2022.Params(),
              max_trades: int = 1) -> list[Setup]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.extend(run_day(bars_1m, d, asset, params, max_trades))
        d += timedelta(days=1)
    return out
