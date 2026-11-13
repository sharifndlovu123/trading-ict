"""Silver Bullet on a hand-built day where the right answer is known.

Story (Tue 2024-01-09, bullish daily bias): Asia session flat at 96.5 (Asia low ≈ 96.48),
then 96.7 after midnight (Asia low untouched). 09:55 dips to 96.0 — runs the Asia low (the leg starts at a HTF array); 09:57 one
displacement candle leaves a bullish FVG *before* the 10:00 hour. The order is placed
at 10:00, filled on the 10:20 retrace, and the rally reaches the previous week's high
(110 — the draw, offering > 10 points) by 10:50.
"""

from datetime import date

import pandas as pd
import pytest

from ict_engine.models.model_sb import Params, find_setups
from ict_engine.sim import run
from tests.test_model_2022 import history, path_bars

SYNTHETIC_PRICES = True                  # conftest: no costs on the ~100-price synthetic day
NY = "America/New_York"
DAY = date(2024, 1, 9)


def sb_day(jump_at="09:57"):
    j = pd.Timestamp(f"2024-01-09 {jump_at}", tz=NY)
    pts = [("2024-01-08 18:00", 96.5), ("2024-01-08 23:59", 96.5), ("2024-01-09 00:30", 96.7),
           ("2024-01-09 09:40", 96.7), ("2024-01-09 09:55", 96.0),
           (str((j - pd.Timedelta(minutes=1)).tz_localize(None)), 96.1), (str(j.tz_localize(None)), 97.6),
           ("2024-01-09 10:05", 98.3), ("2024-01-09 10:20", 97.2), ("2024-01-09 10:50", 111.0),
           ("2024-01-09 16:00", 110.5)]
    return path_bars(pts, "2024-01-08 18:00", "2024-01-09 16:30")


def bars(**kw):
    return pd.concat([history(), sb_day(**kw)])


def planned(ss):
    return [s for s in ss if s.plan is not None]


def first_hour_fvg(ss):
    """The 09:57 setup. (The straight-line synthetic rally after 10:20 prints a FVG every minute —
    valid FVGs, but not the setup this story is about.)"""
    return [s for s in ss if s.evidence["fvg"].origin_ts < pd.Timestamp("2024-01-09 10:00", tz=NY)]


def test_finds_the_am_silver_bullet():
    ss = first_hour_fvg(planned(find_setups(bars(), DAY, "US100")))
    assert len(ss) == 1
    s = ss[0]
    assert s.model == "silver_bullet" and s.side == "long" and s.tags["window"] == "sb_am"
    assert s.decided_at == pd.Timestamp("2024-01-09 10:00", tz=NY)          # FVG known 09:58, order at the hour
    assert s.plan.expires_at == pd.Timestamp("2024-01-09 11:00", tz=NY)
    assert s.tags["poi"] == "leg ran asia_low"
    assert s.plan.stop < 96.0 < s.plan.entry < s.plan.tp1
    assert s.plan.final_name == "pwh" and s.plan.final_target == pytest.approx(110, abs=0.1)


def test_silver_bullet_wins():
    out = run.run_day(bars(), DAY, "US100", Params())
    t = [s for s in out if s.traded]
    assert len(t) == 1 and t[0].result.vote and t[0].result.filled_at >= pd.Timestamp("2024-01-09 10:00", tz=NY)
    assert t[0].evidence["fvg"].origin_ts == pd.Timestamp("2024-01-09 09:57", tz=NY)   # gap's middle (displacement) candle


def test_strict_mode_needs_the_fvg_inside_the_hour():
    strict = Params(strict_fvg_in_hour=True)
    assert not first_hour_fvg(find_setups(bars(), DAY, "US100", strict))         # 09:57 FVG not even evaluated
    late = planned(find_setups(bars(jump_at="10:02"), DAY, "US100", strict))
    assert late and late[0].evidence["fvg"].origin_ts >= pd.Timestamp("2024-01-09 10:00", tz=NY)


def test_framework_minimum_blocks_a_small_draw():
    ss = find_setups(bars(), DAY, "US100", Params(min_framework_ticks=400))    # 100 points
    assert not planned(ss) and all(any(g.name == "target" and not g.passed for g in s.gates)
                                   for s in ss if any(g.name == "target" for g in s.gates))


def test_fvg_outside_any_hour_is_ignored():
    assert not find_setups(bars(jump_at="12:30"), DAY, "US100")


def test_runner_uses_the_models_daily_cap(monkeypatch):
    assert Params().cap_scope == "day"
    out = run.run_day(bars(), DAY, "US100", Params())
    capped = [g for s in out for g in s.gates if g.name == "cap"]
    assert all("daily cap" in g.detail for g in capped)


def test_no_lookahead_plan_identical_without_future_bars():
    full = bars()
    s = first_hour_fvg(planned(find_setups(full, DAY, "US100")))[0]
    s2 = first_hour_fvg(planned(find_setups(full[full.index <= s.decided_at], DAY, "US100")))[0]
    assert s2.plan == s.plan
