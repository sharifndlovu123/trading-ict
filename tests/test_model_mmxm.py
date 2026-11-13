"""Market Maker Buy/Sell Model on a hand-built day where the right answer is known.

Story (Tue 2024-01-09, bullish daily bias — Mon took Fri's high with a higher low):
02:00–04:00 tight original consolidation at ~103.1 (buy-side engineered above).
Sell-side curve: drop to 100.5, redistribution high 101.5 (05:37), drop to 99.0,
redistribution high 99.8 (07:22), drop runs PDL 95 at 08:45 (smart money reversal),
displacement MSS at 08:47 leaves a FVG, retrace fills it at 09:15, rally through
99.8 (TP1) to the terminus above the OC high.
"""

from datetime import date

import pandas as pd
import pytest

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import swings
from ict_engine.models import model_mmxm
from ict_engine.models.model_mmxm import find_curve


# The hand-built MMBM tape below is a 1m-entry scenario (its displacement FVG exists on 1m only);
# the model's default entry_tf is 5m since the 2026-11-13 sweep, so these tests pin 1m explicitly.
def Params(**kw):
    return model_mmxm.Params(**{"entry_tf": "1m", **kw})


def find_setups(bars_1m, day, asset, params=None):
    return model_mmxm.find_setups(bars_1m, day, asset, params or Params())
from ict_engine.sim.run import run_day
from tests.test_model_2022 import history, path_bars

SYNTHETIC_PRICES = True                  # conftest: no costs on the ~100-price synthetic day
NY = "America/New_York"
DAY = date(2024, 1, 9)


def mmbm_day(oc=True, reclaim=False):
    pts = [("2024-01-08 18:00", 101.0), ("2024-01-09 02:00", 103.1)]
    pts += [("2024-01-09 04:00", 103.1)] if oc else [("2024-01-09 04:00", 104.6)]       # flat OC vs steady trend
    pts += [("2024-01-09 05:00", 100.5), ("2024-01-09 05:37", 101.5),
            ("2024-01-09 06:10", 100.2) if not reclaim else ("2024-01-09 06:10", 103.8),
            ("2024-01-09 07:00", 99.0), ("2024-01-09 07:22", 99.8),
            ("2024-01-09 08:20", 96.0), ("2024-01-09 08:23", 96.6), ("2024-01-09 08:40", 95.2),
            ("2024-01-09 08:45", 94.5), ("2024-01-09 08:46", 95.0), ("2024-01-09 08:47", 97.0),
            ("2024-01-09 08:48", 97.4), ("2024-01-09 09:05", 99.2), ("2024-01-09 09:15", 95.3),
            ("2024-01-09 09:45", 104.0), ("2024-01-09 16:00", 103.5)]
    return path_bars(pts, "2024-01-08 18:00", "2024-01-09 16:30")


def bars(**kw):
    return pd.concat([history(), mmbm_day(**kw)])


def mirror(df, axis=200.0):
    return pd.DataFrame({"open": axis - df.open, "high": axis - df.low, "low": axis - df.high,
                         "close": axis - df.close}, index=df.index)


def planned(setups):
    return [s for s in setups if s.plan is not None]


def test_finds_the_mmbm_with_curve_evidence_and_plan():
    ss = planned(find_setups(bars(), DAY, "US100"))
    assert len(ss) == 1
    s = ss[0]
    assert s.model == "mmbm" and s.side == "long" and s.tags["window"] == "ny_am_kz"
    assert s.tags["oc_high"] == pytest.approx(103.12, abs=0.05)
    assert [round(x, 1) for x in s.tags["steps"]] == [101.5, 99.8]
    assert s.tags["poi"] == "ran pdl" and s.tags["reversal"] == pytest.approx(94.5, abs=0.05)
    p = s.plan
    assert p.stop < 94.5 < p.entry < p.tp1 < p.final_target
    assert p.tp1 == pytest.approx(99.8, abs=0.05) and p.tp1_name == "step 2"
    assert p.final_target == pytest.approx(103.12, abs=0.05)


def test_mmbm_trade_wins():
    s = [x for x in run_day(bars(), DAY, "US100", Params()) if x.traded][0]
    assert s.result.vote and s.result.r > 1


def test_no_original_consolidation_no_trade():
    ss = find_setups(bars(oc=False), DAY, "US100")
    assert not planned(ss)
    assert any("original consolidation" in g.detail for s in ss for g in s.gates)


def test_curve_that_reclaims_the_oc_is_not_an_mmbm():
    """06:10 rally back above the OC high: the curve failed — no model."""
    ss = find_setups(bars(reclaim=True), DAY, "US100")
    assert not any(s.tags.get("oc_high", 0) > 103 and s.plan for s in ss)


def test_sell_model_is_the_mirror():
    ss = planned(find_setups(mirror(bars()), DAY, "US100"))
    assert len(ss) == 1
    s = ss[0]
    assert s.model == "mmsm" and s.side == "short"
    assert s.plan.tp1 == pytest.approx(200 - 99.8, abs=0.05)
    assert s.plan.final_target == pytest.approx(200 - 103.12, abs=0.05)


def test_reaccumulation_zone_is_carried_across_from_the_lowest_redistribution():
    """Redistribution #1 = the 07:15–07:30 area under the 99.8 step: its up-close bar (07:00–07:15,
    99.0 → 99.51) is the zone. The 09:15→09:45 rally (0.29/min) first closes above it at 09:30."""
    ss = [s for s in find_setups(bars(), DAY, "US100", Params(entry="reacc1")) if "zone" in s.tags]
    assert ss
    s = ss[0]
    lo, hi = s.tags["zone"]
    assert lo == pytest.approx(99.0, abs=0.05) and hi == pytest.approx(99.55, abs=0.05)
    assert s.decided_at == pd.Timestamp("2024-01-09 09:30", tz=NY)
    assert any(g.name == "trigger" and g.passed and "carried across" in g.detail for g in s.gates)


def test_reacc2_uses_the_next_redistribution_up():
    ss = [s for s in find_setups(bars(), DAY, "US100", Params(entry="reacc2")) if "zone" in s.tags]
    assert ss and ss[0].tags["zone"][1] > 100.5                    # the 101.5 redistribution


def test_no_lookahead_plan_identical_without_future_bars():
    full = bars()
    s = planned(find_setups(full, DAY, "US100"))[0]
    cut = full[full.index <= s.decided_at]
    s2 = planned(find_setups(cut, DAY, "US100"))[0]
    assert s2.plan == s.plan


def test_find_curve_ignores_frame_bars_after_the_low():
    frame = resample(bars(), "15m")
    sw = swings(frame, "15m")
    low_ts = pd.Timestamp("2024-01-09 08:45", tz=NY)
    c = find_curve(frame, sw, True, low_ts, 94.5, Params())
    assert c is not None and c.oc_end <= low_ts and all(t < low_ts for t in c.step_times)


def test_smr_must_purge_resting_liquidity_not_the_curves_own_lows():
    from ict_engine.concepts.events import Event
    from ict_engine.models.model_mmxm import Curve, smr_purge
    T = lambda hm: pd.Timestamp(f"2024-01-09 {hm}", tz=NY)
    frame = resample(bars(), "15m")
    ctx = type("C", (), {"levels": {"pdl": 95.0}})()
    curve = Curve(T("02:00"), T("04:00"), 103.1, 102.9, (101.5,), (T("05:45"),), (T("05:30"),))
    p = Params()
    assert smr_purge(ctx, frame, [], True, 94.5, T("08:45"), curve, p) == "ran pdl"
    assert smr_purge(ctx, frame, [], True, 95.5, T("08:45"), curve, p) is None
    sl = lambda o, px: Event("swing_low", "15m", "bull", T(o) + pd.Timedelta(minutes=30), T(o), px, px)
    one_curve_low = [sl("06:00", 99.9)]                               # a curve's own stepping low
    assert smr_purge(ctx, frame, one_curve_low, True, 95.5, T("08:45"), curve, p) is None
    eql = [sl("06:00", 99.9), sl("07:00", 99.95)]                      # relatively equal lows (tol 0.1)
    assert smr_purge(ctx, frame, eql, True, 95.5, T("08:45"), curve, p).startswith("ran equal lows")
    older = [Event("swing_low", "15m", "bull", pd.Timestamp("2024-01-08 20:30", tz=NY),
                   pd.Timestamp("2024-01-08 20:00", tz=NY), 96.0, 96.0)]
    assert smr_purge(ctx, frame, older, True, 95.5, T("08:45"), curve, p).startswith("ran older")


def test_poi_gate_reports_the_purge():
    s = planned(find_setups(bars(), DAY, "US100"))[0]
    assert s.tags["purge"] == "ran pdl"
