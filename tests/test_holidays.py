"""US market holidays (ict_engine.news.holidays) against known dates."""
from datetime import date

from ict_engine.news.holidays import early_close, holiday_name, session_note


def test_known_holidays():
    assert holiday_name(date(2021, 11, 25)) == "Thanksgiving"
    assert holiday_name(date(2026, 6, 19)) == "Juneteenth" and holiday_name(date(2020, 6, 19)) is None   # from 2022
    assert holiday_name(date(2026, 5, 25)) == "Memorial Day"
    assert holiday_name(date(2026, 4, 3)) == "Good Friday" and holiday_name(date(2020, 4, 10)) == "Good Friday"
    assert holiday_name(date(2021, 7, 5)) == "Independence Day"        # 4 July 2021 was a Sunday
    assert holiday_name(date(2020, 7, 3)) == "Independence Day"        # 4 July 2020 was a Saturday
    assert holiday_name(date(2021, 12, 31)) is None                    # New Year's Day 2022 on a Saturday: no closure
    assert holiday_name(date(2023, 1, 2)) == "New Year's Day"          # 1 Jan 2023 was a Sunday
    assert holiday_name(date(2025, 1, 9)) is not None                  # the one-off closure
    assert holiday_name(date(2024, 1, 15)) == "Martin Luther King Jr. Day" and holiday_name(date(2024, 2, 19)) == "Presidents' Day"
    assert holiday_name(date(2024, 9, 2)) == "Labor Day" and holiday_name(date(2024, 12, 25)) == "Christmas"
    assert holiday_name(date(2024, 10, 14)) is None                    # Columbus Day: markets open


def test_early_closes_and_the_day_after():
    assert early_close(date(2021, 11, 26)) and early_close(date(2024, 12, 24)) and early_close(date(2024, 7, 3))
    assert not early_close(date(2021, 11, 25)) and not early_close(date(2024, 12, 23))
    assert session_note(date(2021, 11, 25)) == "holiday" and session_note(date(2021, 11, 26)) == "early close"
    assert session_note(date(2026, 5, 26)) == "after holiday"          # the Tuesday after Memorial Day
    assert session_note(date(2026, 6, 22)) == "after holiday"          # the Monday after Juneteenth (a Friday)
    assert session_note(date(2026, 5, 27)) is None and session_note(date(2024, 3, 13)) is None


def test_calendar_covers_2020_and_the_added_events():
    """The news calendar extended on 2026-11-16: releases back to 2019-10, the 2019–2020 FOMC days (the cancelled
    March 2020 meeting and the unscheduled cuts are not scheduled news), the 10:00 releases and Jackson Hole."""
    import pandas as pd
    from ict_engine.news import calendar
    c = calendar.load()
    has = lambda name, ts: ((c.name == name) & (c.ts == pd.Timestamp(ts, tz="America/New_York"))).any()
    assert c.ts.min() < pd.Timestamp("2019-11-01", tz="America/New_York")
    assert has("NFP", "2020-03-06 08:30") and has("NFP", "2020-05-08 08:30") and not has("NFP", "2020-05-11 08:30")
    assert has("CPI", "2020-01-14 08:30") and has("PPI", "2020-02-19 08:30") and not has("PPI", "2020-02-14 08:30")
    assert has("FOMC statement", "2020-01-29 14:00") and has("FOMC statement", "2019-10-30 14:00")
    assert not c[(c.name == "FOMC statement") & (c.ts.dt.strftime("%Y-%m") == "2020-03")].shape[0]
    assert has("Jackson Hole (Fed chair)", "2024-08-23 10:00") and has("ISM manufacturing", "2024-07-01 10:00")
    assert has("ISM manufacturing", "2026-01-02 10:00")                       # 1 January is a holiday
    assert has("Consumer confidence", "2025-06-24 10:00")
    assert has("NFP", "2021-01-08 08:30") and has("CPI", "2026-11-10 08:30")   # the rows that were there are kept
    assert not c.duplicated(["ts", "name"]).any()
