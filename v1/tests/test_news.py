"""Economic calendar: building it from release (vintage) dates, and asking it about a day/time."""

from datetime import date

import pandas as pd
import pytest

from ict_engine.news import calendar as cal

NY = "America/New_York"


def ts(s):
    return pd.Timestamp(s, tz=NY)


# --- building -------------------------------------------------------------------------------

def test_ppi_february_seasonal_revision_is_dropped_keeping_the_release():
    ds = [date(2024, 1, 12), date(2024, 2, 14), date(2024, 2, 16), date(2024, 3, 14)]
    assert cal.clean_release("PPIFIS", ds) == [date(2024, 1, 12), date(2024, 2, 16), date(2024, 3, 14)]


def test_retail_sales_april_annual_revision_is_dropped():
    ds = [date(2024, 4, 15), date(2024, 4, 23), date(2024, 5, 15)]
    assert cal.clean_release("RSAFS", ds) == [date(2024, 4, 15), date(2024, 5, 15)]


def test_series_with_genuine_two_releases_a_month_keep_both():
    ds = [date(2022, 12, 1), date(2022, 12, 23)]               # PCE: Oct data delayed to Dec 1
    assert cal.clean_release("PCEPI", ds) == ds


def test_weekend_vintages_are_never_releases():
    assert cal.clean_release("PAYEMS", [date(2023, 1, 6), date(2023, 1, 7)]) == [date(2023, 1, 6)]


def test_fomc_meetings_parse_including_month_spanning_ones():
    html = ('<h4>2023 FOMC Meetings</h4>'
            '<div class="fomc-meeting__month col"><strong>Jan/Feb</strong></div>'
            '<div class="fomc-meeting__date col">31-1</div>'
            '<div class="fomc-meeting__month col"><strong>March</strong></div>'
            '<div class="fomc-meeting__date col">21-22*</div>'
            '<h4>2024 FOMC Meetings</h4>')
    assert cal.fomc_decision_days(html) == [date(2023, 2, 1), date(2023, 3, 22)]


def test_build_rows_have_ny_release_times():
    rows = cal.build_rows({"PAYEMS": [date(2023, 1, 6)], "JTSJOL": [date(2023, 1, 4)]}, [date(2023, 2, 1)])
    got = {(r["name"], r["ts"].strftime("%Y-%m-%d %H:%M"), r["impact"]) for _, r in rows.iterrows()}
    assert ("NFP", "2023-01-06 08:30", "high") in got
    assert ("JOLTS", "2023-01-04 10:00", "medium") in got
    assert ("FOMC statement", "2023-02-01 14:00", "high") in got
    assert ("FOMC press conference", "2023-02-01 14:30", "high") in got
    assert ("FOMC minutes", "2023-02-22 14:00", "medium") in got        # 3 weeks after the decision


# --- querying ---------------------------------------------------------------------------------

@pytest.fixture
def table():
    return cal.build_rows({"PAYEMS": [date(2024, 1, 5)], "CPIAUCNS": [date(2024, 1, 11)],
                           "ICSA": [date(2024, 1, 11)]}, [date(2024, 1, 31)])


def test_events_on_a_day(table):
    names = [e.name for e in cal.events_on(date(2024, 1, 11), table=table)]
    assert names == ["CPI", "Jobless claims"]
    assert [e.name for e in cal.events_on(date(2024, 1, 11), "high", table=table)] == ["CPI"]
    assert cal.events_on(date(2024, 1, 10), table=table) == []


def test_bucket_relative_to_the_nearest_high_impact_release(table):
    assert cal.news_bucket(ts("2024-01-05 08:10"), table=table) == "before release (≤30m)"
    assert cal.news_bucket(ts("2024-01-05 08:45"), table=table) == "after release (≤30m)"
    assert cal.news_bucket(ts("2024-01-05 10:30"), table=table) == "news day, away from release"
    assert cal.news_bucket(ts("2024-01-08 10:30"), table=table) == "no high-impact news"


def test_minutes_to_release_is_signed(table):
    ev, mins = cal.nearest(ts("2024-01-31 13:30"), table=table)
    assert ev.name == "FOMC statement" and mins == 30
    ev, mins = cal.nearest(ts("2024-01-31 15:00"), table=table)
    assert ev.name == "FOMC press conference" and mins == -30


def test_blackout_window(table):
    assert cal.in_blackout(ts("2024-01-11 08:20"), (30, 15), table=table)          # 10 min before CPI
    assert cal.in_blackout(ts("2024-01-11 08:40"), (30, 15), table=table)          # 10 min after
    assert not cal.in_blackout(ts("2024-01-11 09:00"), (30, 15), table=table)
    assert not cal.in_blackout(ts("2024-01-11 08:20"), None, table=table)


def test_checked_in_calendar_covers_the_backtest_period():
    t = cal.load()
    nfp = t[t.name == "NFP"]
    assert nfp.ts.min() <= ts("2021-10-08 08:30") and nfp.ts.max() >= ts("2024-06-07 08:30")
    assert ts("2023-03-10 08:30") in set(nfp.ts)                    # known: Feb 2023 NFP on Mar 10
    assert ts("2022-06-15 14:00") in set(t[t.name == "FOMC statement"].ts)
    per_year = nfp.groupby(nfp.ts.dt.year).size()
    assert (per_year.loc[2022:2023] == 12).all()


# --- gate (applied by the day runner to every model) ----------------------------------------

def test_gate_blackout_and_fomc_rules(table):
    g = cal.news_block
    assert g(ts("2024-01-11 08:20"), (30, 15), "trade", table=table) == "news blackout: CPI 08:30"
    assert g(ts("2024-01-11 09:30"), (30, 15), "trade", table=table) is None
    assert g(ts("2024-01-31 10:00"), None, "after_statement", table=table) == "FOMC day: wait for the 14:00 statement"
    assert g(ts("2024-01-31 14:45"), None, "after_statement", table=table) is None
    assert g(ts("2024-01-31 14:45"), None, "skip", table=table) == "FOMC day: no trades"
    assert g(ts("2024-01-30 10:00"), None, "skip", table=table) is None
    with pytest.raises(ValueError):
        g(ts("2024-01-30 10:00"), None, "sometimes", table=table)


def test_runner_blocks_a_setup_inside_the_blackout(monkeypatch):
    from dataclasses import replace
    from ict_engine.models import model_2022
    from ict_engine.sim import run
    from tests.test_run import fake, frame, patched, ROWS
    t = cal.build_rows({"PAYEMS": [date(2024, 1, 9)]}, [])          # pretend NFP 08:30 that day
    monkeypatch.setattr(cal, "load", lambda: t)
    setups = [fake("09:00", "ny_am_kz", 99, 98, 101)]
    patched(monkeypatch, setups)
    out = run.run_day(frame(ROWS), date(2024, 1, 9), "US100", replace(model_2022.Params(), news_blackout=(30, 45)))
    assert out[0].plan is None and out[0].result is None
    assert out[0].gates[-1].name == "news" and "NFP 08:30" in out[0].gates[-1].detail
    patched(monkeypatch, [fake("09:00", "ny_am_kz", 99, 98, 101)])
    out = run.run_day(frame(ROWS), date(2024, 1, 9), "US100", model_2022.Params())     # default: off
    assert out[0].result is not None
