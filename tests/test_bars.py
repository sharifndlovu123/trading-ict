import pandas as pd
import pytest

from ict_engine.concepts.bars import resample

NY = "America/New_York"


def minute_bars(start, end, base=100.0):
    idx = pd.date_range(start, end, freq="1min", tz=NY)
    n = len(idx)
    close = pd.Series(range(n), index=idx, dtype=float) + base
    return pd.DataFrame({"open": close - 0.5, "high": close + 1, "low": close - 1,
                         "close": close, "volume": 1.0}, index=idx)


def test_5m_ohlc_values():
    b = minute_bars("2024-01-09 10:00", "2024-01-09 10:09")
    r = resample(b, "5m")
    assert len(r) == 2
    first = r.iloc[0]
    assert first.open == 99.5 and first.close == 104 and first.high == 105 and first.low == 99
    assert first.volume == 5
    assert first.close_ts == pd.Timestamp("2024-01-09 10:04", tz=NY)


def test_4h_bins_start_at_18_22_02_06_10_14():
    b = minute_bars("2024-01-08 18:00", "2024-01-09 17:59")
    starts = [ts.strftime("%H:%M") for ts in resample(b, "4h").index]
    assert starts == ["18:00", "22:00", "02:00", "06:00", "10:00", "14:00"]


def test_daily_bar_runs_1800_to_1700():
    b = minute_bars("2024-01-08 18:00", "2024-01-09 16:59")
    d = resample(b, "1d")
    assert len(d) == 1
    assert d.index[0] == pd.Timestamp("2024-01-08 18:00", tz=NY)
    assert d.iloc[0].close_ts == pd.Timestamp("2024-01-09 16:59", tz=NY)


def test_weekly_bar_groups_sunday_evening_to_friday():
    b = pd.concat([minute_bars("2024-01-07 18:00", "2024-01-07 18:04"),     # Sunday open
                   minute_bars("2024-01-12 16:55", "2024-01-12 16:59"),     # Friday close
                   minute_bars("2024-01-14 18:00", "2024-01-14 18:04")])    # next week
    w = resample(b, "1w")
    assert len(w) == 2
    assert w.iloc[0].close_ts == pd.Timestamp("2024-01-12 16:59", tz=NY)


def test_bins_stay_on_wall_clock_across_dst():
    # US DST starts 2024-03-10 02:00 → 03:00. H1 bins on the Monday must start on the hour.
    b = minute_bars("2024-03-11 09:00", "2024-03-11 11:59")
    assert [ts.strftime("%H:%M") for ts in resample(b, "1h").index] == ["09:00", "10:00", "11:00"]


def test_1m_passthrough_and_bad_tf():
    b = minute_bars("2024-01-09 10:00", "2024-01-09 10:02")
    assert (resample(b, "1m").close_ts == b.index).all()
    with pytest.raises(ValueError):
        resample(b, "7m")
