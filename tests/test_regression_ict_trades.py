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
    mm4 = [s for d in days for s in run_day(bars, d, "US100", MMXM_VARIANTS["tf: frame 4h > entry 1h"])]   # 1h entry runs
    assert all(s.decided_at.minute == 59 for s in mm4 if s.plan is not None)
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


def test_nested_fvg_location_gates_and_range_target_on_real_bars():
    """Nested-FVG pre-registration on real US100 bars (March 2023), both models: the location gates give the same
    verdict with the bars after the decision removed; eq_hold plans carry the session close and a TP1 ahead of entry."""
    from ict_engine.eval.backtest import load_range
    from ict_engine.eval.variants import MMXM_VARIANTS, VARIANTS
    from ict_engine.models import entry_quality as eq, targets as tg
    from ict_engine.sim.run import run_day
    try:
        bars = load_range("US100", date(2023, 1, 20), date(2023, 3, 17))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    days = [d for d in pd.date_range("2023-03-06", "2023-03-17").date if d.weekday() < 5]
    for table in (VARIANTS, MMXM_VARIANTS):
        verdicts = {True: 0, False: 0}
        for gate in ("loc: entry FVG inside a 4h FVG", "loc: not inside a daily FVG"):
            for d in days:
                for s in run_day(bars, d, "US100", table[gate]):
                    g = next((g for g in s.gates if g.name == "entry_quality"), None)
                    if g is None:
                        continue
                    cut = bars[bars.index <= s.decided_at]
                    assert eq.check(s, cut, None, table[gate].entry_gate) == (g.passed, g.detail)
                    verdicts[g.passed] += 1
        assert sum(verdicts.values()) > 0
        plans = [s for d in days for s in run_day(bars, d, "US100", table["targets: 50% of the 4h range, runner to the HTF draw"])
                 if s.plan is not None]
        assert plans
        for s in plans:
            p = s.plan
            assert p.time_exit == tg.session_close(s.day)
            assert (p.tp1 > p.entry) if s.side == "long" else (p.tp1 < p.entry)


def test_range_in_play_entries_on_real_bars():
    """Range-in-play pre-registration on real US100 bars (March 2023), both models: every range verdict is the same with
    the bars after the decision removed; a moved limit is deeper than the model's own entry and stays inside the stop."""
    from ict_engine.eval.backtest import load_range
    from ict_engine.eval.variants import MMXM_VARIANTS, VARIANTS
    from ict_engine.models import range_entry
    from ict_engine.sim.run import run_day
    try:
        bars = load_range("US100", date(2023, 1, 20), date(2023, 3, 17))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    days = [d for d in pd.date_range("2023-03-06", "2023-03-17").date if d.weekday() < 5]
    for table in (VARIANTS, MMXM_VARIANTS):
        base = {s.decided_at: s.plan for d in days for s in run_day(bars, d, "US100", table["baseline"]) if s.plan}
        seen = 0
        for name in ("range: entry in the cheap half", "range: limit at the 50%", "leg: limit at OTE 70.5%"):
            p = table[name]
            for d in days:
                for s in run_day(bars, d, "US100", p):
                    g = next((g for g in s.gates if g.name == "range"), None)
                    if g is None:
                        continue
                    seen += 1
                    orig = base.get(s.decided_at)
                    if orig is None:
                        continue
                    cut = bars[bars.index <= s.decided_at]
                    ok, why, new = range_entry.apply(p.range_entry, orig, cut, stop_buffer=p.stop_buffer, asset="US100",
                                                     max_cost_r=p.max_cost_r)
                    assert (ok, why) == (g.passed, g.detail)
                    if ok:
                        long = orig.side == "long"
                        assert (new.entry <= orig.entry if long else new.entry >= orig.entry)
                        assert (new.entry > orig.stop if long else new.entry < orig.stop)
        assert seen > 0


def test_counter_bias_on_real_bars_us100_sep_2023():
    """Review log #22 / counter-bias pre-reg on real US100 bars. Sep 25 2023: the 10:02 short reached TP1 (Sharif's same
    sell); his 11:00 long (engine 11:05) fails the bias AND the POI gate (no sweep — it added liquidity), so the rule,
    which admits only setups whose sole failed gate is the bias, rightly leaves it out. Over September every admitted
    setup has all other gates passed and its trigger (an earlier bias-side TP1) known before its decision."""
    from dataclasses import replace
    from ict_engine.eval.backtest import load_range
    from ict_engine.models import model_2022
    from ict_engine.sim.run import run_day
    try:
        bars = load_range("US100", date(2023, 8, 1), date(2023, 9, 29))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    d = date(2023, 9, 25)
    base = [s for s in run_day(bars, d, "US100", model_2022.Params()) if s.plan and 9 <= s.decided_at.hour < 12]
    assert [(f"{s.decided_at:%H:%M}", s.side) for s in base] == [("10:02", "short")] and base[0].result.vote
    s1105 = next(s for s in run_day(bars, d, "US100", replace(model_2022.Params(), counter_after="tp1"))
                 if f"{s.decided_at:%H:%M}" == "11:05")
    assert s1105.plan is None and {g.name for g in s1105.gates if not g.passed} == {"bias", "poi"}
    admitted = 0
    for mode in ("tp1", "draw"):
        p = replace(model_2022.Params(), counter_after=mode)
        for day in pd.date_range("2023-09-01", "2023-09-28").date:
            if day.weekday() >= 5:
                continue
            for s in run_day(bars, day, "US100", p):
                g = next((g for g in s.gates if g.name == "bias"), None)
                if g is None or "counter-bias admitted" not in g.detail:
                    continue
                admitted += 1
                assert all(x.passed for x in s.gates if x.name not in ("cap",))
                hhmm = g.detail.rsplit(" at ", 1)[1][:5]
                assert hhmm < f"{s.decided_at:%H:%M}" or s.decided_at.hour < 18 <= int(hhmm[:2])
    assert admitted > 0


def test_liquidity_hold_on_real_bars_us100_sep_2023():
    """Liquidity-hold pre-reg on real US100 bars, September 2023 (in-sample). The hold only adds: every baseline plan is
    still planned. Every 'held <level>' POI names a context level the manipulation extreme stopped short of by ≤ 2 bp
    without trading through, untaken from the day start to the shift. Sep 25 11:05 (Sharif's 11:00 long) still fails
    the bias."""
    from dataclasses import replace
    from datetime import datetime, time
    from ict_engine.concepts.context import build_context
    from ict_engine.eval.backtest import load_range
    from ict_engine.models import model_2022
    from ict_engine.sim.run import run_day
    try:
        bars = load_range("US100", date(2023, 8, 1), date(2023, 9, 29))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    base, held = model_2022.Params(), replace(model_2022.Params(), liquidity_hold_bp=2.0)
    n_held = 0
    for day in pd.date_range("2023-09-01", "2023-09-28").date:
        if day.weekday() >= 5:
            continue
        key = lambda s: (s.decided_at, s.side, s.plan.entry)
        b = {key(s) for s in run_day(bars, day, "US100", base) if s.plan}
        sh = run_day(bars, day, "US100", held)
        assert b <= {key(s) for s in sh if s.plan}
        ctx = build_context(bars, day)
        for s in sh:
            poi = str(s.tags.get("poi"))
            if not poi.startswith("held "):
                continue
            n_held += 1
            long, lvl = s.side == "long", ctx.levels[poi.split()[1]]
            stop_anchor = s.would_plan.stop + held.stop_buffer if long else s.would_plan.stop - held.stop_buffer
            gap = stop_anchor - lvl if long else lvl - stop_anchor
            assert 0 <= gap <= abs(lvl) * 2e-4 + 1e-9
            d0 = pd.Timestamp(datetime.combine(day, time(0)), tz="America/New_York")
            seg = bars[(bars.index >= d0) & (bars.index < s.evidence["shift"].origin_ts)]
            assert (seg.low.min() >= lvl) if long else (seg.high.max() <= lvl)
    assert n_held >= 1
    s1105 = next(s for s in run_day(bars, date(2023, 9, 25), "US100", held) if f"{s.decided_at:%H:%M}" == "11:05")
    assert s1105.plan is None and "bias" in {g.name for g in s1105.gates if not g.passed}


def test_oc_retest_on_real_bars_us100_q3_2023():
    """OC-retest pre-reg on real US100 bars (Jul–Sep 2023, in-sample). Every plan: limit at the OC edge the setup
    broke, stop beyond the OC's far side, TP1 = 2R, order lives to 16:00, decided after a close beyond the edge and
    after price ran 1R past it — and the same plan comes out when the bars stop at the decision (no look-ahead)."""
    from dataclasses import replace
    from ict_engine.eval.backtest import load_range
    from ict_engine.models import model_mmxm
    from ict_engine.sim.run import run_day
    try:
        bars = load_range("US100", date(2023, 6, 1), date(2023, 9, 29))
    except FileNotFoundError:
        pytest.skip("US100 bars not downloaded")
    p = replace(model_mmxm.Params(), entry="oc_retest")
    plans = 0
    for day in pd.date_range("2023-07-01", "2023-09-28").date:
        if day.weekday() >= 5:
            continue
        for s in run_day(bars, day, "US100", p):
            if not s.plan:
                continue
            plans += 1
            long, pl = s.side == "long", s.plan
            hi, lo = s.tags["oc_high"], s.tags["oc_low"]
            assert pl.entry == (hi if long else lo) and pl.stop == (lo - p.stop_buffer if long else hi + p.stop_buffer)
            risk = abs(pl.entry - pl.stop)
            assert abs(abs(pl.tp1 - pl.entry) - 2 * risk) < 1e-6 and f"{pl.expires_at:%H:%M}" == "16:00"
            seg = bars[(bars.index >= s.evidence["shift"].origin_ts) & (bars.index <= s.decided_at)]
            assert ((seg.close > hi).any() and seg.high.max() >= hi + risk) if long else \
                   ((seg.close < lo).any() and seg.low.min() <= lo - risk)
            if plans <= 3:
                cut = bars[bars.index <= s.decided_at]
                again = [x.plan for x in run_day(cut, day, "US100", p) if x.plan and x.decided_at == s.decided_at]
                assert any(a.entry == pl.entry and a.stop == pl.stop and a.tp1 == pl.tp1 for a in again)
    assert plans >= 10
