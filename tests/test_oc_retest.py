"""OC-retest pre-registration (research/preregistered-oc-retest-2026-11-15.md) on hand-built cases with known answers:
break = first 1m close beyond the OC edge after the MSS; decided when the leg runs 1R (OC width + buffer) past the edge;
entry = OC edge, stop beyond the OC's far side; TP1 = 2R, final = nearest untaken context level beyond TP1; no look-ahead."""

from types import SimpleNamespace

import pandas as pd

from ict_engine.concepts.events import Event
from ict_engine.models import model_mmxm
from ict_engine.models.model_mmxm import Curve, oc_retest, oc_retest_targets
from tests.test_model_2022 import path_bars

NY = "America/New_York"
P = model_mmxm.Params(entry="oc_retest")       # stop_buffer 0.25


def ts(hm):
    return pd.Timestamp(f"2024-01-09 {hm}", tz=NY)


CURVE = Curve(ts("08:00"), ts("09:00"), 101.0, 100.0, (99.0,), (ts("09:30"),), (ts("09:15"),))   # OC 100–101
MSS = Event("mss", "1m", "bull", ts("10:06"), ts("10:05"), 99.5, 99.5)


def day(peak=103.0, peak_at="10:45"):
    """Down from the OC to 97 at 10:00, back up through 101 at ~10:25, on to ``peak`` at ``peak_at``, back to 100.5."""
    b = path_bars([("2024-01-09 07:00", 100.5), ("2024-01-09 09:00", 100.5), ("2024-01-09 10:00", 97.0),
                   ("2024-01-09 10:30", 101.5), (f"2024-01-09 {peak_at}", peak), ("2024-01-09 12:00", 100.5),
                   ("2024-01-09 15:59", 100.5)], "2024-01-09 07:00", "2024-01-09 16:00")
    return b.assign(close_ts=b.index)


def test_decided_when_the_leg_runs_1r_past_the_broken_oc():
    d = day()
    decided, entry, stop = oc_retest(CURVE, True, MSS, d, P)
    assert entry == 101.0 and stop == 99.75                         # R = 1.25
    first = d.index[d.high >= 102.25][0]
    assert decided == first and decided > d.index[(d.index >= ts("10:05")) & (d.close > 101.0)][0]


def test_no_decision_without_a_break_or_without_the_1r_run():
    assert "never closed above" in oc_retest(CURVE, True, MSS, day(peak=100.8, peak_at="10:31").assign(
        close=lambda x: x.close.clip(upper=100.9), high=lambda x: x.high.clip(upper=100.95)), P)
    assert "never ran 1R" in oc_retest(CURVE, True, MSS, day(peak=102.0), P)


def test_no_lookahead():
    d = day()
    decided, *_ = oc_retest(CURVE, True, MSS, d, P)
    assert oc_retest(CURVE, True, MSS, d[d.index <= decided], P)[0] == decided


def test_targets_tp1_2r_final_nearest_untaken_context_level_beyond_tp1():
    d = day()
    ctx = SimpleNamespace(levels={"asia_high": 103.2, "pdh": 104.0, "pwh": 110.0})
    # by 11:00 the high 103.0 is seen; TP1 = 101 + 2.5 = 103.5 → asia 103.2 is inside TP1 → final PDH 104
    assert oc_retest_targets(101.0, 1.25, True, ctx, d, ts("11:00")) == (103.5, "2R", 104.0, "pdh")
    taken = SimpleNamespace(levels={"pdh": 102.9})
    assert oc_retest_targets(101.0, 1.25, True, taken, d, ts("11:00"))[2:] == (103.5, "2R")


def test_short_mirror():
    b = path_bars([("2024-01-09 07:00", 100.5), ("2024-01-09 09:00", 100.5), ("2024-01-09 10:00", 104.0),
                   ("2024-01-09 10:30", 99.5), ("2024-01-09 10:45", 98.0), ("2024-01-09 15:59", 100.0)],
                  "2024-01-09 07:00", "2024-01-09 16:00").assign(close_ts=lambda x: x.index)
    mss = Event("mss", "1m", "bear", ts("10:06"), ts("10:05"), 103.5, 103.5)
    decided, entry, stop = oc_retest(CURVE, False, mss, b, P)
    assert entry == 100.0 and stop == 101.25 and b.loc[decided].low <= 98.75
