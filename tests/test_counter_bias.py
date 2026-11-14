"""Counter-bias pre-registration (research/preregistered-counter-bias-2026-11-15.md) on hand-built cases with known
answers: only a setup whose sole failed gate is the bias is admitted; ``tp1`` needs an earlier bias-side TP1, ``draw``
needs the previous day's bias-side level traded before the decision; no look-ahead."""

from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from ict_engine.models.base import Gate, Setup, TradePlan
from ict_engine.sim.run import admit_counter, tp1_time
from tests.test_model_2022 import path_bars

NY = "America/New_York"
DAY = date(2024, 1, 9)


def ts(s):
    return pd.Timestamp(s, tz=NY)


def counter_long(at="2024-01-09 11:05", extra_fail=False):
    s = Setup("m", "v", "US100", "day", DAY, "long", ts(at), {})
    s.gates = [Gate("time", True, "macro"), Gate("bias", False, "daily bias bear"),
               Gate("pricing", not extra_fail, "x")]
    s.would_plan = TradePlan("long", ts(at), ts("2024-01-09 11:10"), 100.0, 98.0, 104.0, 106.0)
    return s


CTX = SimpleNamespace(levels={"pdh": 120.0, "pdl": 95.0})


def test_tp1_mode_needs_an_earlier_bias_side_tp1():
    s = counter_long()
    admit_counter(s, "tp1", None, CTX, [("short", ts("2024-01-09 10:27"))])
    assert s.plan is s.would_plan and s.gates[1].passed and "TP1 at 10:27" in s.gates[1].detail
    late = counter_long()
    admit_counter(late, "tp1", None, CTX, [("short", ts("2024-01-09 11:30"))])      # TP1 after the decision
    assert late.plan is None
    same = counter_long()
    admit_counter(same, "tp1", None, CTX, [("long", ts("2024-01-09 10:27"))])       # not the bias side
    assert same.plan is None


def test_only_a_setup_failing_the_bias_alone_is_admitted():
    s = counter_long(extra_fail=True)
    admit_counter(s, "tp1", None, CTX, [("short", ts("2024-01-09 10:27"))])
    assert s.plan is None and not s.gates[1].passed


def day_bars(low_at=None):
    """Jan 8 18:00 → Jan 9 12:00 around 100; ``low_at``: a dip to 94 (below PDL 95) at that time."""
    pts = [("2024-01-08 18:00", 100.0)]
    if low_at:
        t = pd.Timestamp(low_at)
        pts += [((t - pd.Timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M"), 100.0), (low_at, 94.0),
                ((t + pd.Timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M"), 100.0)]
    pts += [("2024-01-09 12:00", 100.0)]
    return path_bars(pts, "2024-01-08 18:00", "2024-01-09 12:00")


def test_draw_mode_needs_the_pdl_traded_before_the_decision():
    s = counter_long()
    admit_counter(s, "draw", day_bars("2024-01-09 09:40"), CTX, [])
    assert s.plan is s.would_plan and "PDL 95.00" in s.gates[1].detail
    after = counter_long()
    admit_counter(after, "draw", day_bars("2024-01-09 11:30"), CTX, [])            # only after the decision
    assert after.plan is None
    none = counter_long()
    admit_counter(none, "draw", day_bars(), CTX, [])
    assert none.plan is None


def test_tp1_time_is_the_first_touch_after_the_fill():
    bars = path_bars([("2024-01-09 10:00", 100.0), ("2024-01-09 10:20", 104.5), ("2024-01-09 10:40", 100.0)],
                     "2024-01-09 10:00", "2024-01-09 10:40")
    p = TradePlan("long", ts("2024-01-09 10:00"), ts("2024-01-09 11:00"), 100.0, 98.0, 104.0, 106.0)
    t = tp1_time(p, bars, ts("2024-01-09 10:01"))
    assert ts("2024-01-09 10:15") <= t <= ts("2024-01-09 10:20")


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        admit_counter(counter_long(), "always", None, CTX, [])
