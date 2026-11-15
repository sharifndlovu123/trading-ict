"""Gravitation signal (research/scripts/gravitation_test.py) on hand-built candles: the first 15m displacement after
08:30 that closes beyond everything traded since 00:00 gives the side; a big candle that stays inside the range is not
a signal; nothing after the candle's close is read."""
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from gravitation_test import signal  # noqa: E402
from tests.test_model_2022 import path_bars  # noqa: E402

D = date(2024, 1, 10)


def chop(until, lo=100.0, hi=101.0):
    """15-minute zigzag between lo and hi from Jan 8 to ``until``."""
    pts, t, up = [], pd.Timestamp("2024-01-08 00:00"), True
    while t <= pd.Timestamp(until):
        pts.append((str(t), hi if up else lo)); up = not up; t += pd.Timedelta(minutes=15)
    return pts


def test_up_signal_on_a_displacement_close_above_the_midnight_range():
    pts = chop("2024-01-10 09:00") + [("2024-01-10 09:14", 110.0), ("2024-01-10 12:00", 109.0)]
    s = signal(path_bars(pts, "2024-01-08 00:00", "2024-01-10 13:00"), D)
    assert s is not None and s[0] == "up"
    assert s[1] == pd.Timestamp("2024-01-10 09:14", tz="America/New_York")   # close_ts = the candle's last minute and s[2] > 101.0


def test_down_signal_mirror():
    pts = chop("2024-01-10 09:00") + [("2024-01-10 09:14", 91.0), ("2024-01-10 12:00", 92.0)]
    s = signal(path_bars(pts, "2024-01-08 00:00", "2024-01-10 13:00"), D)
    assert s is not None and s[0] == "down"


def test_no_signal_when_the_big_candle_stays_inside_the_range_or_comes_before_0830():
    pts = chop("2024-01-10 06:00") + [("2024-01-10 06:14", 110.0), ("2024-01-10 06:30", 105.0)] + \
          [(str(pd.Timestamp("2024-01-10 06:30") + pd.Timedelta(minutes=15 * i)), 104.0 + (i % 2)) for i in range(1, 22)]
    assert signal(path_bars(pts, "2024-01-08 00:00", "2024-01-10 13:00"), D) is None


def test_no_lookahead_bars_after_noon_change_nothing():
    pts = chop("2024-01-10 09:00") + [("2024-01-10 09:14", 110.0), ("2024-01-10 12:00", 109.0), ("2024-01-10 15:00", 50.0)]
    b = path_bars(pts, "2024-01-08 00:00", "2024-01-10 16:00")
    assert signal(b, D) == signal(b[b.index < pd.Timestamp("2024-01-10 12:00", tz="America/New_York")], D)
