"""Sessions: which session a moment falls in, and whether an entry may be looked for then. The tool for concept 04;
the why is in lesson.md beside this file.

Every clock time in here is a definition he gave (19 Nov 2026), not a value from an example chart: "don't lock
training to specific times BUT, when it comes to sessions it's a must, because time is key for sessions and when to
trade." All times are New York time.

  * HIS_WINDOWS: "the times I've marked myself are the times I like, because of what I see on the chart."
  * KILL_ZONES, SESSIONS, ASIAN_RANGE: the reference definitions he gave beside his own (ICT's).
  * The rule: "never look for a trade outside of those times"; "your entries or trigger mode should only initiate
    within the kill zones / special times we mentioned"; "avoid trading New York PM session unless you're holding a
    trade or closing it off there"; the Asian session is never traded unless holding from late New York.

Mine, not his: joining the kill zones and his own windows into one answer (``stance``); taking the later of the two
ends he gave for London ("10:00 / 11:00"); taking the "commonly used" London kill zone and not the wider one from the
later lesson; saying nothing about which day of the week it is. This reads the clock only: no candles, no prices.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")


def _at(hour: int, minute: int = 0) -> int:
    return hour * 60 + minute


# minutes after midnight, New York; the end is not part of the window
HIS_WINDOWS = {"first": (_at(8, 20), _at(9)), "second": (_at(9, 20), _at(10)), "third": (_at(10, 20), _at(11))}
KILL_ZONES = {"london": (_at(2), _at(5)), "new york": (_at(7), _at(10))}
SESSIONS = {"asian": (_at(19), _at(5)), "london": (_at(2), _at(11)), "new york morning": (_at(8, 30), _at(11)),
            "new york pm": (_at(13), _at(16))}
ASIAN_RANGE = (_at(20), _at(0))
PM_SWEET_SPOT = (_at(14), _at(16))


def _inside(minute: int, span: tuple[int, int]) -> bool:
    start, end = span
    return start <= minute < end if start < end else minute >= start or minute < end     # a span may run past midnight


def new_york_clock(utc_seconds: float) -> int:
    """Minutes after midnight on the New York clock for a moment given in UTC seconds (summer and winter time)."""
    t = datetime.fromtimestamp(utc_seconds, timezone.utc).astimezone(NEW_YORK)
    return t.hour * 60 + t.minute


def sessions(minute: int) -> list[str]:
    """Every session the minute falls in (they overlap: the end of the Asian hours is the start of London)."""
    return [name for name, span in SESSIONS.items() if _inside(minute, span)]


def kill_zone(minute: int) -> str | None:
    return next((name for name, span in KILL_ZONES.items() if _inside(minute, span)), None)


def his_window(minute: int) -> str | None:
    """Which of his own New York morning windows the minute is in, if any."""
    return next((name for name, span in HIS_WINDOWS.items() if _inside(minute, span)), None)


def stance(minute: int) -> str:
    """What may be done at this minute:

    * ``"entry"``: inside a kill zone or one of his windows, so an entry may be looked for;
    * ``"manage"``: the New York PM session or the Asian hours, where only a trade already open is held or closed;
    * ``"read"``: anything else: read the chart top to bottom, look for no trade.
    """
    if kill_zone(minute) or his_window(minute):
        return "entry"
    if _inside(minute, SESSIONS["new york pm"]) or _inside(minute, SESSIONS["asian"]):
        return "manage"
    return "read"


def pm_sweet_spot(minute: int) -> bool:
    """ "The sweet spot for the NY PM session is 2 p.m. to 4 p.m." (for managing or closing, not for a new trade)."""
    return _inside(minute, PM_SWEET_SPOT)
