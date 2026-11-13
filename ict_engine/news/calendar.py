"""US economic calendar — when the high-impact releases hit (NFP, CPI, FOMC, ...).

The schedule is published weeks ahead, so gates may use it from the start of the day (no
look-ahead). The released *numbers* (actual vs forecast) are only known at the release time
and are not stored here.

Data: ``us_calendar.csv`` (checked in, NY local times), built from official sources:
    releases  ALFRED vintage dates (alfred.stlouisfed.org/series?seid=<SERIES>, the
              "revision dates" list): every date a series was revised. That is the
              release date, apart from the seasonal/annual revisions removed in
              ``clean_release``. FRED/BLS block scripted clients, so the lists were
              saved from a browser into ``<dir>/<SERIES>.txt``, one ISO date per line.
    FOMC      federalreserve.gov/monetarypolicy/fomccalendars.htm. The statement is at
              14:00 on the meeting's last day, the press conference at 14:30, and the
              minutes at 14:00 three weeks later.

    uv run python -m ict_engine.news.calendar build <vintage_dir> <fomccalendars.html>
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path

import pandas as pd

NY = "America/New_York"
CSV = Path(__file__).with_name("us_calendar.csv")

# ALFRED series → (event name, NY release time, impact)
RELEASES: dict[str, tuple[str, time, str]] = {
    "PAYEMS": ("NFP", time(8, 30), "high"),                 # Employment Situation (BLS)
    "CPIAUCNS": ("CPI", time(8, 30), "high"),               # not seasonally adjusted: no Feb revision vintages
    "PPIFIS": ("PPI", time(8, 30), "high"),
    "RSAFS": ("Retail sales", time(8, 30), "high"),
    "GDP": ("GDP", time(8, 30), "high"),                    # advance / second / third estimates
    "PCEPI": ("PCE", time(8, 30), "high"),                  # Personal Income & Outlays (BEA)
    "ICSA": ("Jobless claims", time(8, 30), "medium"),      # weekly
    "JTSJOL": ("JOLTS", time(10, 0), "medium"),
}
# Revision-only vintages: (series, month) with two dates → keep the release ("first"/"last").
REVISIONS = {("PPIFIS", 2): "last",       # seasonal factors revised a few days before the Jan PPI
             ("RSAFS", 4): "first"}       # annual retail trade revision ~a week after the March data
FOMC_STATEMENT, FOMC_PRESSER, FOMC_MINUTES = time(14, 0), time(14, 30), time(14, 0)


@dataclass(frozen=True)
class NewsEvent:
    ts: pd.Timestamp
    name: str
    impact: str          # high | medium


# --- building --------------------------------------------------------------------------------

def clean_release(series: str, dates: list[date]) -> list[date]:
    """Release dates from a series' vintage dates: weekdays only, revision-only vintages removed."""
    ds = sorted(d for d in set(dates) if d.weekday() < 5)
    out = []
    for d in ds:
        rule = REVISIONS.get((series, d.month))
        same = [x for x in ds if (x.year, x.month) == (d.year, d.month)]
        if rule and len(same) > 1 and d != (same[0] if rule == "first" else same[-1]):
            continue
        out.append(d)
    return out


_MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug",
                                        "sep", "oct", "nov", "dec"), start=1)}


def fomc_decision_days(html: str) -> list[date]:
    """Last day of every scheduled FOMC meeting on the Fed's calendar page."""
    heads = [(m.start(), int(m.group(1))) for m in re.finditer(r"(\d{4}) FOMC Meetings", html)]
    out = []
    for k, (pos, year) in enumerate(heads):
        block = html[pos:heads[k + 1][0] if k + 1 < len(heads) else len(html)]
        for month, days in re.findall(r'fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>.*?'
                                      r'fomc-meeting__date[^>]*>([^<]+)<', block, re.S):
            nums = [int(n) for n in re.findall(r"\d+", days)]
            if not nums:
                continue
            months = [_MONTHS[m.strip()[:3].lower()] for m in month.split("/")]
            out.append(date(year, months[-1], nums[-1]))
    return sorted(out)


def _ts(d: date, t: time) -> pd.Timestamp:
    return pd.Timestamp(datetime.combine(d, t), tz=NY)


def build_rows(series_dates: dict[str, list[date]], fomc_days: list[date]) -> pd.DataFrame:
    rows = []
    for series, ds in series_dates.items():
        name, t, impact = RELEASES[series]
        rows += [{"ts": _ts(d, t), "name": name, "impact": impact, "source": f"ALFRED {series}"}
                 for d in clean_release(series, ds)]
    for d in fomc_days:
        rows += [{"ts": _ts(d, FOMC_STATEMENT), "name": "FOMC statement", "impact": "high", "source": "federalreserve.gov"},
                 {"ts": _ts(d, FOMC_PRESSER), "name": "FOMC press conference", "impact": "high", "source": "federalreserve.gov"},
                 {"ts": _ts(d + timedelta(days=21), FOMC_MINUTES), "name": "FOMC minutes", "impact": "medium",
                  "source": "federalreserve.gov (+3 weeks)"}]
    return _sorted(pd.DataFrame(rows, columns=["ts", "name", "impact", "source"]))


def _sorted(df: pd.DataFrame) -> pd.DataFrame:
    return (df.assign(_k=(df.impact != "high")).sort_values(["ts", "_k", "name"])
              .drop(columns="_k").reset_index(drop=True))


# --- querying --------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df["ts"] = pd.to_datetime(df.ts, utc=True).dt.tz_convert(NY)
    return _sorted(df)


def _table(table):
    return load() if table is None else table


def events_on(day: date, impact: str | None = None, table: pd.DataFrame | None = None) -> list[NewsEvent]:
    t = _table(table)
    t = t[t.ts.dt.date == day]
    if impact:
        t = t[t.impact == impact]
    return [NewsEvent(r.ts, r.name, r.impact) for r in t.itertuples()]


def nearest(ts: pd.Timestamp, impact: str = "high", table=None) -> tuple[NewsEvent | None, float | None]:
    """Same-day release nearest to ``ts`` and the signed minutes to it (+ = still ahead)."""
    evs = events_on(ts.date(), impact, table)
    if not evs:
        return None, None
    e = min(evs, key=lambda e: abs(e.ts - ts))
    return e, (e.ts - ts).total_seconds() / 60


def news_bucket(ts: pd.Timestamp, near_min: float = 30, table=None) -> str:
    e, mins = nearest(ts, "high", table)
    if e is None:
        return "no high-impact news"
    if 0 <= mins <= near_min:
        return f"before release (≤{near_min:g}m)"
    if -near_min <= mins < 0:
        return f"after release (≤{near_min:g}m)"
    return "news day, away from release"


def in_blackout(ts: pd.Timestamp, window: tuple[float, float] | None, impact: str = "high", table=None) -> bool:
    """``window`` = (minutes before, minutes after) a release in which no new trade is opened."""
    if not window:
        return False
    before, after = window
    return any(-after <= (e.ts - ts).total_seconds() / 60 <= before for e in events_on(ts.date(), impact, table))


FOMC_DAY_RULES = ("trade", "after_statement", "skip")


def news_block(ts: pd.Timestamp, blackout: tuple[float, float] | None, fomc_day: str = "trade",
               table=None) -> str | None:
    """Why a new trade may not open at ``ts`` because of scheduled news, or None. Uses only the
    published schedule, so it is known before the session (no look-ahead)."""
    if fomc_day not in FOMC_DAY_RULES:
        raise ValueError(f"fomc_day must be one of {FOMC_DAY_RULES}, not {fomc_day!r}")
    if blackout:
        before, after = blackout
        for e in events_on(ts.date(), "high", table):
            if -after <= (e.ts - ts).total_seconds() / 60 <= before:
                return f"news blackout: {e.name} {e.ts:%H:%M}"
    if fomc_day != "trade":
        st = [e for e in events_on(ts.date(), "high", table) if e.name == "FOMC statement"]
        if st and fomc_day == "skip":
            return "FOMC day: no trades"
        if st and ts < st[0].ts:
            return f"FOMC day: wait for the {st[0].ts:%H:%M} statement"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.news.calendar")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("vintage_dir", type=Path)
    b.add_argument("fomc_html", type=Path)
    b.add_argument("--start", type=date.fromisoformat, default=date(2021, 1, 1))
    a = ap.parse_args(argv)
    series = {s: [date.fromisoformat(x.strip()) for x in (a.vintage_dir / f"{s}.txt").read_text().split()
                  if x.strip() and date.fromisoformat(x.strip()) >= a.start]
              for s in RELEASES}
    fomc = [d for d in fomc_decision_days(a.fomc_html.read_text()) if d >= a.start]
    df = build_rows(series, fomc)
    df.assign(ts=df.ts.map(lambda t: t.isoformat())).to_csv(CSV, index=False)
    print(f"{CSV}: {len(df)} events {df.ts.min():%Y-%m-%d} → {df.ts.max():%Y-%m-%d}")
    print(df.groupby("name").size().to_string())


if __name__ == "__main__":
    main()
