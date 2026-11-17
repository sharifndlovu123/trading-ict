"""Measured spreads from Dukascopy bid/ask bars: hourly table, and the no-look-ahead expected cost."""

from datetime import date

import pandas as pd
import pytest

from ict_engine.data import spreads as sp

NY = "America/New_York"


def bars(days, hours, spread_of):
    """bid/ask 1m bars for the given days × hours; ask = bid + spread_of(day, hour)."""
    idx = [pd.Timestamp(f"{d} {h:02d}:{m:02d}", tz=NY) for d in days for h in hours for m in range(60)]
    bid = pd.DataFrame({"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0}, index=pd.DatetimeIndex(idx))
    s = pd.Series([spread_of(t.date().isoformat(), t.hour) for t in bid.index], index=bid.index)
    ask = bid.add(s, axis=0)
    return bid, ask


def test_minute_spread_is_ask_minus_bid_and_never_negative():
    bid, ask = bars(["2024-01-08"], [9], lambda d, h: 0.5)
    ask.iloc[0, ask.columns.get_loc("close")] = 99.0          # a crossed quote
    s = sp.minute_spreads(bid, ask)
    assert s.iloc[1] == pytest.approx(0.5) and s.iloc[0] == 0.0


def test_hourly_table_takes_the_median_per_hour():
    bid, ask = bars(["2024-01-08"], [9, 10], lambda d, h: 0.4 if h == 9 else 0.2)
    t = sp.hourly_table(sp.minute_spreads(bid, ask))
    assert t.loc[pd.Timestamp("2024-01-08 09:00", tz=NY), "median"] == pytest.approx(0.4)
    assert t.loc[pd.Timestamp("2024-01-08 10:00", tz=NY), "n"] == 30          # half-hour buckets


def test_expected_spread_uses_only_previous_days_same_hour():
    days = ["2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11", "2024-01-12", "2024-01-15", "2024-01-16"]
    # spread rises 0.1 per day at 09:00; the 16th itself is huge (must NOT be used for the 16th)
    val = {d: 0.1 * (i + 1) for i, d in enumerate(days)}
    val["2024-01-16"] = 9.0
    bid, ask = bars(days, [9, 10], lambda d, h: val[d] if h == 9 else 0.05)
    book = sp.SpreadBook({"US100": sp.expected_table(sp.hourly_table(sp.minute_spreads(bid, ask)), lookback=5)})
    # previous 5 trading days before the 16th at 09:00: 0.2 0.3 0.4 0.5 0.6 → median 0.4
    assert book.spread("US100", pd.Timestamp("2024-01-16 09:40", tz=NY)) == pytest.approx(0.4)
    assert book.spread("US100", pd.Timestamp("2024-01-16 10:05", tz=NY)) == pytest.approx(0.05)


def test_unknown_hour_or_asset_returns_none():
    book = sp.SpreadBook({})
    assert book.spread("US100", pd.Timestamp("2024-01-16 09:40", tz=NY)) is None


def test_build_and_load_round_trip(tmp_path):
    days = ["2024-01-08", "2024-01-09"]
    bid, ask = bars(days, [9], lambda d, h: 0.3)
    path = sp.save("US100", sp.expected_table(sp.hourly_table(sp.minute_spreads(bid, ask)), lookback=1), root=tmp_path)
    book = sp.SpreadBook.load(root=tmp_path)
    assert path.exists() and book.spread("US100", pd.Timestamp("2024-01-09 09:10", tz=NY)) == pytest.approx(0.3)


def test_half_hours_separate_premarket_from_the_cash_open():
    days = ["2024-01-08", "2024-01-09"]
    bid, ask = bars(days, [9], lambda d, h: 0.0)
    pre = ask.index.minute < 30
    ask.loc[pre] = bid.loc[pre] + 3.45                      # 09:00–09:29 wide, 09:30–09:59 tight
    ask.loc[~pre] = bid.loc[~pre] + 1.45
    book = sp.SpreadBook({"US100": sp.expected_table(sp.hourly_table(sp.minute_spreads(bid, ask)), lookback=1)})
    assert book.spread("US100", pd.Timestamp("2024-01-09 09:10", tz=NY)) == pytest.approx(3.45)
    assert book.spread("US100", pd.Timestamp("2024-01-09 09:40", tz=NY)) == pytest.approx(1.45)
