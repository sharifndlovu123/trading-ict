"""Intraday structure and distance facts (ict_engine.concepts.momentum) and the recipe gates on the PD-array-return
model (off by default): known answers on hand-built inputs, completed candles only."""
from dataclasses import replace

import pandas as pd
import pytest

from ict_engine.concepts import momentum as mo
from ict_engine.models import model_pd_return as pr

NY = "America/New_York"


def test_side_vs_structure_truth_table():
    assert mo.side_vs_structure({"1h": "bull", "4h": "bull"}, True) == "with"
    assert mo.side_vs_structure({"1h": "bull", "4h": "bull"}, False) == "against"
    assert mo.side_vs_structure({"1h": "bull", "4h": "bear"}, True) == "split"
    assert mo.side_vs_structure({"1h": "neutral", "4h": "bear"}, True) == "split"      # neutral is never "against"
    assert mo.side_vs_structure({"1h": "bear", "4h": "bear"}, False) == "with"


def test_distance_from_the_area():
    assert mo.dist_from_area(105, 100, 110) == 0
    assert mo.dist_from_area(95, 100, 110) == 5 and mo.dist_from_area(113, 100, 110) == 3


def trend(up: bool, days=30):
    """1m bars in a trend with small swings inside bigger ones, so the hourly has intermediate-term highs and lows to
    break (the structure rule needs them: a clean staircase has none)."""
    idx = pd.date_range("2024-01-02 00:00", periods=days * 24 * 60, freq="1min", tz=NY)
    idx = idx[idx.dayofweek < 5]
    hours = pd.Series(range(len(idx)), index=idx, dtype=float) / 60
    small = ((hours % 8) - 4).abs() * 6                          # an 8-hour zig-zag, 24 points
    big = ((hours % 56) - 28).abs() * 5                          # a 56-hour zig-zag, 140 points
    px = 5000 + (1 if up else -1) * hours * 4 + small + big
    return pd.DataFrame({"open": px, "high": px + 0.5, "low": px - 0.5, "close": px}, index=idx)


def test_tf_state_follows_the_trend_and_ignores_the_future():
    up, down = trend(True), trend(False)
    at = pd.Timestamp("2024-01-26 10:17", tz=NY)
    assert mo.tf_state(up, at, "1h") == "bull" and mo.tf_state(up, at, "4h") == "bull"
    assert mo.tf_state(down, at, "1h") == "bear"
    crash = up.copy()
    crash.loc[crash.index >= at, ["open", "high", "low", "close"]] = 1.0     # the future collapses
    assert mo.tf_state(crash, at, "1h") == "bull"
    forming = up.copy()
    forming.loc[(forming.index >= at.floor("1h")) & (forming.index < at), ["low", "close"]] = 1.0   # the forming hour
    assert mo.tf_state(forming, at, "1h") == "bull"                          # a candle still forming is not used


def test_adr_uses_completed_days_only():
    b = trend(True)
    at = pd.Timestamp("2024-01-26 10:17", tz=NY)
    a = mo.adr(b, at)
    spike = b.copy()
    spike.loc[spike.index >= at.normalize(), "high"] += 5000                  # today's range explodes
    assert a and a > 0 and mo.adr(spike, at) == pytest.approx(a)


def test_recipe_gates_are_off_by_default_and_labelled():
    p = pr.Params()
    assert p.structure_gate is None and p.max_entry_dist_adr is None and p.last_entry is None
    q = replace(p, structure_gate="not_against", max_entry_dist_adr=0.25, last_entry="14:00")
    for word in ("structure_gate=not_against", "max_entry_dist_adr=0.25", "last_entry=14:00"):
        assert word in q.variant
    assert "structure_gate" not in p.variant
    assert pr.recipe_gates(q, long=True, decided=pd.Timestamp("2024-01-26 14:30", tz=NY), entry=100, area=(99, 101),
                           states={"1h": "bull", "4h": "bull"}, adr=10)[0].passed is False        # after 14:00
    ok = pr.recipe_gates(q, long=True, decided=pd.Timestamp("2024-01-26 10:30", tz=NY), entry=100, area=(99, 101),
                         states={"1h": "bull", "4h": "bear"}, adr=10)
    assert all(g.passed for g in ok)                                           # split is not "against"
    bad = pr.recipe_gates(q, long=True, decided=pd.Timestamp("2024-01-26 10:30", tz=NY), entry=104, area=(99, 101),
                          states={"1h": "bear", "4h": "bear"}, adr=10)
    assert [g.name for g in bad if not g.passed] == ["structure", "location"]  # against both; 0.3 ADR from the area
    strict = replace(q, structure_gate="with")
    assert not all(g.passed for g in pr.recipe_gates(strict, long=True, decided=pd.Timestamp("2024-01-26 10:30", tz=NY),
                                                     entry=100, area=(99, 101), states={"1h": "bull", "4h": "bear"}, adr=10))
    with pytest.raises(ValueError):
        pr.recipe_gates(replace(q, structure_gate="nope"), long=True, decided=pd.Timestamp("2024-01-26 10:30", tz=NY),
                        entry=100, area=(99, 101), states={}, adr=10)
