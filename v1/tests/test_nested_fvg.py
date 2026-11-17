"""Nested-FVG pre-registration (research/preregistered-nested-fvg-2026-11-14.md) on hand-built candles with known
answers: the entry FVG must sit inside a live 4h FVG of the trade's direction; no entry inside a live daily FVG; TP1 at
the 50% of the 4h dealing range."""

from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from ict_engine.concepts.events import Event
from ict_engine.models import entry_quality as eq
from ict_engine.models import targets as tg
from ict_engine.models.base import Setup, TradePlan
from tests.test_model_2022 import path_bars

NY = "America/New_York"


def ts(s):
    return pd.Timestamp(s, tz=NY)


def setup(side, zone, at="2024-01-09 09:50", entry=None):
    fvg = Event("fvg", "1m", "bull" if side == "long" else "bear", ts(at), ts(at), zone[1], zone[0])
    s = Setup("m", "v", "US100", "day", date(2024, 1, 9), side, ts(at), {"fvg": fvg})
    if entry is not None:
        long = side == "long"
        s.plan = TradePlan(side, ts(at), ts(at), entry, entry - 1 if long else entry + 1, entry + 2 if long else entry - 2,
                           entry + 3 if long else entry - 3)
    return s


def four_hour_gap(break_below=False):
    """CME 4h candles: 02-06 flat 100, 06-10 rally to 110, 10-14 flat 110 → bullish 4h FVG ≈100.02-109.98 known
    13:59 on Jan 8. Then quiet at 108 into Jan 9 09:50; ``break_below``: Jan 9 05:00 trades and closes at 95."""
    pts = [("2024-01-08 02:00", 100.0), ("2024-01-08 06:00", 100.0), ("2024-01-08 10:00", 110.0),
           ("2024-01-08 14:00", 110.0), ("2024-01-08 20:00", 108.0)]
    pts += [("2024-01-09 04:30", 108.0), ("2024-01-09 05:00", 95.0), ("2024-01-09 06:00", 108.0)] if break_below else []
    pts += [("2024-01-09 09:51", 108.0)]
    return path_bars(pts, "2024-01-08 02:00", "2024-01-09 09:51")


def test_nested_4h_needs_a_live_4h_fvg_of_the_trade_direction_around_the_entry_fvg():
    bars = four_hour_gap()
    ok, why = eq.nested_4h(setup("long", (104.0, 106.0)), bars)
    assert ok and "inside 4h bull FVG" in why
    assert not eq.nested_4h(setup("long", (111.0, 113.0)), bars)[0]          # entry FVG above the 4h gap
    assert not eq.nested_4h(setup("short", (104.0, 106.0)), bars)[0]         # a short needs a bearish 4h FVG
    assert not eq.nested_4h(setup("long", (104.0, 106.0)), four_hour_gap(break_below=True))[0]   # closed through: dead


def daily_gap():
    """Trading days (18:00→17:00): Jan 3 flat 100, Jan 4 rally to 120, Jan 5 flat 120 → bullish daily FVG
    ≈100.02-119.98; then Jan 8-9 around 110 (inside it, never closing below 100.02)."""
    pts = [("2024-01-02 18:00", 100.0), ("2024-01-03 17:00", 100.0), ("2024-01-03 18:00", 100.0),
           ("2024-01-04 17:00", 120.0), ("2024-01-05 17:00", 120.0), ("2024-01-08 10:00", 110.0), ("2024-01-09 09:51", 110.0)]
    return path_bars(pts, "2024-01-02 18:00", "2024-01-09 09:51")


def test_outside_daily_fvg_blocks_an_entry_inside_a_live_daily_gap():
    bars = daily_gap()
    ok, why = eq.outside_daily_fvg(setup("long", (109.0, 110.0), entry=110.0), bars)
    assert not ok and "inside daily bull FVG" in why
    assert eq.outside_daily_fvg(setup("long", (124.0, 125.0), entry=125.0), bars)[0]


def range_day():
    """4h candles: rally to 120 (Jan 8 10:00), fall to 100 (Jan 8 22:00), back to 106 → newest 4h swing high 120,
    swing low 100, 50% = 110."""
    pts = [("2024-01-07 18:00", 105.0), ("2024-01-08 10:00", 120.0), ("2024-01-08 22:00", 100.0),
           ("2024-01-09 09:51", 106.0)]
    return path_bars(pts, "2024-01-07 18:00", "2024-01-09 09:51")


def test_range_eq_is_the_middle_of_the_newest_4h_swing_high_and_low():
    mid, lo, hi = tg.range_eq(range_day(), ts("2024-01-09 09:50"))
    assert lo == pytest.approx(100.0, abs=0.1) and hi == pytest.approx(120.0, abs=0.1) and mid == pytest.approx(110.0, abs=0.1)


def test_eq_hold_moves_tp1_to_the_range_middle_only_when_far_enough(monkeypatch):
    monkeypatch.setenv("ICT_COST_BASIS", "futures")
    ctx = SimpleNamespace(levels={}, liquidity=())
    kw = dict(stop=103.0, long=True, tp1=105.0, tp1_name="5m swing high", final=106.0, final_name="asia_high",
              bars_1m=range_day(), decided=ts("2024-01-09 09:50"), ctx=ctx, day=date(2024, 1, 9), min_tp1=1.0)
    tp1, name, final, _, t_exit = tg.apply("eq_hold", entry=104.0, **kw)
    assert tp1 == pytest.approx(110.0, abs=0.1) and name.startswith("4h range 50%") and final >= tp1
    assert t_exit == ts("2024-01-09 16:55")
    tp1, name, *_ = tg.apply("eq_hold", entry=109.5, **{**kw, "stop": 108.5, "tp1": 111.0})   # 50% only 0.5R ahead
    assert tp1 == 111.0 and name == "5m swing high"


def test_location_gates_read_no_future_bars():
    s = setup("long", (104.0, 106.0), entry=105.0)
    later = pd.concat([four_hour_gap(), path_bars([("2024-01-09 09:52", 108.0), ("2024-01-09 12:00", 90.0)],
                                                  "2024-01-09 09:52", "2024-01-09 12:00")])
    for gate in ("nested_4h", "outside_daily_fvg"):
        assert eq.check(s, four_hour_gap(), None, gate) == eq.check(s, later, None, gate)
