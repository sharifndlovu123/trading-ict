"""Sessions: his times as he gave them on 19 Nov 2026. These test the clock only, so there are no candles, prices or
timeframes in here; what must hold instead is every edge of every window, and the New York clock in summer and winter."""
from datetime import datetime, timezone

import pytest

from sessions import ASIAN_RANGE, his_window, kill_zone, new_york_clock, pm_sweet_spot, sessions, stance


def at(hour, minute=0):
    return hour * 60 + minute


@pytest.mark.parametrize("when, name", [(at(8, 20), "first"), (at(8, 59), "first"), (at(9, 20), "second"), (at(9, 59), "second"),
                                        (at(10, 20), "third"), (at(10, 59), "third")])
def test_his_own_windows_start_and_end_where_he_put_them(when, name):
    assert his_window(when) == name and stance(when) == "entry"


@pytest.mark.parametrize("when", [at(8, 19), at(9, 0), at(9, 19), at(10, 0), at(10, 19), at(11, 0)])
def test_the_minutes_between_his_windows_are_not_inside_one(when):
    assert his_window(when) is None


@pytest.mark.parametrize("when, zone", [(at(2), "london"), (at(4, 59), "london"), (at(7), "new york"), (at(9, 59), "new york")])
def test_an_entry_may_be_looked_for_inside_a_kill_zone(when, zone):
    assert kill_zone(when) == zone and stance(when) == "entry"


@pytest.mark.parametrize("when", [at(1, 59), at(5), at(6, 59), at(10), at(10, 19)])
def test_just_outside_a_kill_zone_and_his_windows_no_entry_is_looked_for(when):
    """ "Never look for a trade outside of those times." """
    assert kill_zone(when) is None and stance(when) != "entry"


@pytest.mark.parametrize("when", [at(13), at(14, 30), at(15, 59)])
def test_the_new_york_pm_session_is_for_holding_or_closing_only(when):
    """ "Avoid trading New York PM session unless you're holding a trade or closing it off there." """
    assert "new york pm" in sessions(when) and stance(when) == "manage"


def test_the_pm_sweet_spot_is_the_last_two_hours_of_the_pm_session():
    assert [pm_sweet_spot(m) for m in (at(13, 59), at(14), at(15, 59), at(16))] == [False, True, True, False]


@pytest.mark.parametrize("when", [at(19), at(23, 30), at(0, 30), at(1, 59)])
def test_the_asian_hours_are_never_for_a_new_trade(when):
    assert "asian" in sessions(when) and stance(when) == "manage"


def test_where_the_asian_hours_and_london_overlap_london_decides():
    """The Asian session runs to 5 a.m. and London's kill zone starts at 2: an entry may be looked for there."""
    assert set(sessions(at(3))) == {"asian", "london"} and stance(at(3)) == "entry"


@pytest.mark.parametrize("when", [at(5, 30), at(11, 30), at(12, 59), at(16), at(18, 59)])
def test_outside_every_window_the_chart_is_read_and_no_trade_is_looked_for(when):
    assert stance(when) == "read"


def test_the_asian_range_runs_up_to_midnight():
    assert ASIAN_RANGE == (at(20), 0)


def test_the_new_york_clock_is_right_in_summer_and_in_winter():
    """The same New York time is a different UTC time on each side of the clock change."""
    summer = datetime(2001, 7, 2, 13, 30, tzinfo=timezone.utc).timestamp()      # New York is four hours behind
    winter = datetime(2001, 1, 2, 14, 30, tzinfo=timezone.utc).timestamp()      # New York is five hours behind
    assert new_york_clock(summer) == at(9, 30) == new_york_clock(winter)
    assert stance(new_york_clock(summer)) == stance(new_york_clock(winter)) == "entry"
