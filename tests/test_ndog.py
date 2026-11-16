"""Opening-gap study (research/scripts/ndog_study.py) on hand-built bars with known answers."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import ndog_study as nd  # noqa: E402

NY = "America/New_York"


def arr(rows):
    a = np.array(rows, dtype=float)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]


def test_sessions_find_the_evening_open_after_the_break():
    day = pd.date_range("2024-01-09 09:00", "2024-01-09 16:14", freq="1min", tz=NY)
    eve = pd.date_range("2024-01-09 18:00", "2024-01-10 16:54", freq="1min", tz=NY)
    idx = day.append(eve)
    b = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0}, index=idx)
    b.loc[eve[0], "open"] = 103.0
    s = nd.sessions(b)
    assert len(s) == 1 and s[0]["open_ts"] == eve[0] and s[0]["prev_close"] == 100.0 and s[0]["open"] == 103.0
    assert not s[0]["weekend"] and s[0]["end_i"] == len(idx)                    # the session runs to 16:55 the next day


def test_trade_counts_the_stop_first_and_exits_at_the_session_end():
    o, h, lo, c = arr([(100, 101, 99.5, 100.5), (100.5, 104.5, 97, 104)])       # both in one bar → stop
    assert nd.trade(o, h, lo, c, 0, 2, True, 100, 98, 104)["exit"] == "stop"
    o, h, lo, c = arr([(100, 101, 99.5, 100.5), (100.5, 104.5, 100, 104)])
    t = nd.trade(o, h, lo, c, 0, 2, True, 100, 98, 104)
    assert t["exit"] == "tp" and t["r"] == pytest.approx(2.0)
    o, h, lo, c = arr([(100, 101, 99.5, 100.5), (100.5, 101.5, 100, 101)])
    assert nd.trade(o, h, lo, c, 0, 2, True, 100, 98, 104)["r"] == pytest.approx(0.5)   # time exit at the last close
    assert nd.trade(o, h, lo, c, 0, 2, False, 100, 102, 96)["r"] == pytest.approx(-0.5)


def test_fill_stats_and_the_at_open_trade_for_a_gap_above():
    # previous close 110, open 100: the gap is above → a buy closes it; 50% = 105
    o, h, lo, c = arr([(100, 101, 99, 100), (100, 106, 100, 105), (105, 110.5, 104, 110)])
    s = {"open_i": 0, "end_i": 3, "prev_close": 110.0, "open": 100.0}
    assert nd.fill_stats(o, h, lo, c, s) == {"ce_min": 1, "full_min": 2}
    t = nd.at_open(o, h, lo, c, s)
    assert (t["entry"], t["stop"], t["target"]) == (100.0, 90.0, 110.0) and t["exit"] == "tp" and t["r"] == pytest.approx(1.0)


def test_after_sweep_buys_the_15m_close_back_above_the_swept_low():
    # gap above (close 120, open 100). A low of 98 stands for the first minutes; later 97 trades (sweep), then a 15m
    # candle closes at 99 (> 98) → buy 99, stop 96.5 (the sweep's low), target 120.
    n = 60
    o = np.full(n, 100.0); h = np.full(n, 101.0); lo = np.full(n, 99.0); c = np.full(n, 100.0)
    mins = (18 * 60 + np.arange(n)) % 1440
    lo[2] = 98.0                                           # the resting low
    lo[20] = 97.0; lo[21] = 96.5; c[20] = 97.5; c[21] = 97.2
    for k in range(22, 30):
        c[k] = 99.0
    h[50] = 121.0                                          # the gap closes later
    s = {"open_i": 0, "end_i": n, "prev_close": 120.0, "open": 100.0}
    t = nd.after_sweep(o, h, lo, c, mins, s, old_min=10)
    assert t["swept"] == 98.0 and t["entry"] == 99.0 and t["stop"] == 96.5 and t["entry_i"] == 29   # 18:29 closes a 15m candle
    assert t["exit"] == "tp" and t["r"] == pytest.approx((120 - 99) / 2.5)
    h[10] = 121.0                                          # the gap already closed before the sweep → no trade
    assert nd.after_sweep(o, h, lo, c, mins, s, old_min=10) is None
