"""PD array return (ICT's live-execution form) on a hand-built day with known answers.

Tape (Tue 2024-01-09): 02:00–05:00 rally 100 → 106.5 (leaves a 1h bull FVG ≈ 102.0–104.0; 05:00 peak 106.5 =
untaken liquidity) → hold 106 → 08:00–08:40 pullback into the 1h FVG (low ≈ 103.2) → sharp 1m reaction up
(1m bull FVG; its near edge ≈ 103.33 is the limit) → 08:44–08:50 retrace to 103.28 fills it → rally through 106.5 by 10:00.
"""

from datetime import date

from dataclasses import replace

import pandas as pd
import pytest

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import fvgs
from ict_engine.models import model_pd_return as pr
from ict_engine.sim.run import run_day
from tests.test_model_2022 import history, path_bars
from tests.test_model_mmxm import mirror

SYNTHETIC_PRICES = True
DAY = date(2024, 1, 9)
NY = "America/New_York"
P = pr.Params(use_bias=False)          # the synthetic history doesn't define a daily bias


def ts(hm):
    return pd.Timestamp(f"2024-01-09 {hm}", tz=NY)


def day_bars(fail=False):
    pts = [("2024-01-08 18:00", 100.0), ("2024-01-09 02:00", 100.0), ("2024-01-09 05:00", 106.5),
           ("2024-01-09 05:20", 106.0), ("2024-01-09 08:00", 106.0)]
    if fail:   # blows through both overnight 1h FVGs (≈100.0–102.1, 102.2–104.3): closes below 100, then bounces
        pts += [("2024-01-09 08:40", 98.6), ("2024-01-09 08:44", 99.8), ("2024-01-09 09:30", 99.2)]
    else:
        pts += [("2024-01-09 08:40", 103.2), ("2024-01-09 08:44", 104.4), ("2024-01-09 08:50", 103.28),
                ("2024-01-09 10:00", 107.5)]
    pts += [("2024-01-09 16:00", 107.0)]
    return path_bars(pts, "2024-01-08 18:00", "2024-01-09 16:30")


def bars(**kw):
    return pd.concat([history(), day_bars(**kw)])


def planned(ss, side="long"):
    return [s for s in ss if s.plan is not None and s.side == side]


def one_h_gap():
    g = [x for x in pr.htf_arrays(bars(), ("1h",)) if x.direction == "bull" and x.ts.date() == DAY]
    return max(g, key=lambda x: x.top - x.bottom)


# --- pieces -----------------------------------------------------------------------------------

def test_htf_arrays_find_the_overnight_1h_bull_fvg():
    g = one_h_gap()
    assert g.tf == "1h" and 101.5 < g.bottom < g.top < 104.6


def test_return_is_the_first_touch_of_a_still_valid_array():
    g = one_h_gap()
    day = bars()[bars().index >= ts("00:00")]
    hits = dict((x.ts, t) for x, t in pr.returns([g], day, ts("00:00")))
    touch = hits[g.ts]
    assert ts("08:20") < touch < ts("08:40") and day.loc[touch].low <= g.top


def test_trigger_is_a_1m_fvg_in_the_reaction_and_none_when_the_array_fails_first():
    g = one_h_gap()
    for fail, expect in ((False, True), (True, False)):
        day = bars(fail=fail)
        day = day[day.index >= ts("00:00")]
        touch = pr.returns([g], day, ts("00:00"))[0][1]
        ltf = fvgs(resample(day, "1m"), "1m", min_size=0.002)
        got = pr.reaction_trigger(g, touch, day, ltf, 30)
        assert (got is not None) == expect
        if got:
            f, ext = got
            assert f.direction == "bull" and ts("08:40") <= f.ts <= ts("08:45") and ext == pytest.approx(103.2, abs=0.05)


# --- the full model -----------------------------------------------------------------------------

def test_finds_the_long_from_the_1h_array_with_1m_entry_and_tight_stop():
    ss = planned(pr.find_setups(bars(), DAY, "US100", P))
    assert ss, [(s.tags, [str(g) for g in s.gates]) for s in pr.find_setups(bars(), DAY, "US100", P)][:5]
    s = ss[0]
    assert s.model == "pd_return" and s.tags["array_tf"] == "1h"
    assert s.tags["window"] in ("ny_premarket", "ny_am_kz")
    assert s.plan.stop == pytest.approx(103.2, abs=0.05)                      # reaction low (stop_mode reaction)
    assert 103.2 < s.plan.entry < 104.4 and s.plan.tp1 == pytest.approx(106.5, abs=0.05)


def test_array_stop_mode_puts_the_stop_beyond_the_array():
    s = planned(pr.find_setups(bars(), DAY, "US100", pr.Params(use_bias=False, stop_mode="array")))[0]
    assert s.plan.stop == pytest.approx(one_h_gap().bottom, abs=0.01)


def test_trade_wins_and_is_one_per_window():
    out = run_day(bars(), DAY, "US100", P)
    traded = [s for s in out if s.traded]
    assert len(traded) == 1 and traded[0].result.vote and traded[0].side == "long"


def test_no_trade_when_the_array_fails():
    """Only today's arrays (lookback 0): the history's own gaps (Monday's 95 → 112 rally) are real arrays too."""
    today = pr.Params(use_bias=False, lookback_days=0)
    assert planned(pr.find_setups(bars(), DAY, "US100", today))
    assert not planned(pr.find_setups(bars(fail=True), DAY, "US100", today))


def test_sell_model_is_the_mirror():
    ss = planned(pr.find_setups(mirror(bars()), DAY, "US100", P), side="short")
    assert ss and ss[0].plan.tp1 == pytest.approx(200 - 106.5, abs=0.05)


def test_no_lookahead_plan_identical_without_future_bars():
    full = planned(pr.find_setups(bars(), DAY, "US100", P))[0]
    cut = bars()
    cut = cut[cut.index <= full.decided_at]
    b = planned(pr.find_setups(cut, DAY, "US100", P))[0]
    assert (full.plan.entry, full.plan.stop, full.plan.tp1, full.decided_at) == \
           (b.plan.entry, b.plan.stop, b.plan.tp1, b.decided_at)


def test_outside_the_windows_nothing_is_traded():
    assert not planned(pr.find_setups(bars(), DAY, "US100", pr.Params(use_bias=False, windows=("ny_pm_kz",))))


def test_bias_gate_is_applied_by_default():
    s = pr.find_setups(bars(), DAY, "US100")[0]
    assert any(g.name == "bias" for g in s.gates)


def test_registered():
    from ict_engine.models.registry import modules
    assert modules()["pd_return"] is pr


# --- OB / breaker / mitigation variants (models.md §6) --------------------------------------------

def test_htf_arrays_returns_only_the_asked_kinds_and_blocks_fail_at_their_50pct():
    for kinds in (("ob",), ("breaker", "mitigation"), ("fvg", "ob")):
        got = pr.htf_arrays(bars(), ("15m", "1h"), kinds)
        assert got and {g.kind for g in got} <= set(kinds)
    ob = pr.Event("ob", "1h", "bull", ts("05:00"), ts("02:00"), 104.0, 102.0)
    fvg = pr.Event("fvg", "1h", "bull", ts("05:00"), ts("02:00"), 104.0, 102.0)
    assert pr.fail_level(ob) == 103.0 and pr.fail_level(fvg) == 102.0


def ob_bars():
    """02:00–02:45 dip 100 → 98.9 (down-close 15m candles = the OB ≈ 98.9–100), 02:45–05:00 rally to 106.5 (a 15m
    close above the OB's high validates it), 08:00–08:40 pullback into the OB above its 50% (low 99.6), a sharp 1m
    reaction (1m FVG), a retrace that fills it, then the rally through 106.5."""
    pts = [("2024-01-08 18:00", 100.0), ("2024-01-09 02:00", 100.0), ("2024-01-09 02:45", 98.9),
           ("2024-01-09 05:00", 106.5), ("2024-01-09 05:20", 106.0), ("2024-01-09 08:00", 106.0),
           ("2024-01-09 08:40", 99.6), ("2024-01-09 08:44", 100.8), ("2024-01-09 08:50", 99.7),
           ("2024-01-09 10:00", 107.5), ("2024-01-09 16:00", 107.0)]
    return pd.concat([history(), path_bars(pts, "2024-01-08 18:00", "2024-01-09 16:30")])


def test_ob_variant_trades_the_return_to_the_overnight_order_block_without_lookahead():
    p = pr.Params(use_bias=False, arrays=("ob",), htf_tfs=("15m",), lookback_days=0)
    assert "arrays=" in p.variant
    ss = planned(pr.find_setups(ob_bars(), DAY, "US100", p))
    assert ss, [(s.tags, [str(g) for g in s.gates]) for s in pr.find_setups(ob_bars(), DAY, "US100", p)]
    s = ss[0]
    assert s.tags["array_kind"] == "ob" and s.tags["poi"] == "15m OB" and 98.8 < s.plan.stop < s.plan.entry < 101
    cut = ob_bars()
    cut = cut[cut.index <= s.decided_at]
    b = planned(pr.find_setups(cut, DAY, "US100", p))[0]
    assert (b.plan.entry, b.plan.stop, b.plan.tp1, b.decided_at) == (s.plan.entry, s.plan.stop, s.plan.tp1, s.decided_at)


def test_htf_arrays_ob_confirm_open_and_body_measure():
    from ict_engine.models.model_pd_return import htf_arrays, fail_level
    idx = pd.date_range("2024-04-10 09:30", periods=4, freq="1min", tz="America/New_York")
    df = pd.DataFrame({"open": [18190.0, 18184.0, 18486.25, 18151.0], "high": [18200.0, 18518.75, 18507.75, 18350.75],
                       "low": [18150.0, 18088.0, 18120.25, 17841.5], "close": [18160.0, 18485.5, 18172.5, 17875.0]}, index=idx)
    rng = [a for a in htf_arrays(df, ("1m",), ("ob",)) if a.direction == "bear"]
    body = [a for a in htf_arrays(df, ("1m",), ("ob",), ob_confirm="open", ob_measure="body") if a.direction == "bear"]
    assert rng[0].ts == idx[3] and (rng[0].top, rng[0].bottom) == (18518.75, 18088.0)
    assert body[0].ts == idx[2] and (body[0].top, body[0].bottom) == (18485.5, 18184.0)
    assert fail_level(body[0]) == 18334.75                      # mean threshold on the body


# --- IFVG arrays (research/preregistered-htf-ifvg-2026-11-14.md) ------------------------------------

def test_htf_arrays_ifvg_kind_and_close_mode_validation():
    got = pr.htf_arrays(bars(fail=True), ("15m", "1h"), ("ifvg",))
    assert got and {g.kind for g in got} == {"ifvg"}
    for g in got:                                   # own-TF mode: known at a close of that timeframe
        tfb = resample(bars(fail=True), g.tf)
        assert g.ts in set(tfb.close_ts)
    with pytest.raises(ValueError):
        pr.htf_arrays(bars(), ("1h",), ("ifvg",), ifvg_close="5m")


def test_ifvg_bias_override_only_lifts_the_bias_gate_for_ifvg_arrays(monkeypatch):
    monkeypatch.setattr(pr, "bias_gate", lambda *a, **k: pr.Gate("bias", False, "daily bias bull"))
    day = day_bars()
    ifvg = pr.Event("ifvg", "1d", "bear", ts("02:00"), ts("01:00"), 104.0, 102.0)
    fvg = replace(ifvg, kind="fvg")
    gate = lambda g, p: next(x for x in pr._evaluate(g, ts("09:40"), None, DAY, "US100", p, day, [], []).gates
                             if x.name == "bias")
    over = pr.Params(arrays=("ifvg",), ifvg_bias="override")
    assert gate(ifvg, over).passed and "overrides" in gate(ifvg, over).detail
    assert not gate(ifvg, pr.Params(arrays=("ifvg",))).passed      # default: the bias still gates
    assert not gate(fvg, over).passed                               # only IFVG arrays may go against the bias
    assert "ifvg_bias=override" in over.variant


def test_return_level_ce_waits_for_the_50pct_of_the_array():
    """Sharif's handling notes (2026-11-16): "sold too early … try 50% of the 4h FVG" — the return can be the first
    trade to the array's consequent encroachment instead of its near edge. Default unchanged."""
    g = one_h_gap()
    day = bars()[bars().index >= ts("00:00")]
    edge = pr.returns([g], day, ts("00:00"))[0][1]
    ce = pr.returns([g], day, ts("00:00"), level="ce")[0][1]
    assert ce > edge and day.loc[ce].low <= g.ce and (day[(day.index > g.ts) & (day.index < ce)].low > g.ce).all()
    assert pr.Params().return_level == "proximal" and "return_level" not in pr.Params().variant
    assert "return_level=ce" in replace(pr.Params(), return_level="ce").variant
    with pytest.raises(ValueError):
        pr.returns([g], day, ts("00:00"), level="nope")
