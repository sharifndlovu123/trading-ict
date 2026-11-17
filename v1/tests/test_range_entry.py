"""Range-in-play pre-registration (research/preregistered-range-in-play-2026-11-14.md) on hand-built candles with
known answers: the 1h dealing range whose swings took liquidity, the cheap/expensive half gate, the 50% limit, the leg
OTE limit, and no look-ahead."""

from datetime import date

import pandas as pd
import pytest

from ict_engine.models import range_entry as re_
from ict_engine.models.base import TradePlan
from tests.test_model_2022 import path_bars

NY = "America/New_York"
DEC = pd.Timestamp("2024-01-09 09:50", tz=NY)


def ts(s):
    return pd.Timestamp(s, tz=NY)


def plan(side, entry, stop, tp1=None):
    long = side == "long"
    tp1 = tp1 if tp1 is not None else (entry + 20 if long else entry - 20)
    return TradePlan(side, DEC, ts("2024-01-09 11:00"), entry, stop, tp1, tp1 + (5 if long else -5))


def zigzag():
    """1h swings: high 110 (Jan 8 05:00), low 102 (08:00), high 115 (11:00, above 110 → took buyside),
    low 98 (14:00, below 102 → took sellside), then chop with lower highs and higher lows (overlapping 4h candles, so
    no 4h FVG) to 106 by Jan 9 09:50 → range 98-115, 50% = 106.5."""
    pts = [("2024-01-08 02:00", 100.0), ("2024-01-08 05:00", 110.0), ("2024-01-08 08:00", 102.0),
           ("2024-01-08 11:00", 115.0), ("2024-01-08 14:00", 98.0), ("2024-01-08 18:00", 107.0),
           ("2024-01-08 22:00", 103.0), ("2024-01-09 02:00", 106.5), ("2024-01-09 06:00", 103.5),
           ("2024-01-09 09:51", 106.0)]
    return path_bars(pts, "2024-01-08 02:00", "2024-01-09 09:51")


def test_dealing_range_uses_the_newest_swings_that_took_liquidity():
    lo, hi = re_.dealing_range_1h(zigzag(), DEC)
    assert lo == pytest.approx(98.0, abs=0.1) and hi == pytest.approx(115.0, abs=0.1)
    lo2, hi2, name = re_.range_in_play(zigzag(), DEC, 104.0)
    assert name == "1h dealing range" and (lo2, hi2) == (lo, hi)
    assert re_.range_in_play(zigzag(), DEC, 120.0) is None             # price outside the range: none in play


def kw():
    return dict(stop_buffer=0.25, asset="US100", max_cost_r=None)


def test_cheap_half_keeps_discount_longs_and_premium_shorts_only():
    bars = zigzag()
    ok, why, p = re_.apply("cheap_half", plan("long", 104.0, 97.0), bars, **kw())
    assert ok and p.entry == 104.0 and "cheap half" in why
    ok, why, p = re_.apply("cheap_half", plan("long", 110.0, 97.0), bars, **kw())
    assert not ok and p is None and "expensive half" in why
    assert re_.apply("cheap_half", plan("short", 110.0, 116.0), bars, **kw())[0]
    assert not re_.apply("cheap_half", plan("short", 104.0, 116.0), bars, **kw())[0]
    ok, why, p = re_.apply("cheap_half", plan("long", 120.0, 117.0), bars, **kw())   # no range in play: unchanged
    assert ok and why == "no range in play" and p.entry == 120.0


def test_eq_limit_moves_an_expensive_entry_to_the_range_middle_unless_beyond_the_stop():
    bars = zigzag()
    ok, why, p = re_.apply("eq_limit", plan("long", 110.0, 100.0), bars, **kw())
    assert ok and p.entry == pytest.approx(106.5, abs=0.1) and p.stop == 100.0 and p.tp1 == 130.0
    ok, why, p = re_.apply("eq_limit", plan("long", 110.0, 107.0), bars, **kw())
    assert not ok and "beyond the stop" in why


def sweep_leg():
    """Jan 9: 105 at 09:00, swept to 100 at 09:20, rallied to 110 at 09:40, 108 at 09:50."""
    return path_bars([("2024-01-09 09:00", 105.0), ("2024-01-09 09:20", 100.0), ("2024-01-09 09:40", 110.0),
                      ("2024-01-09 09:51", 108.0)], "2024-01-09 09:00", "2024-01-09 09:51")


def test_leg_ote_moves_the_limit_to_70_5_percent_of_extreme_to_leg_high():
    bars = sweep_leg()
    far = re_.leg(bars, DEC, 100.0, True)
    assert far == pytest.approx(110.0, abs=0.05)
    ok, why, p = re_.apply("leg_ote", plan("long", 107.0, 99.75), bars, **kw())
    assert ok and p.entry == pytest.approx(far - 0.705 * (far - 100.0), abs=1e-9) and p.entry == pytest.approx(102.95, abs=0.05)
    ok, why, p = re_.apply("leg_ote", plan("long", 102.0, 99.75), bars, **kw())       # already deeper: unchanged
    assert ok and p.entry == 102.0 and "not deeper" in why


def test_cost_gate_applies_to_the_new_risk():
    ok, why, p = re_.apply("leg_ote", plan("long", 107.0, 99.75), sweep_leg(), stop_buffer=0.25, asset="US100", max_cost_r=0.01)
    assert not ok and "cost" in why


def test_no_lookahead():
    later = pd.concat([sweep_leg(), path_bars([("2024-01-09 09:51", 108.0), ("2024-01-09 10:30", 90.0), ("2024-01-09 11:00", 130.0)],
                                              "2024-01-09 09:51", "2024-01-09 11:00")])
    for mode in ("leg_ote",):
        a = re_.apply(mode, plan("long", 107.0, 99.75), sweep_leg(), **kw())
        b = re_.apply(mode, plan("long", 107.0, 99.75), later, **kw())
        assert a[:2] == b[:2] and a[2].entry == b[2].entry
    z_later = pd.concat([zigzag(), path_bars([("2024-01-09 09:51", 106.0), ("2024-01-09 12:00", 125.0)],
                                             "2024-01-09 09:51", "2024-01-09 12:00")])
    for mode in ("cheap_half", "eq_limit"):
        a = re_.apply(mode, plan("long", 110.0, 100.0), zigzag(), **kw())
        b = re_.apply(mode, plan("long", 110.0, 100.0), z_later, **kw())
        assert a[:2] == b[:2]


def test_a_live_4h_fvg_containing_the_entry_is_the_range_in_play_first():
    """A straight climb 98 → 108 over 20 hours leaves bullish 4h FVGs; the one holding the entry wins over the 1h range."""
    pts = [("2024-01-08 02:00", 100.0), ("2024-01-08 05:00", 110.0), ("2024-01-08 08:00", 102.0),
           ("2024-01-08 11:00", 115.0), ("2024-01-08 14:00", 98.0), ("2024-01-09 09:51", 108.0)]
    bars = path_bars(pts, "2024-01-08 02:00", "2024-01-09 09:51")
    lo, hi, name = re_.range_in_play(bars, DEC, 104.0)
    assert name == "4h bull FVG" and lo <= 104.0 <= hi and hi - lo < 3
