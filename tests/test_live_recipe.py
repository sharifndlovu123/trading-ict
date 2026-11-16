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


def test_strength_reads_the_session_move_and_the_place_in_yesterdays_range():
    day = bars([(100, 110, 90, 100)] * 60, "2024-01-09 10:00")              # yesterday: range 90 → 110
    eve = bars([(104, 105, 103, 104)] * 30 + [(104, 106, 104, 105)], "2024-01-09 18:00")   # session opens 104, last 105
    s = lr.strength(pd.concat([day, eve]), pd.Timestamp("2024-01-09 18:31", tz=NY), adr=20.0)
    assert s["session_move_adr"] == 0.05 and s["prev_range_pos"] == 75 and s["session_range_adr"] == 0.15


def test_adr_of_uses_finished_days_only():
    days = pd.concat([bars([(100, 100 + k, 100, 100)] * 3, f"2024-01-{d:02d} 10:00") for d, k in zip(range(2, 9), (10, 10, 10, 10, 10, 10, 50))])
    assert lr.adr_of(days, pd.Timestamp("2024-01-08 12:00", tz=NY)) == 10.0      # 8 Jan itself (range 50) is not counted


def test_entry_areas_show_the_breaker_body_only_once_it_is_known():
    # one 1m bar per hour = the 1h candle. Low (01:00) → high 103 (04:00, body 100.5–102) → a minor lower high
    # (06:00) → lower low (08:00) → the 10:00 candle closes above 103: a bullish breaker, known at 11:00
    rows = [(98, 98, 96, 97), (97, 97, 95, 96), (96, 98, 96, 97.5), (97.5, 101, 97, 100.5), (100.5, 103, 100, 102),
            (102, 102.2, 99.5, 99.8), (99.8, 102.5, 99.2, 99.4), (99.4, 99.5, 95, 95.5), (95.5, 98.5, 94, 98.2),
            (98.2, 101, 98, 100.5), (100.5, 104, 100, 103.6), (103.6, 104.5, 103, 104)]
    idx = pd.date_range(pd.Timestamp("2024-01-09 00:00", tz=NY), periods=len(rows), freq="1h")
    b = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    br = [a for a in lr.entry_areas(b, pd.Timestamp("2024-01-09 12:00", tz=NY), adr=10.0) if a["kind"] == "breaker"]
    assert len(br) == 1
    a = br[0]
    assert (a["side"], a["bottom"], a["top"], a["body_pct"], a["where"]) == ("buy", 100.5, 102.0, 50, "below")
    assert a["from"].endswith("04:00") and pd.Timestamp(a["t0"], unit="s").strftime("%H:%M") == "04:00"
    early = lr.entry_areas(b, pd.Timestamp("2024-01-09 10:30", tz=NY), adr=10.0)        # the 10:00 candle is still open
    assert not [x for x in early if x["kind"] == "breaker"]
    assert all(x["inside"] or x["where"] == ("below" if x["side"] == "buy" else "above")
               for x in lr.entry_areas(b, pd.Timestamp("2024-01-09 12:00", tz=NY), adr=10.0))


def test_order_block_needs_the_very_next_candle_to_engulf_it():
    # up candle (100 → 102), then one candle closing under its open: a sell order block = its body, known at that close
    one = bars([(100, 102.5, 99.5, 102), (102, 102.2, 98, 98.5), (98.5, 99, 97, 97.5)], "2024-01-09 10:00")
    ob = lr.engulfed_blocks(one, "1m")
    assert [(e.direction, e.bottom, e.top, e.meta["beyond_wick"]) for e in ob] == [("bear", 100.0, 102.0, True)]
    assert ob[0].origin_ts == one.index[0] and ob[0].ts == one.index[1]
    # the same fall spread over two candles: the first does not close under the open → no order block
    two = bars([(100, 102.5, 99.5, 102), (102, 102.2, 100.5, 100.8), (100.8, 101, 98, 98.5)], "2024-01-09 10:00")
    assert lr.engulfed_blocks(two, "1m") == []
    buy = bars([(102, 102.5, 99.5, 100), (100, 102.4, 99.8, 102.3)], "2024-01-09 10:00")       # mirror; close inside the wick
    assert [(e.direction, e.bottom, e.top, e.meta["beyond_wick"]) for e in lr.engulfed_blocks(buy, "1m")] == [("bull", 100.0, 102.0, False)]


def test_higher_timeframe_candles_follow_the_futures_clock():
    # 1h bars from Sunday 18:00 to Tuesday 16:00 (no 17:00 hour), each bar open = close = its number
    idx = [t for t in pd.date_range(pd.Timestamp("2024-01-07 18:00", tz=NY), pd.Timestamp("2024-01-09 16:00", tz=NY), freq="1h") if t.hour != 17]
    h1 = pd.DataFrame({"open": range(len(idx)), "high": [x + 0.5 for x in range(len(idx))], "low": [x - 0.5 for x in range(len(idx))],
                       "close": range(len(idx))}, index=pd.DatetimeIndex(idx), dtype=float)
    h4 = lr.htf_candles(h1, "4h")
    assert pd.Timestamp(h4[0]["time"], unit="s").strftime("%a %H:%M") == "Sun 18:00" and (h4[0]["open"], h4[0]["close"]) == (0, 3)
    assert pd.Timestamp(h4[1]["time"], unit="s").strftime("%H:%M") == "22:00"
    d = lr.htf_candles(h1, "1D")                                   # Sunday evening belongs to Monday's candle
    assert [pd.Timestamp(x["time"], unit="s").strftime("%a %d") for x in d] == ["Mon 08", "Tue 09"]
    assert d[0]["open"] == 0 and d[0]["close"] == 22 and d[1]["open"] == 23 and d[0]["high"] == 22.5
    w = lr.htf_candles(h1, "1W")
    assert len(w) == 1 and pd.Timestamp(w[0]["time"], unit="s").strftime("%a %d") == "Mon 08" and w[0]["close"] == len(idx) - 1
