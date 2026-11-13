from datetime import date

import pandas as pd
import pytest

from ict_engine.concepts.clock import active, midnight_open, tag, trading_day

NY = "America/New_York"


def ny(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz=NY)


@pytest.mark.parametrize("utc, expected_ny", [
    ("2023-11-20 13:33", "08:33"),   # winter, EST = UTC-5
    ("2023-07-10 12:33", "08:33"),   # summer, EDT = UTC-4
])
def test_dst_is_handled_by_timezone(utc, expected_ny):
    ts = pd.Timestamp(utc, tz="UTC").tz_convert(NY)
    assert ts.strftime("%H:%M") == expected_ny
    assert "ny_am_kz" in active(ts, "futures")


def test_futures_vs_fx_killzones():
    t = ny("2023-11-20 08:33")
    assert "ny_am_kz" in active(t, "futures") and "ny_kz" not in active(t, "futures")
    assert "ny_kz" in active(t, "fx") and "ny_am_kz" not in active(t, "fx")


def test_windows_are_half_open():
    assert "sb_am" in active(ny("2024-01-09 10:00"), "futures")
    assert "sb_am" not in active(ny("2024-01-09 11:00"), "futures")
    assert "ny_lunch" in active(ny("2024-01-09 12:00"), "futures")
    assert "ny_lunch" not in active(ny("2024-01-09 13:00"), "futures")


def test_ict_macro_trade_time():
    # 9 Jan 2024 ICT entry 11:04: inside the 10:50–11:10 macro, after the AM killzone/SB hour
    names = active(ny("2024-01-09 11:04"), "futures")
    assert "macro_1050" in names
    assert "ny_am_kz" not in names and "sb_am" not in names


def test_optional_late_silver_bullet():
    t = ny("2024-01-09 15:30")
    assert "sb_late" not in active(t, "futures")
    assert "sb_late" in active(t, "futures", include_optional=True)


def test_asia_wraps_midnight():
    assert "asia_kz" in active(ny("2024-01-08 23:59"), "fx")
    assert "asia_kz" not in active(ny("2024-01-09 00:00"), "fx")
    assert "asia_kz" in active(ny("2024-01-08 20:00"), "fx")


def test_trading_day_rolls_at_1800():
    assert trading_day(ny("2024-01-07 18:00")) == date(2024, 1, 8)   # Sunday evening → Monday
    assert trading_day(ny("2024-01-08 17:59")) == date(2024, 1, 8)
    idx = pd.DatetimeIndex([ny("2024-01-08 17:59"), ny("2024-01-08 18:00")])
    assert list(trading_day(idx)) == [date(2024, 1, 8), date(2024, 1, 9)]


def test_tag_matches_active():
    idx = pd.date_range("2024-01-09 00:00", "2024-01-09 23:59", freq="1min", tz=NY)
    tags = tag(idx, "futures")
    for ts in [idx[0], idx[150], idx[640], idx[664], idx[725], idx[900]]:
        on = {c for c in tags.columns if c != "trading_day" and tags.at[ts, c]}
        assert on == set(active(ts, "futures")), ts


def test_rejects_naive_or_utc_timestamps():
    with pytest.raises(ValueError):
        active(pd.Timestamp("2024-01-09 10:00"), "futures")
    with pytest.raises(ValueError):
        active(pd.Timestamp("2024-01-09 10:00", tz="UTC"), "futures")


def test_midnight_open():
    idx = pd.date_range("2024-01-08 23:58", periods=4, freq="1min", tz=NY)
    bars = pd.DataFrame({"open": [1, 2, 3, 4]}, index=idx)
    assert midnight_open(bars).to_dict() == {date(2024, 1, 9): 3}
