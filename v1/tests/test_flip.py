"""The flip after a failed trade (ict_engine.eval.flip) on hand-built candles with known answers."""

from datetime import date
from types import SimpleNamespace

import pandas as pd

from ict_engine.concepts.events import Event
from ict_engine.eval import flip as fl
from ict_engine.models.base import Result, Setup, TradePlan
from ict_engine.sim.simulate import simulate
from tests.test_model_2022 import path_bars

NY = "America/New_York"
DAY = date(2024, 1, 9)
CTX = SimpleNamespace(levels={"pdh": 120.0, "pdl": 90.0, "asia_high": 110.0, "asia_low": 97.0})
PARAMS = SimpleNamespace(max_cost_r=None, partial_frac=0.5, runner_stop="entry")


def t(hm):
    return pd.Timestamp(f"2024-01-09 {hm}", tz=NY)


def day(close_through=True):
    """Long from the 1m bull FVG 100–102 fails: at 10:05 a candle closes at 99 (or only wicks there and closes 100.4
    when ``close_through`` is False), the stop at 98.6 is hit at 10:07, price retests 100 at 10:30 and falls to 96."""
    if close_through:
        pts = [("2024-01-09 00:00", 103.0), ("2024-01-09 09:59", 103.0), ("2024-01-09 10:04", 101.0),
               ("2024-01-09 10:05", 99.0), ("2024-01-09 10:07", 98.5), ("2024-01-09 10:30", 100.0),
               ("2024-01-09 11:00", 96.0), ("2024-01-09 16:00", 96.0)]
        return path_bars(pts, "2024-01-09 00:00", "2024-01-09 16:30")
    pts = [("2024-01-09 00:00", 103.0), ("2024-01-09 09:59", 103.0), ("2024-01-09 10:04", 101.0),
           ("2024-01-09 10:07", 100.4), ("2024-01-09 16:00", 100.4)]
    b = path_bars(pts, "2024-01-09 00:00", "2024-01-09 16:30")
    b.loc[t("10:07"), "low"] = 98.5                    # one wick to the stop; every close stays above 100
    return b


def failed_long(stop_at="10:07", reason="stop"):
    fvg = Event("fvg", "1m", "bull", t("09:50"), t("09:49"), top=102.0, bottom=100.0)
    plan = TradePlan("long", t("09:50"), t("11:00"), 102.0, 98.6, 106.0, 110.0)
    s = Setup("2022_model", "v", "US100", "day", DAY, "long", t("09:50"), {"fvg": fvg}, plan=plan)
    s.result = Result(filled_at=t("10:00"), exit_at=t(stop_at), exit_reason=reason, r=-1.0)
    return s


def test_inversion_close_is_the_first_own_tf_close_through_the_far_edge():
    fvg = failed_long().evidence["fvg"]
    assert fl.inversion_close(fvg, day(), t("10:07")) == t("10:05")
    assert fl.inversion_close(fvg, day(), t("10:04")) is None          # candles after the stop-out don't count


def test_flip_plan_is_the_opposite_trade_at_the_ifvg_with_stop_beyond_it():
    p = fl.flip_plan(failed_long(), day(), CTX, PARAMS)
    assert p.side == "short" and p.placed_at == t("10:05") and p.expires_at == t("11:35")
    assert (p.entry, p.stop) == (100.0, 102.0)
    assert p.tp1 == 97.0 and p.tp1_name.startswith("flip")            # nearest untaken liquidity ≥ 1R (Asia low)
    r = simulate(p, day(), t("16:00"))
    assert r.filled_at is not None and r.vote                          # retest at 10:30, then down through 97


def test_no_flip_without_a_close_through_or_without_a_stop_out():
    assert fl.flip_plan(failed_long(), day(close_through=False), CTX, PARAMS) is None
    assert fl.flip_plan(failed_long(reason="tp1"), day(), CTX, PARAMS) is None


def test_no_lookahead_flip_identical_without_bars_after_the_inversion():
    full = fl.flip_plan(failed_long(), day(), CTX, PARAMS)
    cut = day()
    cut = cut[cut.index <= t("10:07")]
    assert fl.flip_plan(failed_long(), cut, CTX, PARAMS) == full


def test_summary_counts_flips_and_adds_their_r_per_day():
    df = pd.DataFrame([
        {"model": "m", "day": pd.Timestamp("2024-01-09"), "kind": "model", "r": -1.0, "vote": False, "exit": "stop"},
        {"model": "m", "day": pd.Timestamp("2024-01-09"), "kind": "flip", "r": 1.0, "vote": True, "exit": "tp1"},
        {"model": "m", "day": pd.Timestamp("2024-01-10"), "kind": "model", "r": 2.0, "vote": True, "exit": "tp1"},
        {"model": "m", "day": pd.Timestamp("2024-01-10"), "kind": "flip", "r": None, "vote": None, "exit": "missed"},
    ])
    s = fl.summarize(df, pd.Timestamp("2024-01-01")).iloc[0]
    assert (s.oos_stopped, s.flips_armed, s.flips_filled) == (1, 2, 1)
    assert s.model_r_per_day == 0.5 and s.with_flips_r_per_day == 1.0


def test_failed_extreme_stop_sits_beyond_the_high_the_failed_long_made():
    b = day()
    leg_high = float(b[(b.index >= t("10:00")) & (b.index <= t("10:05"))].high.max())
    p = fl.flip_plan(failed_long(), b, CTX, PARAMS, stop_rule="failed_extreme")
    edge = fl.flip_plan(failed_long(), b, CTX, PARAMS, stop_rule="far_edge")
    assert leg_high > 102.0 and p.stop == leg_high and edge.stop == 102.0
    assert p.entry == edge.entry == 100.0 and abs(p.tp1 - p.entry) >= p.risk     # TP1 still ≥ 1R of the wider risk
    import pytest
    with pytest.raises(ValueError):
        fl.flip_plan(failed_long(), b, CTX, PARAMS, stop_rule="wick")
