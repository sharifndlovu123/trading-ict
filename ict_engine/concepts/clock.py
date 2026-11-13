"""The clock — pipeline stage 2. Time is checked before any price pattern.

All windows are New York local time; bars must already be NY-indexed
(``ict_engine.data.dukascopy.load`` does this), so DST is handled by the
timezone, not by shifting window hours.

Windows are half-open: start ≤ t < end. A window whose end is before its start
wraps past midnight (Asia 20:00–00:00).

Sources: framework.md §6/§10, models.md (Silver Bullet), patterns.md (macros),
references/personal/ictindex-rulings.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable, Literal

import pandas as pd

Kind = Literal["killzone", "silver_bullet", "macro", "no_trade", "range", "sweet_spot"]
ClockSet = Literal["futures", "fx"]


@dataclass(frozen=True)
class Window:
    name: str
    kind: Kind
    start: time
    end: time
    clocks: frozenset[str] = frozenset({"futures", "fx"})
    optional: bool = False       # off by default; turned on as a tested variant
    source: str = ""

    @property
    def _bounds(self) -> tuple[int, int]:
        return self.start.hour * 60 + self.start.minute, self.end.hour * 60 + self.end.minute

    def contains(self, t: time) -> bool:
        m = t.hour * 60 + t.minute
        lo, hi = self._bounds
        return lo <= m < hi if lo < hi else (m >= lo or m < hi)


def _t(s: str) -> time:
    return datetime.strptime(s, "%H:%M").time()


def _w(name, kind, start, end, clocks=("futures", "fx"), optional=False, source=""):
    return Window(name, kind, _t(start), _t(end), frozenset(clocks), optional, source)


WINDOWS: tuple[Window, ...] = (
    # killzones — index futures (2022 slide; AM end 11:00 per ictindex ruling)
    _w("london_kz", "killzone", "02:00", "05:00", ("futures", "fx"), source="2022 slide / ICT Bible p.9"),
    _w("ny_am_kz", "killzone", "08:30", "11:00", ("futures",), source="2022 slide; ruling #4"),
    _w("ny_pm_kz", "killzone", "13:30", "16:00", ("futures",), source="2022 slide / ICT Bible p.9"),
    _w("ny_premarket", "killzone", "07:00", "09:30", ("futures",),
       source="ICT 2023 MMxM (2022 model 7–9 'NY Open Kill Zone'); Oct 28 2024; Jan 2026 — see ictindex-rulings"),
    # killzones — FX, dollar index, metals (ICT Bible p.9)
    _w("asia_kz", "killzone", "20:00", "00:00", ("fx",), source="ICT Bible p.9"),
    _w("ny_kz", "killzone", "07:00", "10:00", ("fx",), source="ICT Bible p.9; ruling #4"),
    _w("london_close_kz", "killzone", "10:00", "12:00", ("fx",), source="ICT Bible p.9"),
    _w("london_sweet_spot", "sweet_spot", "02:00", "04:00", source="Twitter Spaces"),
    # Silver Bullet (ruling #2): one-hour windows; 15–16 is an optional fourth
    _w("sb_london", "silver_bullet", "03:00", "04:00", source="SB lecture 14 May 2023"),
    _w("sb_am", "silver_bullet", "10:00", "11:00", source="SB lecture 14 May 2023"),
    _w("sb_pm", "silver_bullet", "14:00", "15:00", source="SB lecture 14 May 2023"),
    _w("sb_late", "silver_bullet", "15:00", "16:00", optional=True, source="ICT May–Sep 2023; ruling #2"),
    # algorithmic macros (patterns.md); others still to research
    _w("macro_0950", "macro", "09:50", "10:10", source="ICT Mentorship 2023 macros"),
    _w("macro_1050", "macro", "10:50", "11:10", source="ICT Mentorship 2023 macros"),
    # no new trades
    _w("ny_lunch", "no_trade", "12:00", "13:00", source="2022 Mentorship"),
    # ranges used as reference levels, not trade windows
    _w("asia_range", "range", "20:00", "00:00", source="ICT Bible"),
    _w("cbdr", "range", "14:00", "20:00", ("fx",), source="Core Content M08; ruling #3"),
)


def windows_for(clock: ClockSet, *, include_optional: bool = False,
                windows: Iterable[Window] = WINDOWS) -> list[Window]:
    return [w for w in windows if clock in w.clocks and (include_optional or not w.optional)]


def active(ts: datetime, clock: ClockSet, *, include_optional: bool = False) -> list[str]:
    """Names of windows open at ``ts`` (a NY-local, tz-aware timestamp)."""
    _require_ny(ts)
    t = ts.time()
    return [w.name for w in windows_for(clock, include_optional=include_optional) if w.contains(t)]


def tag(index: pd.DatetimeIndex, clock: ClockSet, *, include_optional: bool = False) -> pd.DataFrame:
    """Boolean column per window for every bar (vectorised)."""
    _require_ny(index)
    m = index.hour * 60 + index.minute
    cols = {}
    for w in windows_for(clock, include_optional=include_optional):
        lo, hi = w._bounds
        cols[w.name] = (m >= lo) & (m < hi) if lo < hi else (m >= lo) | (m < hi)
    out = pd.DataFrame(cols, index=index)
    out["trading_day"] = trading_day(index)
    return out


# --- calendar helpers ---------------------------------------------------------

DAY_ROLL = time(18, 0)   # futures/FX trading day starts 18:00 NY the evening before


def trading_day(ts):
    """Trading day a bar belongs to: bars from 18:00 count toward the next date.

    Accepts a single timestamp or a DatetimeIndex (NY-local).
    """
    _require_ny(ts)
    if isinstance(ts, pd.DatetimeIndex):
        shifted = ts + pd.to_timedelta((ts.hour >= DAY_ROLL.hour).astype(int), unit="D")
        return pd.Index(shifted.date, name="trading_day")
    d = ts.date()
    return d + timedelta(days=1) if ts.time() >= DAY_ROLL else d


def midnight_open(bars: pd.DataFrame) -> pd.Series:
    """00:00 NY open per calendar date — the only true open used as a price level (§5)."""
    _require_ny(bars.index)
    at_midnight = bars[(bars.index.hour == 0) & (bars.index.minute == 0)]["open"]
    return pd.Series(at_midnight.values, index=at_midnight.index.date, name="midnight_open")


def _require_ny(x) -> None:
    tz = getattr(x, "tz", None) or getattr(x, "tzinfo", None)
    if tz is None or "New_York" not in str(tz):
        raise ValueError("timestamps must be tz-aware America/New_York (convert first)")
