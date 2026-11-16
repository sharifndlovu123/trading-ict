"""US market holidays and early closes (known years ahead: usable from the start of the day, no look-ahead).

On a cash-market holiday the index futures trade a shortened, thin session (the feed stops near 13:00 NY); the day
after, "previous day" levels come from that thin session. Trade reviews on 2026-11-16 found recipe trades on
Thanksgiving 2021 and Juneteenth 2026 whose exits were booked on the 18:00 reopen.

    session_note(day) → "holiday" | "early close" | "after holiday" | None

Rules (NYSE): New Year's Day, Martin Luther King Jr. Day, Presidents' Day, Good Friday, Memorial Day, Juneteenth
(from 2022), Independence Day, Labor Day, Thanksgiving, Christmas. A holiday on a Sunday is observed on Monday; on a
Saturday on the Friday before, except New Year's Day (no closure when it falls on a Saturday). Early closes (13:00):
the day after Thanksgiving, Christmas Eve and 3 July when they are weekdays next to the holiday. Plus the one-off
closures in ``SPECIAL``.
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

from dateutil.easter import easter

SPECIAL = {date(2025, 1, 9): "National Day of Mourning (President Carter)"}


def _nth(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _last(year: int, month: int, weekday: int) -> date:
    d = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _observed(d: date, saturday_to_friday: bool = True) -> date | None:
    if d.weekday() == 6:
        return d + timedelta(days=1)
    if d.weekday() == 5:
        return d - timedelta(days=1) if saturday_to_friday else None
    return d


@lru_cache(maxsize=None)
def holidays(year: int) -> dict[date, str]:
    out: dict[date, str] = {}

    def add(d: date | None, name: str):
        if d is not None:
            out[d] = name
    add(_observed(date(year, 1, 1), saturday_to_friday=False), "New Year's Day")
    add(_nth(year, 1, 0, 3), "Martin Luther King Jr. Day")
    add(_nth(year, 2, 0, 3), "Presidents' Day")
    add(easter(year) - timedelta(days=2), "Good Friday")
    add(_last(year, 5, 0), "Memorial Day")
    if year >= 2022:
        add(_observed(date(year, 6, 19)), "Juneteenth")
    add(_observed(date(year, 7, 4)), "Independence Day")
    add(_nth(year, 9, 0, 1), "Labor Day")
    add(_nth(year, 11, 3, 4), "Thanksgiving")
    add(_observed(date(year, 12, 25)), "Christmas")
    for d, name in SPECIAL.items():
        if d.year == year:
            out[d] = name
    return out


def holiday_name(day: date) -> str | None:
    return holidays(day.year).get(day)


def early_close(day: date) -> bool:
    if day.weekday() >= 5 or holiday_name(day):
        return False
    y = day.year
    if day == _nth(y, 11, 3, 4) + timedelta(days=1):                 # the Friday after Thanksgiving
        return True
    if day == date(y, 12, 24) and holiday_name(date(y, 12, 25)):     # Christmas Eve before a weekday Christmas
        return True
    return day == date(y, 7, 3) and holiday_name(date(y, 7, 4)) is not None


def session_note(day: date) -> str | None:
    """What kind of session ``day`` is, or None for a normal one."""
    if holiday_name(day):
        return "holiday"
    if early_close(day):
        return "early close"
    prev = day - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return "after holiday" if holiday_name(prev) else None
