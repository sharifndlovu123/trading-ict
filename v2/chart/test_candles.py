"""The chart's candle plumbing, on hand-built minutes."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from candles import resample, to_candles, trading_day  # noqa: E402
from fetch import month_starts, parse_csv  # noqa: E402


def minutes(start, prices):
    """One candle a minute from ``start`` (New York clock); each price is that minute's close, the open is the price before."""
    idx = pd.date_range(start, periods=len(prices), freq="1min")
    opens = [prices[0]] + prices[:-1]
    return pd.DataFrame({"open": opens, "high": [max(o, c) + 0.5 for o, c in zip(opens, prices)],
                         "low": [min(o, c) - 0.5 for o, c in zip(opens, prices)], "close": prices}, index=idx)


def test_five_minutes_are_built_from_one_minutes():
    df = minutes("2031-01-06 09:30", [101, 102, 103, 102, 104, 105, 106])
    r = resample(df, "5m")
    assert list(r.index.strftime("%H:%M")) == ["09:30", "09:35"]
    first = r.iloc[0]
    assert (first.open, first.high, first.low, first.close) == (101, 104.5, 100.5, 104)


def test_four_hour_candles_start_at_6pm():
    df = minutes("2031-01-06 17:58", list(range(100, 100 + 6)))                # crosses 6 p.m.? no trading 17:00-18:00, but the clock rule is what is tested
    r = resample(df, "4h")
    assert list(r.index.strftime("%H:%M")) == ["14:00", "18:00"]


def test_a_trading_day_runs_from_6pm_so_sunday_evening_belongs_to_monday():
    sunday = minutes("2031-01-05 18:00", [100, 101, 102])                      # Sunday evening
    monday = minutes("2031-01-06 10:00", [103, 104, 99])
    after = minutes("2031-01-06 18:00", [98, 97])                              # Monday evening: Tuesday's day
    r = resample(pd.concat([sunday, monday, after]), "1D")
    assert list(r.index.strftime("%Y-%m-%d")) == ["2031-01-06", "2031-01-07"]
    assert r.iloc[0].open == 100 and r.iloc[0].close == 99 and r.iloc[0].high == 104.5 and r.iloc[0].low == 98.5
    assert list(trading_day(sunday.index).strftime("%a")) == ["Mon", "Mon", "Mon"]


def test_weeks_and_months_follow_the_trading_day():
    df = pd.concat([minutes("2031-01-05 18:00", [100, 101]), minutes("2031-01-09 12:00", [105, 104]),      # one week (Sunday evening to Thursday)
                    minutes("2031-01-12 18:00", [103, 108]), minutes("2031-01-31 18:00", [110, 111])])     # the next week; then a Friday evening that belongs to February
    w = resample(df, "1W")
    assert list(w.index.strftime("%Y-%m-%d"))[:2] == ["2031-01-06", "2031-01-13"]
    assert w.iloc[0].open == 100 and w.iloc[0].close == 104
    m = resample(df, "1M")
    assert list(m.index.strftime("%Y-%m")) == ["2031-01", "2031-02"]


def test_candles_for_the_page_carry_new_york_clock_time_as_seconds():
    c = to_candles(minutes("2031-01-06 09:30", [101, 102]))
    assert c[0]["time"] == int((pd.Timestamp("2031-01-06 09:30") - pd.Timestamp("1970-01-01")).total_seconds())
    assert c[1]["time"] - c[0]["time"] == 60 and set(c[0]) == {"time", "open", "high", "low", "close"}
    assert len(to_candles(minutes("2031-01-06 09:30", [1, 2, 3, 4]), last=2)) == 2


def test_an_unknown_timeframe_is_refused():
    with pytest.raises(ValueError):
        resample(minutes("2031-01-06 09:30", [1, 2]), "7m")


def test_the_downloaders_csv_is_read_as_utc_minutes():
    df = parse_csv("timestamp,open,high,low,close,volume\n1924992000000,100,101,99,100.5,0.5\n1924992060000,100.5,102,100,101.5,0.7\n")
    assert str(df.index.tz) == "UTC" and len(df) == 2 and df.iloc[1].close == 101.5
    assert parse_csv("timestamp,open,high,low,close,volume\n").empty


def test_which_months_are_fetched():
    from datetime import date
    assert [m.isoformat() for m in month_starts(date(2031, 1, 20), 3)] == ["2030-11-01", "2030-12-01", "2031-01-01"]
