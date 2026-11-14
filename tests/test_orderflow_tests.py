"""Order-flow test measures on hand-built data with known answers."""

import numpy as np
import pandas as pd
import pytest

from ict_engine.eval import orderflow_tests as ot

NY = "America/New_York"


def T(s):
    return pd.Timestamp(s, tz=NY)


def test_cluster_diff_matches_difference_of_means_and_clusters_widen_se():
    y = [1, 1, 0, 0, 1, 0, 0, 0]
    x = [1, 1, 1, 1, 0, 0, 0, 0]
    b, se, z = ot.cluster_diff(y, x, range(8))          # one cluster per row
    assert b == pytest.approx(0.5 - 0.25)
    b2, se2, _ = ot.cluster_diff(y, x, [0, 0, 1, 1, 2, 2, 3, 3])   # duplicated outcomes inside clusters
    assert b2 == pytest.approx(b) and se2 > 0


def test_absorption_finds_the_stop_print_volume_near_it_and_overshoot():
    idx = [T("2024-01-09 10:00:05"), T("2024-01-09 10:00:20"), T("2024-01-09 10:01:00"),
           T("2024-01-09 10:03:00"), T("2024-01-09 10:07:00")]
    tr = pd.DataFrame({"price": [100.5, 100.0, 99.5, 101.0, 95.0], "size": [5, 2, 3, 4, 9]}, index=idx)
    a = ot.absorption(tr, T("2024-01-09 10:00"), "long", 100.0, 2.0)
    assert a["t0"] == idx[1]                              # first print at/through the stop
    assert a["vol_near"] == 2 + 3 + 4                     # 100.0, 99.5, 101.0 within ±4 ticks (1.0); 10:07 is outside 5 min
    assert a["F"] == pytest.approx(0.5 / 2.0)             # lowest 99.5 → 0.5 beyond, risk 2
    assert ot.absorption(tr, T("2024-01-09 10:00"), "short", 110.0, 2.0) == {}


def test_baseline_uses_only_previous_days():
    days = pd.bdate_range("2024-01-01", periods=4)
    idx = [T(f"{d.date()} 10:0{m}") for d in days for m in range(5)]
    vol = [float(i // 5 + 1) for i in range(len(idx))]  # day k: every minute volume k → 5-min block 5k
    b = ot.baseline_5m(pd.DataFrame({"volume": vol}, index=pd.DatetimeIndex(idx)), days=2)
    assert b[(days[2].date(), 10.0)] == np.median([5.0, 10.0])
    assert b[(days[3].date(), 10.0)] == np.median([10.0, 15.0])
    assert (days[1].date(), 10.0) not in b.index          # not enough history


def test_first_after_tp1_vs_mirror():
    idx = pd.DatetimeIndex([T("2024-01-09 10:01"), T("2024-01-09 10:02"), T("2024-01-09 10:03")])
    bars = pd.DataFrame({"high": [99, 103, 99], "low": [97, 98, 90]}, index=idx)
    # long stopped at 98, TP1 103 → mirror 93
    assert ot.first_after(bars, T("2024-01-09 10:00"), T("2024-01-09 16:00"), "long", 103, 98) == "tp1"
    assert ot.first_after(bars, T("2024-01-09 10:02"), T("2024-01-09 16:00"), "long", 103, 98) == "mirror"
    assert ot.first_after(bars, T("2024-01-09 10:03"), T("2024-01-09 16:00"), "long", 103, 98) == "neither"
