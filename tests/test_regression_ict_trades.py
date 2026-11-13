"""Regression: the concept layer must see what ICT saw on his live executions.

Uses real Dukascopy data (skipped until fetched). Prices on ICT's chart are
futures; they are mapped onto the CFD feed with the case's anchors.
"""

from datetime import date, timedelta

import pandas as pd
import pytest

from ict_engine.concepts.clock import active
from ict_engine.concepts.context import build_context
from ict_engine.concepts.events import fvgs, gap_lifecycle, structure, sweeps, swing_levels, swings
from ict_engine.eval import load_cases
from ict_engine.eval.basis import estimate_offset

NY = "America/New_York"
CASES = {c.id: c for c in load_cases("tests/cases/ict_live_exec.yaml")}


def ny(s):
    return pd.Timestamp(s, tz=NY)


def _bars(day: date):
    from ict_engine.data.dukascopy import load
    try:
        return load("US100", max(day - timedelta(days=70), date(2023, 11, 1)), day)
    except FileNotFoundError:
        pytest.skip("Dukascopy data not downloaded")


@pytest.fixture(scope="module")
def jan9():
    case = CASES["2024-01-09-nq-macro-pdh"]
    bars = _bars(case.trade.day)
    off = estimate_offset(bars, case.trade.day, list(case.anchors))
    day = bars[(bars.index >= ny("2024-01-09 00:00")) & (bars.index < ny("2024-01-09 16:00"))]
    return case, build_context(bars, case.trade.day), day.assign(close_ts=day.index), off.value


def test_jan9_bias_is_bullish(jan9):
    _, ctx, _, _ = jan9
    assert ctx.bias == "bull"


def test_jan9_entry_is_inside_the_macro(jan9):
    case, *_ = jan9
    assert "macro_1050" in active(ny("2024-01-09 11:04"), "futures")


def test_jan9_sellside_taken_then_bullish_mss_before_entry(jan9):
    _, _, day, _ = jan9
    sw = swings(day, "1m")
    taken = [e for e in sweeps(day, swing_levels(sw), until=ny("2024-01-09 11:01"))
             if e.meta["level"].startswith("1m_swing_low") and e.origin_ts >= ny("2024-01-09 10:45")]
    assert taken, "no sell-side taken in 10:45–11:01"
    mss = [e for e in structure(day, "1m", sw)
           if e.kind == "mss" and e.direction == "bull" and ny("2024-01-09 10:50") <= e.origin_ts <= ny("2024-01-09 11:04")]
    assert mss, "no bullish MSS inside the macro before the entry"


def test_jan9_displacement_fvg_contains_icts_shifted_entry(jan9):
    case, _, day, off = jan9
    entry = case.trade.entry_price + off
    t = ny("2024-01-09 11:04")
    hits = [g for g in fvgs(day, "1m")
            if g.direction == "bull" and g.meta["displacement"] and ny("2024-01-09 10:50") <= g.origin_ts < t
            and g.bottom - 1 <= entry <= g.top + 1 and gap_lifecycle(g, day, until=t).valid_at(t)]
    assert hits, f"no valid bullish displacement FVG around shifted entry {entry:.2f}"


def test_jan9_buyside_targets_are_run_after_entry(jan9):
    _, ctx, day, _ = jan9
    runs = {e.meta["level"] for e in sweeps(day, ctx.liquidity) if e.origin_ts > ny("2024-01-09 11:04")
            and e.direction == "bull"}
    assert {"asia_high", "pdh"} <= runs
