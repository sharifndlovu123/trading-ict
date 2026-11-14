"""Target modes (models/targets.py), the session-close exit (simulate) and the entry-quality gates
(models/entry_quality.py) on hand-built candles with known answers."""

from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from ict_engine.concepts.events import Event, Level
from ict_engine.models import entry_quality as eq
from ict_engine.models import targets as tg
from ict_engine.models.base import Setup, TradePlan
from ict_engine.sim.simulate import simulate
from tests.test_model_2022 import path_bars

NY = "America/New_York"


def ts(s):
    return pd.Timestamp(s, tz=NY)


def drop_day(rally=False):
    """08:00 1h candle flat at 110, 09:00 drop to 104, 10:00 flat 104, 13:00–15:00 down to 100 → two bearish 1h FVGs
    above (≈104.02–109.98 and ≈102.02–103.98). ``rally``: price trades up to 111 the next morning (both filled)."""
    pts = [("2024-01-08 00:00", 110.0), ("2024-01-08 09:00", 110.0), ("2024-01-08 10:00", 104.0),
           ("2024-01-08 13:00", 104.0), ("2024-01-08 15:00", 100.0), ("2024-01-09 06:00", 100.0)]
    if rally:
        pts += [("2024-01-09 07:00", 111.0), ("2024-01-09 08:00", 100.0)]
    pts += [("2024-01-09 10:00", 100.0)]
    return path_bars(pts, "2024-01-08 00:00", "2024-01-09 10:01")


CTX = SimpleNamespace(levels={"pdh": 108.0, "pwh": 115.0, "pdl": 90.0, "pwl": 85.0}, liquidity=())


def test_fvg_draws_are_unfilled_opposite_gaps_ahead_near_edge_first():
    d = ts("2024-01-09 10:00")
    got = sorted(px for px, _ in tg.fvg_draws(drop_day(), d, ("1h",), long=True, entry=100.0))
    # the two designed gaps are there (the straight-line ramps leave two more small ones, also real and unfilled)
    assert any(abs(g - 102.02) < 0.05 for g in got) and any(abs(g - 104.02) < 0.05 for g in got)
    assert all(g > 100.0 for g in got)
    after_rally = [px for px, _ in tg.fvg_draws(drop_day(rally=True), d, ("1h",), long=True, entry=100.0)]
    assert not any(abs(g - 102.02) < 0.05 or abs(g - 104.02) < 0.05 for g in after_rally)   # traded through: filled
    assert tg.fvg_draws(drop_day(), d, ("1h",), long=False, entry=100.0) == []               # short: none below


def test_apply_modes_fvg_tp1_and_hold_and_default_and_bad_mode(monkeypatch):
    kw = dict(entry=100.0, stop=99.0, long=True, tp1=105.0, tp1_name="5m swing high", final=106.0, final_name="asia_high",
              bars_1m=drop_day(), decided=ts("2024-01-09 10:00"), ctx=CTX, day=date(2024, 1, 9), min_tp1=1.0)
    assert tg.apply("default", **kw) == (105.0, "5m swing high", 106.0, "asia_high", None)
    tp1, name, final, _, t_exit = tg.apply("fvg_tp1", **kw)
    assert abs(tp1 - 102.02) < 0.05 and name == "1h FVG" and final == 106.0 and t_exit is None
    monkeypatch.setenv("ICT_COST_BASIS", "futures")
    tp1, _, final, fname, t_exit = tg.apply("hold", **kw)
    assert tp1 == 105.0 and final >= 103.0 and t_exit == ts("2024-01-09 16:55")
    monkeypatch.setenv("ICT_COST_BASIS", "cfd")
    assert tg.apply("hold", **kw)[4] == ts("2024-01-09 16:10")
    with pytest.raises(ValueError):
        tg.apply("far", **kw)


def test_session_close_exit_uses_the_last_bar_when_the_market_halted_early():
    """A CFD index halts 16:15: a 16:55 exit must close at the 16:14 bar, not at the next session's 18:00 open."""
    day = path_bars([("2024-01-09 09:00", 100.0), ("2024-01-09 16:14", 103.0)], "2024-01-09 09:00", "2024-01-09 16:15")
    nxt = path_bars([("2024-01-09 18:00", 200.0), ("2024-01-09 19:00", 200.0)], "2024-01-09 18:00", "2024-01-09 19:00")
    bars = pd.concat([day, nxt])
    plan = TradePlan("long", ts("2024-01-09 09:00"), ts("2024-01-09 09:30"), 100.05, 90.0, 120.0, 130.0,
                     time_exit=ts("2024-01-09 16:55"))
    r = simulate(plan, bars, ts("2024-01-09 16:00"))
    assert r.exit_reason == "time_exit" and r.exit_at == ts("2024-01-09 16:14")
    assert abs(r.r - (103.0 - 100.05) / (100.05 - 90.0)) < 0.01


def _setup(side="long", zone=(100.0, 101.0), at="2024-01-09 09:50"):
    fvg = Event("fvg", "1m", "bull" if side == "long" else "bear", ts(at), ts(at), zone[1], zone[0])
    return Setup("m", "v", "US100", "day", date(2024, 1, 9), side, ts(at), {"fvg": fvg})


def test_no_chop_counts_5m_candles_inside_the_zone():
    inside = path_bars([("2024-01-09 08:00", 100.5), ("2024-01-09 09:50", 100.6)], "2024-01-09 08:00", "2024-01-09 09:51")
    away = path_bars([("2024-01-09 08:00", 104.0), ("2024-01-09 09:50", 104.1)], "2024-01-09 08:00", "2024-01-09 09:51")
    ok, why = eq.no_chop(_setup(), ts("2024-01-09 09:50"), inside)
    assert not ok and why.startswith("12 of the last 12")
    assert eq.no_chop(_setup(), ts("2024-01-09 09:50"), away)[0]


def sweep_day(sweep=True):
    """Quiet at 97 from 03:00, a quick stab at 09:20 (below the 95 PDL when ``sweep``, else only to 95.5) closed back
    above within 3 one-minute bars (else the engine calls it a run), then a sharp 5m rally 09:40–09:45 to 98."""
    low = 94.5 if sweep else 95.5
    pts = [("2024-01-09 03:00", 97.0), ("2024-01-09 09:00", 97.0), ("2024-01-09 09:19", 95.6), ("2024-01-09 09:20", low),
           ("2024-01-09 09:21", 95.5), ("2024-01-09 09:23", 95.6),
           ("2024-01-09 09:40", 95.6), ("2024-01-09 09:45", 98.0), ("2024-01-09 09:50", 97.9)]
    return path_bars(pts, "2024-01-09 03:00", "2024-01-09 09:51")


def test_sweep_then_displacement_needs_both_in_order():
    ctx = SimpleNamespace(liquidity=(Level("pdl", 95.0, "low", ts("2024-01-09 03:00")),))
    ok, why = eq.sweep_then_displacement(True, ts("2024-01-09 09:50"), sweep_day(), ctx)
    assert ok and "pdl" in why
    ok, why = eq.sweep_then_displacement(True, ts("2024-01-09 09:50"), sweep_day(sweep=False), ctx)
    assert not ok and why.startswith("no sweep")
    assert not eq.sweep_then_displacement(False, ts("2024-01-09 09:50"), sweep_day(), ctx)[0]     # short: wrong side


def test_entry_gates_read_no_future_bars_and_reject_unknown_gate():
    ctx = SimpleNamespace(liquidity=(Level("pdl", 95.0, "low", ts("2024-01-09 03:00")),))
    s = _setup(zone=(95.0, 95.5))
    later = pd.concat([sweep_day(), path_bars([("2024-01-09 09:51", 97.9), ("2024-01-09 12:00", 80.0)],
                                              "2024-01-09 09:51", "2024-01-09 12:00")])
    assert eq.check(s, sweep_day(), ctx, "both") == eq.check(s, later, ctx, "both")
    with pytest.raises(ValueError):
        eq.check(s, sweep_day(), ctx, "patience")
