"""HTF-stop pre-registration (research/preregistered-htf-stop-2026-11-15.md) on hand-built cases with known answers:
the stop moves to the newest confirmed 15m/1h swing beyond the model's stop; final → nearest untaken PDH/PWH beyond
TP1; TP1 and entry keep their price; cost gate on the new risk; nothing after the decision is read."""

from types import SimpleNamespace

import pandas as pd
import pytest

from ict_engine.models import htf_stop
from ict_engine.models.base import TradePlan
from tests.test_model_2022 import path_bars

NY = "America/New_York"


def ts(s):
    return pd.Timestamp(s, tz=NY)


def zigzag():
    """1h swing lows at 95 (Jan 8 12:00) and 97 (Jan 9 04:00); price 100 at the 10:00 decision on Jan 9."""
    return path_bars([("2024-01-08 06:00", 100), ("2024-01-08 12:00", 95), ("2024-01-08 20:00", 101),
                      ("2024-01-09 04:00", 97), ("2024-01-09 08:00", 101), ("2024-01-09 10:00", 100),
                      ("2024-01-09 11:00", 90), ("2024-01-09 16:00", 100)], "2024-01-08 06:00", "2024-01-09 16:00")


def plan(stop=99.0, tp1=102.0):
    return TradePlan("long", ts("2024-01-09 10:00"), ts("2024-01-09 11:00"), 100.0, stop, tp1, 103.0, "swing", "asia")


CTX = SimpleNamespace(levels={"pdh": 101.5, "pwh": 108.0})


def test_structural_stop_is_the_newest_confirmed_swing_beyond_the_models_stop():
    b = zigzag()
    lvl = htf_stop.structural_stop(b, ts("2024-01-09 10:00"), "1h", 99.0, True)
    assert lvl == pytest.approx(96.98, abs=0.03)                         # 97 swing (newest), not 95
    assert htf_stop.structural_stop(b, ts("2024-01-09 10:00"), "1h", 96.0, True) == pytest.approx(94.98, abs=0.03)
    assert htf_stop.structural_stop(b, ts("2024-01-09 10:00"), "1h", 90.0, True) is None


def test_apply_moves_the_stop_keeps_entry_and_tp1_and_aims_the_runner_at_the_untaken_draw():
    ok, why, p = htf_stop.apply("1h", plan(), zigzag(), CTX, stop_buffer=0.25, asset="US100", max_cost_r=None)
    assert ok and p.entry == 100.0 and p.tp1 == 102.0 and p.stop == pytest.approx(96.73, abs=0.03)
    assert (p.final_target, p.final_name) == (108.0, "pwh")                     # PDH 101.5 is below TP1 → PWH
    ctx = SimpleNamespace(levels={"pdh": 104.0, "pwh": 108.0})
    assert htf_stop.apply("1h", plan(), zigzag(), ctx, stop_buffer=0.25, asset="US100", max_cost_r=None)[2].final_name == "pdh"
    taken = SimpleNamespace(levels={"pdh": 100.9})                        # traded at 08:00 → taken; no draw → final kept
    assert htf_stop.apply("1h", plan(tp1=100.5), zigzag(), taken, stop_buffer=0.25, asset="US100", max_cost_r=None)[2].final_target == 103.0


def test_unchanged_without_a_swing_and_cost_gate_on_the_new_risk():
    ok, why, p = htf_stop.apply("1h", plan(stop=90.0), zigzag(), CTX, stop_buffer=0.25, asset="US100", max_cost_r=None)
    assert ok and p == plan(stop=90.0) and "no 1h swing" in why
    with pytest.raises(ValueError):
        htf_stop.apply("4h", plan(), zigzag(), CTX, stop_buffer=0.25, asset="US100", max_cost_r=None)


def test_no_lookahead():
    b = zigzag()
    cut = b[b.index < ts("2024-01-09 10:00")]
    a = htf_stop.apply("1h", plan(), b, CTX, stop_buffer=0.25, asset="US100", max_cost_r=None)[2]
    c = htf_stop.apply("1h", plan(), cut, CTX, stop_buffer=0.25, asset="US100", max_cost_r=None)[2]
    assert a == c
