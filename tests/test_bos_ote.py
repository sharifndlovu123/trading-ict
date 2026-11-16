"""BOS → OTE study (research/scripts/bos_ote_study.py) on hand-built bars with known answers."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import bos_ote_study as bo  # noqa: E402

NY = "America/New_York"


def arrays(rows, start="2024-01-09 10:00"):
    idx = pd.date_range(pd.Timestamp(start, tz=NY), periods=len(rows), freq="1min")
    a = np.array(rows, dtype=float)
    return idx, idx.tz_convert("UTC").as_unit("ns").asi8, a[:, 0], a[:, 1], a[:, 2], a[:, 3]


def test_session_flat_follows_the_futures_session():
    t = lambda s: pd.Timestamp(s, tz=NY)  # noqa: E731
    assert bo.session_flat(t("2024-01-09 10:00")) == t("2024-01-09 16:55")
    assert bo.session_flat(t("2024-01-09 18:48")) == t("2024-01-10 16:55")        # the evening belongs to the next day
    assert bo.session_flat(t("2024-01-07 18:48")) == t("2024-01-08 16:55")        # Sunday open → Monday
    assert bo.session_flat(t("2024-01-12 18:30")) == t("2024-01-15 16:55")        # Friday evening → Monday


def test_short_fills_at_the_retrace_level_and_wins_at_the_range_low():
    # range 110 (far) → 100 (near); 0.62 → entry 106.2, stop 110, TP1 100: reward:risk 6.2 / 3.8
    idx, ix, o, h, lo, c = arrays([(101, 102, 100.5, 101), (101, 105, 101, 104), (104, 106.5, 104, 105), (105, 105, 99.5, 100)])
    ev = {"ts": idx[0], "short": True, "far": 110.0, "near0": 100.0}
    t = bo.replay(ix, o, h, lo, c, ev, 0.62, None)
    assert t["entry"] == pytest.approx(106.2) and t["filled_at"] == idx[2]
    assert t["exit"] == "tp1" and t["r"] == pytest.approx(6.2 / 3.8) and t["tp1"] == 100.0


def test_the_leg_stretches_before_the_retrace_and_the_entry_follows_it():
    # price first falls to 95: the range is 110 → 95, so 0.62 is 104.3 (not 106.2)
    idx, ix, o, h, lo, c = arrays([(101, 101, 95, 96), (96, 104.5, 96, 104), (104, 104, 100, 101), (101, 111, 101, 110)])
    t = bo.replay(ix, o, h, lo, c, {"ts": idx[0], "short": True, "far": 110.0, "near0": 100.0}, 0.62, None)
    assert t["entry"] == pytest.approx(95 + 0.62 * 15) and t["filled_at"] == idx[1] and t["tp1"] == 95.0
    assert t["exit"] == "stop" and t["r"] == -1.0


def test_long_side_mirrors_and_a_fill_bar_through_the_stop_is_a_loss():
    idx, ix, o, h, lo, c = arrays([(109, 109.5, 108, 109), (109, 109, 103, 104), (104, 111, 104, 110)])
    ev = {"ts": idx[0], "short": False, "far": 100.0, "near0": 110.0}                 # range 100 → 110, long at 103.8
    t = bo.replay(ix, o, h, lo, c, ev, 0.62, None)
    assert t["entry"] == pytest.approx(103.8) and t["exit"] == "tp1" and t["r"] == pytest.approx(6.2 / 3.8)
    idx, ix, o, h, lo, c = arrays([(109, 109.5, 108, 109), (109, 109, 99, 100)])
    assert bo.replay(ix, o, h, lo, c, ev, 0.62, None)["exit"] == "stop"


def test_a_break_the_other_way_cancels_the_resting_order():
    idx, ix, o, h, lo, c = arrays([(101, 102, 100.5, 101), (101, 102, 101, 102), (102, 107, 102, 106), (106, 106, 99, 100)])
    ev = {"ts": idx[0], "short": True, "far": 110.0, "near0": 100.0}
    assert bo.replay(ix, o, h, lo, c, ev, 0.62, idx[2].tz_convert("UTC").value) is None
    assert bo.replay(ix, o, h, lo, c, ev, 0.62, None)["filled_at"] == idx[2]        # without it the order fills
