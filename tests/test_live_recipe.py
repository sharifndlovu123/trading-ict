"""Live sheet helpers (research/scripts/live_recipe.py) on hand-built bars."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import live_recipe as lr  # noqa: E402

NY = "America/New_York"


def bars(rows, start):
    idx = pd.date_range(pd.Timestamp(start, tz=NY), periods=len(rows), freq="1min")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)


def test_merge_appends_new_bars_and_the_fresh_copy_wins():
    base = bars([(1, 2, 0, 1), (1, 3, 1, 2)], "2024-01-09 10:00")
    fresh = bars([(1, 9, 1, 5), (5, 6, 4, 5)], "2024-01-09 10:01")       # 10:01 revised, 10:02 new
    m = lr.merge(base, fresh)
    assert len(m) == 3 and m.high.tolist() == [2, 9, 6] and m.index.is_monotonic_increasing
    assert lr.merge(base, pd.DataFrame()) is base                         # a failed poll changes nothing


def test_candles_resample_and_show_new_york_wall_clock():
    b = bars([(10, 11, 9, 10), (10, 12, 10, 11), (11, 11, 8, 9), (9, 10, 9, 10), (10, 10, 10, 10)], "2024-01-09 09:58")
    c = lr.candles(b, "5min", pd.Timestamp("2024-01-09 00:00", tz=NY))
    assert [(x["open"], x["high"], x["low"], x["close"]) for x in c] == [(10, 12, 9, 11), (11, 11, 8, 10)]
    assert pd.Timestamp(c[1]["time"], unit="s").strftime("%H:%M") == "10:00"   # NY 10:00 shown as 10:00
    assert lr.candles(b, "5min", pd.Timestamp("2024-01-09 10:00", tz=NY))[0]["open"] == 11  # ``since`` cuts history


def test_state_of_reads_a_running_trade_as_open():
    """Bars end at "now", so the simulator's time exit before 16:00 means the trade is still open."""
    t = lambda h: pd.Timestamp(f"2024-01-09 {h}", tz=NY)  # noqa: E731
    close, exp = t("16:00"), t("11:00")
    assert lr.state_of("time_exit", True, t("10:30"), close, exp) == "open"
    assert lr.state_of("time_exit", True, t("16:05"), close, exp) == "closed at the session end"
    assert lr.state_of("tp1", True, t("10:30"), close, exp) == "TP1 hit"
    assert lr.state_of("stop", True, t("10:30"), close, exp) == "stopped"
    assert lr.state_of(None, False, t("10:30"), close, exp) == "waiting for the fill"
    assert lr.state_of(None, False, t("11:00"), close, exp) == "not filled"
    assert lr.state_of("missed", False, t("10:30"), close, exp).startswith("missed")
