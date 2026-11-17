"""Re-entry v2 (research/preregistered-reentry-v2-2026-11-16.md): ``reentry_nochase`` refuses a re-entry at a worse price
than the stopped trade; ``counter_tp1`` closes a trade against the weekly trend (htf40) entirely at TP1 (a small grab)."""
from dataclasses import replace
from types import SimpleNamespace

import pandas as pd
import pytest

from ict_engine.concepts.context import BIAS_RULES, bias_htf40
from ict_engine.models import model_2022
from ict_engine.sim import run
from tests.test_reentry import LOSS, setup
from tests.test_run import DAY, frame, patched

SYNTHETIC_PRICES = True

# long fills 99 at 09:01, TP1 101 at 09:03, then runs to 104 (final) by 09:10
RUN = [("09:01", 100, 100, 98.5, 99), ("09:03", 99, 101.5, 99, 101.2), ("09:10", 101.2, 104.5, 101.2, 104.2)]


def go(monkeypatch, rows, setups, weekly="neutral", **kw):
    patched(monkeypatch, setups)
    ctx = SimpleNamespace(biases={"htf40": (weekly, "test")})
    return run.run_day(frame(rows), DAY, "US100", params=replace(model_2022.Params(), **kw), max_trades=1, ctx=ctx)


def runner_setup():
    s = setup("09:00", "long", 99, 98, 101)
    s.plan = replace(s.plan, final_target=104)
    return s


def test_nochase_refuses_a_worse_price_and_admits_a_better_one(monkeypatch):
    # first long filled 99, stopped. A long re-entry at 99.5 chases (worse); at 97 it is better.
    out = go(monkeypatch, LOSS, [setup("09:00", "long", 99, 98, 101), setup("09:10", "long", 99.5, 96, 101)],
             reentry="after_stop", reentry_nochase=True)
    assert out[1].result is None and out[1].gates[-1].name == "reentry" and "chasing" in out[1].gates[-1].detail
    out = go(monkeypatch, LOSS, [setup("09:00", "long", 99, 98, 101), setup("09:10", "long", 97, 96, 99)],
             reentry="after_stop", reentry_nochase=True)
    assert out[1].tags.get("reentry") and out[1].result.filled_at is not None


def test_nochase_off_keeps_the_chasing_reentry(monkeypatch):
    out = go(monkeypatch, LOSS, [setup("09:00", "long", 99, 98, 101), setup("09:10", "long", 99.5, 96, 101)],
             reentry="after_stop")
    assert out[1].tags.get("reentry")


def test_counter_trend_trade_takes_everything_at_tp1(monkeypatch):
    # long against a bearish weekly: all off at TP1 101 → +2R (minus cost), no runner to 104
    out = go(monkeypatch, RUN, [runner_setup()], weekly="bear", counter_tp1="all")
    s = out[0]
    assert s.tags.get("tp1_only") and s.plan.partial_frac == 1.0 and s.tags["weekly_trend"] == "bear"
    assert s.result.runner_r == pytest.approx(s.result.r, abs=1e-9)
    # the same long with the weekly keeps its runner and makes more
    w = go(monkeypatch, RUN, [runner_setup()], weekly="bull", counter_tp1="all")[0]
    assert not w.tags.get("tp1_only") and w.plan.partial_frac == 0.5 and w.result.runner_r > s.result.runner_r


def test_counter_tp1_reentry_mode_leaves_first_trades_alone(monkeypatch):
    out = go(monkeypatch, RUN, [runner_setup()], weekly="bear", counter_tp1="reentry")
    assert not out[0].tags.get("tp1_only") and out[0].plan.partial_frac == 0.5
    out = go(monkeypatch, LOSS, [setup("09:00", "long", 99, 98, 101), setup("09:10", "long", 97, 96, 99)],
             weekly="bear", reentry="after_stop", counter_tp1="reentry")
    assert out[1].tags.get("reentry") and out[1].tags.get("tp1_only")


def test_neutral_weekly_and_bad_mode(monkeypatch):
    out = go(monkeypatch, RUN, [runner_setup()], weekly="neutral", counter_tp1="all")
    assert not out[0].tags.get("tp1_only")
    with pytest.raises(ValueError):
        go(monkeypatch, RUN, [runner_setup()], counter_tp1="sometimes")


def test_htf40_is_the_40_day_equilibrium_on_completed_closes():
    assert "htf40" in BIAS_RULES
    idx = pd.date_range("2024-01-01", periods=40, freq="D", tz="America/New_York")
    up = pd.DataFrame({"high": range(101, 141), "low": range(99, 139), "close": range(100, 140)}, index=idx, dtype=float)
    assert bias_htf40(up)[0] == "bull"
    down = up.iloc[::-1].set_axis(idx)
    assert bias_htf40(down)[0] == "bear"
    assert bias_htf40(up.tail(39))[0] == "neutral"           # not enough history: never guesses


def test_real_data_weekly_trend_uses_completed_days_only():
    """US100 2023-03-15: htf40 in the day context equals the rule on daily bars closed before the day, and is unchanged
    when the day's own (and later) bars are removed — no look-ahead."""
    from datetime import date

    from ict_engine.concepts.bars import resample
    from ict_engine.concepts.context import build_context, completed_daily
    from ict_engine.data import dukascopy
    try:
        bars = dukascopy.load("US100", date(2022, 11, 1), date(2023, 3, 31))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    d = date(2023, 3, 15)
    ctx = build_context(bars, d)
    cut = bars[bars.index < pd.Timestamp("2023-03-15 00:00", tz="America/New_York")]
    assert build_context(cut, d).biases["htf40"] == ctx.biases["htf40"]
    daily = completed_daily(resample(cut, "1d"), d)
    assert ctx.biases["htf40"] == bias_htf40(daily) and ctx.biases["htf40"][0] in ("bull", "bear")


def test_weekly_rule_picks_which_bias_is_the_weekly(monkeypatch):
    patched(monkeypatch, [runner_setup()])
    ctx = SimpleNamespace(biases={"htf40": ("bull", ""), "weekly_structure": ("bear", "")})
    p = replace(model_2022.Params(), counter_tp1="all", weekly_rule="weekly_structure")
    s = run.run_day(frame(RUN), DAY, "US100", params=p, max_trades=1, ctx=ctx)[0]
    assert s.tags["weekly_trend"] == "bear" and s.tags.get("tp1_only")          # long against the structure
    p = replace(p, weekly_rule="htf40")
    patched(monkeypatch, [runner_setup()])
    s = run.run_day(frame(RUN), DAY, "US100", params=p, max_trades=1, ctx=ctx)[0]
    assert s.tags["weekly_trend"] == "bull" and not s.tags.get("tp1_only")
