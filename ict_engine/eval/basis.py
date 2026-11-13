"""Estimate the price offset (basis) between our feed and a reference chart.

ICT traded futures; v1 data is Dukascopy CFD/spot. Futures sit above spot by a
carry that shrinks toward expiry and jumps at the roll (NQ: ~-58 pts on
2023-11-20, ~-8 on 12-07, ~-139 on 2024-01-09 after rolling to H24) — often many
times the trade's risk. So entries can only be compared after removing it.

The offset must NOT be measured at the entry itself (that would make every
entry match by construction). Instead each reference case lists **anchors**:
named levels drawn on ICT's chart (a swing at a time, Asia high, PDH). The same
level is measured on our bars and the median difference is the offset.

Anchor specs:
    high@HH:MM / low@HH:MM   swing extreme within ±3 min of that time, same day
    asia_high / asia_low     20:00–00:00 the evening before
    pdh / pdl                previous trading day (18:00 → 17:00)
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import pandas as pd

NY = "America/New_York"
_AT = re.compile(r"^(high|low)@(\d{2}):(\d{2})$")
SWING_SLACK = pd.Timedelta(minutes=3)


@dataclass(frozen=True)
class Anchor:
    spec: str
    price: float      # level on the reference (futures) chart


@dataclass
class Offset:
    value: float | None          # our price - reference price
    residuals: list[float]       # per-anchor (ours - ref) - value; spread = reliability
    n: int

    @property
    def spread(self) -> float:
        return max(abs(r) for r in self.residuals) if self.residuals else float("nan")


def _ts(d: date, t: time) -> pd.Timestamp:
    return pd.Timestamp(datetime.combine(d, t), tz=NY)


def level(bars: pd.DataFrame, day: date, spec: str) -> float | None:
    """Measure an anchor level on NY-indexed bars for trading day ``day``."""
    m = _AT.match(spec)
    if m:
        side, hh, mm = m.group(1), int(m.group(2)), int(m.group(3))
        at = _ts(day, time(hh, mm))
        w = bars[(bars.index >= at - SWING_SLACK) & (bars.index <= at + SWING_SLACK)]
        if w.empty:
            return None
        return float(w["high"].max() if side == "high" else w["low"].min())

    if spec in ("asia_high", "asia_low"):
        prev = day - timedelta(days=1)
        w = bars[(bars.index >= _ts(prev, time(20))) & (bars.index < _ts(day, time(0)))]
    elif spec in ("pdh", "pdl"):
        # previous trading day: walk back to a day that has bars
        for back in range(1, 5):
            p = day - timedelta(days=back)
            w = bars[(bars.index >= _ts(p - timedelta(days=1), time(18))) & (bars.index < _ts(p, time(17)))]
            if len(w) > 60:
                break
    else:
        raise ValueError(f"unknown anchor spec {spec!r}")
    if w.empty:
        return None
    return float(w["high"].max() if spec.endswith("high") or spec == "pdh" else w["low"].min())


def estimate_offset(bars: pd.DataFrame, day: date, anchors: list[Anchor]) -> Offset:
    diffs = []
    for a in anchors:
        ours = level(bars, day, a.spec)
        if ours is not None:
            diffs.append(ours - a.price)
    if not diffs:
        return Offset(None, [], 0)
    value = statistics.median(diffs)
    return Offset(value, [d - value for d in diffs], len(diffs))
