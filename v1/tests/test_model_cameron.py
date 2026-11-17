"""Cameron's Model (ICT, Twitter Space) on a hand-built day with known answers.

Tape (Tue 2024-01-09): 05:00 hourly high ~105.02 → sell-off to 99 at 07:00 (the 06:00 candle opens
just under 102.05: the nearest untaken hourly high = the draw) → running back up (07:00 1h candle
closes above the 06:00 one) → 5m swing low ~100.98 at 08:20 → swept at 08:37
(low ~100.58) → the 08:40 5m candle closes up → 1m FVG ~100.71–100.88 → fill on the 08:55 pullback
→ rally through the draw.
"""

from datetime import date

import pandas as pd
import pytest

from ict_engine.concepts.bars import resample
from ict_engine.models import model_cameron as cm
from ict_engine.sim.run import run_day
from tests.test_model_2022 import history, path_bars
from tests.test_model_mmxm import mirror

SYNTHETIC_PRICES = True
DAY = date(2024, 1, 9)
NY = "America/New_York"


def ts(hm):
    return pd.Timestamp(f"2024-01-09 {hm}", tz=NY)


def day_bars(running=True):
    pts = [("2024-01-08 18:00", 99.0), ("2024-01-09 05:00", 105.0), ("2024-01-09 07:00", 99.0)]
    # not running: the 07:00 candle closes at 98.5, below the 06:00 close (~99.05), then jumps back
    pts += [("2024-01-09 08:00", 102.0)] if running else [("2024-01-09 07:30", 101.0), ("2024-01-09 07:59", 98.5),
                                                         ("2024-01-09 08:00", 102.0)]
    pts += [("2024-01-09 08:20", 101.0), ("2024-01-09 08:27", 101.6), ("2024-01-09 08:33", 101.3),
            ("2024-01-09 08:37", 100.6), ("2024-01-09 08:44", 102.0), ("2024-01-09 08:55", 100.85),
            ("2024-01-09 10:00", 105.6), ("2024-01-09 16:00", 104.0)]
    return path_bars(pts, "2024-01-08 18:00", "2024-01-09 16:30")


def bars(**kw):
    return pd.concat([history(), day_bars(**kw)])


def planned(ss, side="long"):
    return [s for s in ss if s.plan is not None and s.side == side]


# --- pieces -----------------------------------------------------------------------------------

def test_running_toward_compares_the_last_two_finished_candles():
    h = resample(day_bars(), "1h")
    done = h[h.index < ts("08:00")]
    assert cm.running_toward(done, long=True) and not cm.running_toward(done, long=False)


def test_draw_is_the_nearest_untaken_htf_high_at_least_min_distance_away():
    hist = bars()
    seen = hist[hist.index <= ts("08:44")]
    near = cm.draw_level(seen, ts("08:44"), long=True, entry=100.88, min_dist=0.5, p=cm.Params())
    assert near == (pytest.approx(102.045, abs=0.01), "1h high 06:00")
    far = cm.draw_level(seen, ts("08:44"), long=True, entry=100.88, min_dist=2.0, p=cm.Params())
    assert far == (pytest.approx(105.02, abs=0.01), "1h high 05:00")      # 102.05 is < 2 away → next one


# --- the full model -----------------------------------------------------------------------------

def test_finds_the_long_with_sweep_upclose_fvg_and_draw():
    ss = planned(cm.find_setups(bars(), DAY, "US100"))
    assert len(ss) >= 1
    s = ss[0]
    assert s.model == "cameron" and s.tags["window"] == "ny_am_kz"
    assert s.decided_at == ts("08:44")
    assert s.tags["swept"] == pytest.approx(100.98, abs=0.03)
    assert s.plan.entry == pytest.approx(100.88, abs=0.03)
    assert s.plan.stop == pytest.approx(100.58 - 0.25, abs=0.03)
    assert s.plan.tp1 == pytest.approx(102.045, abs=0.03) and s.plan.tp1_name == "1h high 06:00"


def test_trade_wins_and_is_one_per_day():
    out = run_day(bars(), DAY, "US100", cm.Params())
    traded = [s for s in out if s.traded]
    assert len(traded) == 1 and traded[0].result.vote and traded[0].side == "long"


def test_no_setup_when_price_is_not_running_toward_the_draw():
    assert not planned(cm.find_setups(bars(running=False), DAY, "US100"))
    assert planned(cm.find_setups(bars(running=False), DAY, "US100", cm.Params(require_running=False)))


def test_sell_model_is_the_mirror():
    ss = planned(cm.find_setups(mirror(bars()), DAY, "US100"), side="short")
    assert ss and ss[0].decided_at == ts("08:44")
    assert ss[0].plan.tp1 == pytest.approx(200 - 102.045, abs=0.03)


def test_no_lookahead_plan_identical_without_future_bars():
    full, cut = bars(), bars()
    cut = cut[cut.index <= ts("08:44")]
    a = planned(cm.find_setups(full, DAY, "US100"))[0]
    b = planned(cm.find_setups(cut, DAY, "US100"))[0]
    assert (a.plan.entry, a.plan.stop, a.plan.tp1, a.decided_at) == (b.plan.entry, b.plan.stop, b.plan.tp1, b.decided_at)


def test_outside_the_windows_nothing_is_traded():
    assert not planned(cm.find_setups(bars(), DAY, "US100", cm.Params(windows=("ny_pm_kz",))))


def test_registered():
    from ict_engine.models.registry import modules
    assert modules()["cameron"] is cm
