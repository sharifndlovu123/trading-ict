"""2022 model on a hand-built day where the right answer is known.

Story (Tue 2024-01-09): bullish daily bias (Mon took Fri's high with a higher low).
In the NY AM killzone price sells off, sweeps the previous day low (PDL 95), then
one displacement candle breaks the last swing high (bullish MSS) and leaves a
FVG. Price retraces into the FVG, then rallies through PDH.
"""

from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd
import pytest

from ict_engine.models.model_2022 import Params, find_setups
from ict_engine.sim.run import run_day

NY = "America/New_York"
DAY = date(2024, 1, 9)


def path_bars(points, start, end):
    """1m bars following straight lines between (time, price) waypoints; tiny wicks."""
    idx = pd.date_range(start, end, freq="1min", tz=NY, inclusive="left")
    ts = pd.DatetimeIndex([pd.Timestamp(t, tz=NY) for t, _ in points])
    px = np.interp(idx.asi8, ts.asi8, [p for _, p in points])
    close = pd.Series(px, index=idx)
    # open halfway from the previous close: like real bars, a turning bar's high is not repeated next bar
    open_ = ((close.shift(1) + close) / 2).fillna(close.iloc[0])
    hi = np.maximum(open_, close) + 0.02
    lo = np.minimum(open_, close) - 0.02
    return pd.DataFrame({"open": open_, "high": hi, "low": lo, "close": close})


def history(fri=(90, 110), mon=(95, 112)):
    """Fri 5 Jan and Mon 8 Jan sessions (18:00 → 17:00) with given (low, high)."""
    f = path_bars([("2024-01-04 18:00", 100), ("2024-01-05 03:00", fri[0]),
                   ("2024-01-05 10:00", fri[1]), ("2024-01-05 17:00", 101)],
                  "2024-01-04 18:00", "2024-01-05 17:00")
    m = path_bars([("2024-01-07 18:00", 101), ("2024-01-08 03:00", mon[0]),
                   ("2024-01-08 10:00", mon[1]), ("2024-01-08 17:00", 99)],
                  "2024-01-07 18:00", "2024-01-08 17:00")
    return pd.concat([f, m])


def setup_day():
    pts = [
        ("2024-01-08 18:00", 99.0), ("2024-01-09 08:00", 99.0),
        ("2024-01-09 08:20", 96.0),            # sell-off
        ("2024-01-09 08:23", 96.6),            # bounce → swing high 96.6
        ("2024-01-09 08:40", 95.2),
        ("2024-01-09 08:45", 94.5),            # sweep of PDL 95
        ("2024-01-09 08:46", 95.0),
        ("2024-01-09 08:47", 97.0),            # one displacement candle closes above 96.6 → MSS
        ("2024-01-09 08:48", 97.4),
        ("2024-01-09 09:05", 100.5),           # leg high
        ("2024-01-09 09:15", 95.3),            # retrace into the displacement FVG
        ("2024-01-09 09:45", 113.0),           # rally through PDH 112
        ("2024-01-09 16:00", 112.0),
    ]
    return path_bars(pts, "2024-01-08 18:00", "2024-01-09 16:30")


def bars(**hist_kw):
    return pd.concat([history(**hist_kw), setup_day()])


def traded(setups):
    return [s for s in setups if s.plan is not None]


def test_finds_the_long_with_correct_evidence_and_plan():
    ss = traded(find_setups(bars(), DAY, "US100"))
    assert len(ss) >= 1
    s = ss[0]
    assert s.side == "long" and s.tags["window"] == "ny_am_kz"
    assert pd.Timestamp("2024-01-09 08:47", tz=NY) <= s.decided_at <= pd.Timestamp("2024-01-09 08:50", tz=NY)
    assert set(s.evidence) == {"shift", "liquidity", "fvg"}
    p = s.plan
    assert p.stop < 94.5 < p.entry < p.tp1 <= p.final_target       # stop below the sweep extreme
    assert all(g.passed for g in s.gates)


def test_trade_wins_on_the_rally():
    s = traded(run_day(bars(), DAY, "US100"))[0]
    assert s.result.filled_at is not None and s.result.vote and s.result.r > 0


def test_stop_is_never_on_the_wrong_side():
    for s in find_setups(bars(), DAY, "US100", Params(use_bias=False, use_pricing=False, use_poi=False)):
        if s.plan:
            assert (s.plan.stop < s.plan.entry) if s.side == "long" else (s.plan.stop > s.plan.entry)


def test_bearish_bias_blocks_the_long_at_the_bias_gate():
    # Mon makes a lower high and lower low than Fri → bearish daily bias
    ss = find_setups(bars(fri=(90, 113), mon=(89, 112)), DAY, "US100")
    longs = [s for s in ss if s.side == "long" and "fvg" in s.evidence]
    assert longs and all(s.plan is None for s in longs)
    assert any(s.failed_gate == "bias" for s in longs)


def test_outside_window_blocks_at_time_gate():
    ss = find_setups(bars(), DAY, "US100", Params(windows=("ny_pm_kz",)))
    long = [s for s in ss if s.side == "long" and "fvg" in s.evidence][0]
    assert long.plan is None and long.failed_gate == "time"


def test_no_lookahead_plan_is_identical_with_future_bars_removed():
    full = bars()
    s = traded(find_setups(full, DAY, "US100"))[0]
    cut = full[full.index <= s.decided_at]
    s2 = traded(find_setups(cut, DAY, "US100"))[0]
    assert (s2.plan.entry, s2.plan.stop) == (s.plan.entry, s.plan.stop)
    assert s2.decided_at == s.decided_at
