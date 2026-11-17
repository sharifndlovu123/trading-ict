"""Trailed runner (runner_stop="trail_5m", research/preregistered-timeframes-trail-2026-11-14.md) on hand-built
candles with known answers: the stop follows confirmed 5m swing lows, only finished candles count, and the runner may
ride past the trade's time exit until ``runner_until``."""

import pandas as pd
import pytest

from ict_engine.models.base import TradePlan
from ict_engine.sim.simulate import simulate
from tests.test_model_2022 import path_bars

NY = "America/New_York"


def ts(s):
    return pd.Timestamp(s, tz=NY)


def stairs(mirror=False):
    """Fill at 100 (09:05), TP1 102 hit ~09:27, then higher lows: 101.5 (09:45), 103 (10:15), top 106 (10:30), crash
    to 98 (11:00). ``mirror``: the same path reflected around 100 (a short)."""
    pts = [("2024-01-09 09:00", 101.0), ("2024-01-09 09:05", 99.9), ("2024-01-09 09:30", 102.5), ("2024-01-09 09:45", 101.5),
           ("2024-01-09 10:00", 104.0), ("2024-01-09 10:15", 103.0), ("2024-01-09 10:30", 106.0), ("2024-01-09 11:00", 98.0),
           ("2024-01-09 16:00", 98.0)]
    if mirror:
        pts = [(t, 200.0 - p) for t, p in pts]
    return path_bars(pts, "2024-01-09 09:00", "2024-01-09 16:00")


def plan(side="long", runner_stop="trail_5m", until=None, final=110.0):
    long = side == "long"
    m = (lambda x: x) if long else (lambda x: 200.0 - x)
    return TradePlan(side, ts("2024-01-09 09:00"), ts("2024-01-09 12:00"), 100.0, m(99.0), m(102.0), m(final),
                     runner_stop=runner_stop, runner_until=until)


def test_trailed_runner_exits_at_the_newest_confirmed_swing_low():
    r = simulate(plan(), stairs(), ts("2024-01-09 16:00"))
    assert r.exit_reason == "tp1" and r.r == pytest.approx(2.0)
    # 50% banked at 2R + 50% stopped at the 10:15 swing low 102.98 (2.98R)
    assert r.runner_r == pytest.approx(0.5 * 2.0 + 0.5 * 2.98, abs=0.02)
    fixed = simulate(plan(runner_stop="entry"), stairs(), ts("2024-01-09 16:00"))
    assert fixed.runner_r == pytest.approx(1.0, abs=0.02)            # today's runner: back to entry


def test_trailed_runner_mirrors_for_shorts():
    r = simulate(plan("short"), stairs(mirror=True), ts("2024-01-09 16:00"))
    assert r.runner_r == pytest.approx(0.5 * 2.0 + 0.5 * 2.98, abs=0.02)


def test_a_swing_counts_only_once_its_third_candle_has_closed():
    """Low at 09:45 (candle 09:45-09:49), crash at 09:53 inside the next candle: that swing is not confirmed yet, so
    the runner stop is still at entry (no look-ahead)."""
    pts = [("2024-01-09 09:00", 101.0), ("2024-01-09 09:05", 99.9), ("2024-01-09 09:30", 102.5), ("2024-01-09 09:45", 101.5),
           ("2024-01-09 09:50", 102.5), ("2024-01-09 09:53", 99.5), ("2024-01-09 16:00", 99.5)]
    r = simulate(plan(), path_bars(pts, "2024-01-09 09:00", "2024-01-09 16:00"), ts("2024-01-09 16:00"))
    assert r.runner_r == pytest.approx(1.0, abs=0.02)


def test_runner_rides_past_the_time_exit_until_runner_until():
    pts = [("2024-01-09 09:00", 101.0), ("2024-01-09 09:05", 99.9), ("2024-01-09 09:30", 102.5), ("2024-01-09 16:55", 110.0),
           ("2024-01-09 17:00", 110.0)]
    bars = path_bars(pts, "2024-01-09 09:00", "2024-01-09 17:00")
    r = simulate(plan(until=ts("2024-01-09 16:55")), bars, ts("2024-01-09 16:00"))
    px = float(bars.loc[ts("2024-01-09 16:55"), "open"])
    assert r.exit_reason == "tp1" and r.runner_r == pytest.approx(1.0 + 0.5 * (px - 100.0), abs=0.01)
    capped = simulate(plan(), bars, ts("2024-01-09 16:00"))             # no runner_until: out at the 16:00 time exit
    assert capped.runner_r < r.runner_r


def test_unknown_runner_stop_is_rejected():
    with pytest.raises(ValueError):
        simulate(plan(runner_stop="trail_7m_banana"), stairs(), ts("2024-01-09 16:00"))
