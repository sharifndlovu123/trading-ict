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


def test_blocks_on_real_data_are_known_after_they_form_and_retire_on_their_50pct():
    """OB / breaker / mitigation blocks on real US100 1h bars (Dec 2023–Jan 2024): every block is known only after
    it formed, its zone is a real price range, all three kinds appear, and the lifecycle's retirement is a body
    close beyond the 50%."""
    from ict_engine.concepts.bars import resample
    from ict_engine.concepts.events import breaker_blocks, order_blocks
    bars = _bars(date(2024, 1, 10))
    h1 = resample(bars[bars.index >= ny("2023-12-01 00:00")], "1h")
    blocks = order_blocks(h1, "1h") + breaker_blocks(h1, "1h")
    assert {b.kind for b in blocks} == {"ob", "breaker", "mitigation"}
    for b in blocks:
        assert b.ts > b.origin_ts and b.top > b.bottom
    b = next(x for x in blocks if x.kind == "ob")
    st = gap_lifecycle(b, bars)
    if st.retired is not None:
        c = bars.loc[st.retired].close
        assert (c < b.ce) if b.direction == "bull" else (c > b.ce)


def test_equal_lows_found_where_sharif_drew_them_nq_april_2024():
    """Sharif's trade-review drawing (2026-11-14): sellside liquidity line ~18046–18050 from the 18 Mar 2024
    session (daily NQ). The equal-lows detector must find it, with ≥3 touches, before the 15 Apr run below it."""
    from datetime import date
    from ict_engine.data import orderflow as of
    from ict_engine.concepts.bars import resample
    from ict_engine.concepts.events import equal_levels, swings
    if not of.path_for(of.SYMBOL, of.BARS, "2024-04").exists():
        pytest.skip("CME NQ bars not downloaded (ict_engine.data.orderflow bars)")
    d = resample(of.load(date(2024, 2, 15), date(2024, 4, 15), schema=of.BARS), "1d")
    eql = [lv for lv in equal_levels(d, swings(d, "1d"), tol=18000 * 2 / 1e4) if lv.side == "low"]
    hit = [lv for lv in eql if 18040 <= lv.price <= 18056 and "eql3" in lv.name]
    assert hit and hit[0].valid_from < pd.Timestamp("2024-04-15", tz="America/New_York")


@pytest.mark.parametrize("start,end,tfs,fvg_bottom,origin,own_tf_day,one_min_day", [
    # Sharif's daily NQ narrative (2024): Mar 20 daily FVG fails on the Apr 4 daily close (US100 CFD prices)
    ("2024-02-15", "2024-04-12", ("1d",), 18041.0, "2024-03-19", "2024-04-04", "2024-04-02"),
    # Sharif's weekly example (2026): week-of-Sep-21 FVG fails on the weekly close of Oct 16
    ("2026-07-01", "2026-11-13", ("1w",), 29703.7, "2026-09-20", "2026-10-16", "2026-10-14"),
])
def test_htf_ifvg_inverts_on_its_own_timeframe_close_sharifs_examples(start, end, tfs, fvg_bottom, origin,
                                                                     own_tf_day, one_min_day):
    """Sharif (2026-11-14): an HTF FVG fails on a close of ITS timeframe, not the first 1m close through it."""
    from datetime import date
    from ict_engine.data import dukascopy as d
    from ict_engine.models.model_pd_return import htf_arrays
    try:
        h = d.load("US100", date.fromisoformat(start), date.fromisoformat(end))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    pick = lambda mode: [e for e in htf_arrays(h, tfs, ("ifvg",), ifvg_close=mode)
                         if e.direction == "bear" and abs(e.bottom - fvg_bottom) < 1 and str(e.origin_ts.date()) == origin]
    (tf_close,), (m1,) = pick("tf"), pick("1m")
    assert str(tf_close.ts.date()) == own_tf_day and str(m1.ts.date()) == one_min_day


def test_flip_after_failed_trade_on_real_bars_us100_march_2023():
    """The flip (research/preregistered-ifvg-flip-2026-11-14.md) on real bars: every flip comes from a real own-TF
    close through the failed trade's entry FVG, sits on the opposite side, and is identical without future bars."""
    from datetime import date, datetime, time, timedelta
    from ict_engine.concepts.bars import resample
    from ict_engine.concepts.context import build_context
    from ict_engine.eval import flip as fl
    from ict_engine.eval.backtest import load_range
    from ict_engine.models.registry import modules
    from ict_engine.sim.run import run_day
    try:
        bars = load_range("US100", date(2023, 3, 1), date(2023, 3, 31))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    NY = "America/New_York"
    P = modules()["silver_bullet"].Params()
    seen, d = 0, date(2023, 3, 1)
    while d <= date(2023, 3, 31):
        if d.weekday() < 5:
            ctx = build_context(bars, d)
            day = bars[(bars.index >= pd.Timestamp(datetime.combine(d, time(0)), tz=NY)) &
                       (bars.index < pd.Timestamp(datetime.combine(d, time(16, 30)), tz=NY))]
            for s in run_day(bars, d, "US100", P, ctx=ctx):
                for rule in fl.STOP_RULES:
                    p = fl.flip_plan(s, day, ctx, P, rule)
                    if p is None:
                        continue
                    seen += 1
                    f = s.evidence["fvg"]
                    c = resample(day, f.tf)
                    close = float(c[c.close_ts == p.placed_at].close.iloc[0])
                    assert (close < f.bottom) if s.side == "long" else (close > f.top)
                    assert p.side != s.side and p.placed_at <= s.result.exit_at + timedelta(minutes=5)
                    cut = day[day.index <= max(p.placed_at, s.result.exit_at)]
                    assert fl.flip_plan(s, cut, ctx, P, rule) == p
        d += timedelta(days=1)
    assert seen > 0


def test_hold_targets_and_entry_gates_on_real_bars_without_lookahead():
    """Liquidity-targets amendment 1 (hold to the session close) and the entry-quality gates on real US100 bars: the
    hold plan carries the session close; the target modes and the gate verdicts are identical when the bars after the
    decision are removed. (Whole find_setups plans are not compared on truncated bars: cutting mid-candle lets a
    partial 5m candle confirm a swing early, e.g. 2023-03-07 12:23; the full backtest correctly waits for the close.)"""
    from datetime import date, timedelta
    from ict_engine.concepts.context import build_context
    from ict_engine.eval.backtest import load_range
    from ict_engine.models import entry_quality as eq, model_pd_return as pr, targets as tg
    try:
        bars = load_range("US100", date(2023, 3, 1), date(2023, 3, 17))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    p = pr.Params(target_mode="hold")
    n = 0
    d = date(2023, 3, 6)
    while d <= date(2023, 3, 17):
        if d.weekday() < 5:
            ctx = build_context(bars, d)
            for s in pr.find_setups(bars, d, "US100", p, ctx):
                w = s.would_plan
                if w is None:
                    continue
                assert w.time_exit == tg.session_close(d)
                cut = bars[bars.index <= s.decided_at]
                for mode in tg.MODES:
                    kw = dict(entry=w.entry, stop=w.stop, long=s.side == "long", tp1=w.tp1, tp1_name=w.tp1_name,
                              final=w.final_target, final_name=w.final_name, decided=s.decided_at, ctx=ctx, day=d,
                              min_tp1=w.risk)
                    assert tg.apply(mode, bars_1m=bars, **kw) == tg.apply(mode, bars_1m=cut, **kw)
                for gate in eq.GATES:
                    assert eq.check(s, bars, ctx, gate) == eq.check(s, cut, ctx, gate)
                n += 1
        d += timedelta(days=1)
    assert n > 0


def test_higher_timeframes_and_trailed_runner_on_real_bars():
    """Timeframes/trail pre-registration on real US100 bars (March 2023): higher-timeframe entries decide only when
    their entry candle has finished; plans are well-formed; the trailed runner carries the session close and its
    result does not change when bars after that close are removed."""
    from dataclasses import replace
    from ict_engine.eval.backtest import load_range
    from ict_engine.eval.variants import MMXM_VARIANTS, VARIANTS
    from ict_engine.models import targets as tg
    from ict_engine.sim.run import run_day
    try:
        bars = load_range("US100", date(2023, 2, 20), date(2023, 3, 17))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    days = [d for d in pd.date_range("2023-03-06", "2023-03-17").date if d.weekday() < 5]
    for name, tf in (("tf: entry 15m", 15), ("tf: entry 5m", 5)):
        plans = [s for d in days for s in run_day(bars, d, "US100", VARIANTS[name]) if s.plan is not None]
        assert plans, name
        for s in plans:
            assert (s.decided_at.minute + 1) % tf == 0, (name, s.decided_at)      # the entry candle had closed
            p = s.plan
            assert (p.stop < p.entry < p.tp1) if s.side == "long" else (p.tp1 < p.entry < p.stop)
    mm = [s for d in days for s in run_day(bars, d, "US100", MMXM_VARIANTS["tf: frame 1h > entry 15m"]) if s.plan is not None]
    assert all((s.decided_at.minute + 1) % 15 == 0 for s in mm)
    trail = VARIANTS["runner: trailed on 5m"]
    n = 0
    for d in days:
        for s in run_day(bars, d, "US100", trail):
            if s.plan is None or s.result is None or s.result.runner_r is None or s.result.exit_reason != "tp1":
                continue
            assert s.plan.runner_until == tg.session_close(d)
            cut = bars[bars.index < s.plan.runner_until + pd.Timedelta(minutes=5)]
            again = [x for x in run_day(cut, d, "US100", trail) if x.decided_at == s.decided_at][0]
            assert again.result.runner_r == pytest.approx(s.result.runner_r)
            n += 1
    assert n > 0
