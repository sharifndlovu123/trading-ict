import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import live_snapshot as ls  # noqa: E402


def _doc():
    m1 = [{"time": 60 * i, "open": 100 + i, "high": 101 + i, "low": 99 + i, "close": 100.5 + i} for i in range(20)]
    five = [{"time": 300 * k, "open": 100 + 5 * k, "high": 105 + 5 * k, "low": 99 + 5 * k, "close": 104.5 + 5 * k} for k in range(4)]
    day = [{"time": -86400, "open": 90, "high": 95, "low": 85, "close": 92}, {"time": 0, "open": 100, "high": 120, "low": 99, "close": 119.5}]
    week = [{"time": -86400, "open": 90, "high": 120, "low": 85, "close": 119.5}]
    return {"day": "1970-01-01", "now": "x", "assets": {"A": {"adr": 10, "levels": {}, "candles": {"1m": m1, "5m": five, "1D": day, "1W": week}}}}


def test_nothing_after_the_cut_is_in_the_snapshot():
    snap = ls.cut(_doc(), at=7 * 60)                       # seven closed 1m candles: 0..6
    c = snap["assets"]["A"]["candles"]
    assert [x["time"] for x in c["1m"]] == [0, 60, 120, 180, 240, 300, 360]
    assert c["5m"][0] == {"time": 0, "open": 100, "high": 105, "low": 99, "close": 104.5}      # a closed 5m candle is kept as it was
    assert c["5m"][1] == {"time": 300, "open": 105, "high": 107, "low": 104, "close": 106.5}   # the forming one is rebuilt from two 1m candles
    assert c["1D"][-1]["high"] == 107 and c["1D"][-1]["close"] == 106.5                         # today so far, not the whole day
    assert c["1W"][-1]["high"] == 107 and c["1W"][-1]["low"] == 85 and c["1W"][-1]["open"] == 90
    assert snap["assets"]["A"]["last"] == 106.5 and snap["mode"] == "replay"


def test_a_cut_on_a_candle_boundary_does_not_repeat_the_last_candle():
    c = ls.cut(_doc(), at=10 * 60)["assets"]["A"]["candles"]["5m"]          # exactly two closed 5m candles
    assert [x["time"] for x in c] == [0, 300]
