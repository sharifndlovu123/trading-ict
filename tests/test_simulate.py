"""Simulator rules on hand-built bars (pipeline.md §7)."""

import pandas as pd
import pytest

from ict_engine.models.base import TradePlan
from ict_engine.sim.simulate import simulate

NY = "America/New_York"


def t(m):
    return pd.Timestamp("2024-01-09 10:00", tz=NY) + pd.Timedelta(minutes=m)


def bars(rows):
    idx = pd.date_range(t(0), periods=len(rows), freq="1min")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)


PLAN = TradePlan("long", placed_at=t(0), expires_at=t(30), entry=100, stop=98, tp1=104, final_target=108)
CLOSE = t(60)


def test_fill_then_tp1_is_a_vote():
    b = bars([(101, 101, 101, 101), (101, 101, 99.5, 100.5), (100.5, 102, 100, 101.8), (102, 104.5, 101.5, 104)])
    r = simulate(PLAN, b, CLOSE)
    assert r.filled_at == t(1) and r.exit_reason == "tp1" and r.vote and r.r == pytest.approx(2.0)


def test_stop_and_tp1_in_same_bar_counts_stop_and_flags():
    b = bars([(101, 101, 101, 101), (101, 101, 99.5, 100.5), (100.5, 105, 97, 101)])
    r = simulate(PLAN, b, CLOSE)
    assert r.exit_reason == "stop" and not r.vote and r.ambiguous and r.r == -1.0


def test_fill_bar_that_also_hits_stop_is_a_loss():
    b = bars([(101, 101, 101, 101), (101, 101, 97.5, 98)])
    r = simulate(PLAN, b, CLOSE)
    assert r.filled_at == t(1) and r.exit_reason == "stop"


def test_tp1_before_fill_is_missed_not_a_trade():
    b = bars([(101, 101, 101, 101), (101, 104.5, 101, 104)])
    r = simulate(PLAN, b, CLOSE)
    assert r.filled_at is None and r.exit_reason == "missed"


def test_order_expires_at_window_end():
    plan = TradePlan("long", t(0), t(2), 100, 98, 104, 108)
    b = bars([(101, 101, 101, 101)] * 3 + [(101, 101, 99, 100)])     # would fill at t(3), after expiry
    assert simulate(plan, b, CLOSE).exit_reason == "not_filled"


def test_time_exit_at_close_uses_open_of_close_bar():
    b = bars([(101, 101, 101, 101), (101, 101, 99.5, 100.5), (100.5, 101, 100, 101), (101, 101, 101, 101)])
    r = simulate(PLAN, b, close := t(3))
    assert r.exit_reason == "time_exit" and r.r == pytest.approx(0.5) and not r.vote


def test_costs_are_charged_in_r():
    b = bars([(101, 101, 101, 101), (101, 101, 99.5, 100.5), (102, 104.5, 101.5, 104)])
    assert simulate(PLAN, b, CLOSE, cost=0.5).r == pytest.approx(2.0 - 0.25)


def test_runner_reaches_final_or_returns_to_entry():
    win = bars([(101, 101, 101, 101), (101, 101, 99.5, 100.5), (102, 104.5, 101.5, 104), (104, 108.5, 103, 108)])
    r = simulate(PLAN, win, CLOSE)
    assert r.final_reached and r.runner_r == pytest.approx(0.5 * 2 + 0.5 * 4)
    back = bars([(101, 101, 101, 101), (101, 101, 99.5, 100.5), (102, 104.5, 101.5, 104), (104, 104, 99.8, 100)])
    r = simulate(PLAN, back, CLOSE)
    assert r.final_reached is False and r.runner_r == pytest.approx(1.0)


def test_short_mirror():
    plan = TradePlan("short", t(0), t(30), entry=100, stop=102, tp1=96, final_target=92)
    b = bars([(99, 99, 99, 99), (99, 100.5, 99, 99.5), (99.5, 99.8, 95.5, 96)])
    r = simulate(plan, b, CLOSE)
    assert r.vote and r.r == pytest.approx(2.0)


def test_no_lookahead_bars_before_placement_are_ignored():
    plan = TradePlan("long", t(2), t(30), 100, 98, 104, 108)
    b = bars([(101, 101, 97, 99), (99, 105, 99, 104), (101, 101, 101, 101), (101, 101, 99.5, 100)])
    r = simulate(plan, b, CLOSE)
    assert r.filled_at == t(3)


def test_arm_level_order_goes_live_only_after_price_trades_there():
    plan = TradePlan("long", t(0), t(30), entry=100, stop=98, tp1=104, final_target=108, arm=102)
    # bar 1 dips to entry before arming → ignored; bar 2 arms; bar 3 fills; bar 4 TP1
    b = bars([(101, 101, 101, 101), (101, 101, 99.5, 100.5), (100.5, 102.2, 100.4, 102), (102, 102, 99.8, 100.2),
              (100.2, 104.5, 100, 104)])
    r = simulate(plan, b, CLOSE)
    assert r.filled_at == t(3) and r.vote


def test_tp1_before_arming_is_missed():
    plan = TradePlan("long", t(0), t(30), entry=100, stop=98, tp1=101.5, final_target=108, arm=102)
    b = bars([(101, 101, 101, 101), (101, 101.8, 100.5, 101.7)])
    assert simulate(plan, b, CLOSE).exit_reason == "missed"
