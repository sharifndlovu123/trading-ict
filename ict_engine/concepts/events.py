"""Event detectors — pipeline stage 3. Concepts are detected, never scored.

Every event carries two times:
    origin_ts  the bar where the thing formed (pivot candle, FVG middle candle)
    ts         when it became KNOWN — the close of the bar that confirms it.
Later stages may only use an event once ``ts`` has passed (no look-ahead).

Definitions (framework.md §3–4, §9; engine defaults are params):
    swing high      high above the ``strength`` bars on each side (ICT 3-candle swing = 1)
    displacement    body ≥ k × mean body of the previous ``lookback`` bars and body/range ≥ ratio
    FVG (bull)      candle 3 low > candle 1 high; zone [c1.high, c3.low]; CE = midpoint
    volume imb.     bodies gap but wicks overlap; zone between the two bodies
    sweep           price trades through a liquidity level and closes back inside within
                    ``reclaim`` bars (a run if it doesn't)
    BOS / MSS       a close beyond the last confirmed swing; MSS when it flips the prior break direction
    gap lifecycle   touched → CE → filled; inverted (IFVG) on a BODY close beyond the far edge;
                    a VI is retired once bodies close through it
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Event:
    kind: str                 # swing_high, swing_low, displacement, fvg, ifvg, vi, sweep, run, bos, mss
    tf: str
    direction: str            # bull | bear
    ts: pd.Timestamp          # known from
    origin_ts: pd.Timestamp   # formed at
    top: float
    bottom: float
    meta: dict = field(default_factory=dict, compare=False, hash=False)

    @property
    def ce(self) -> float:
        return (self.top + self.bottom) / 2


def _arr(df: pd.DataFrame, col: str) -> np.ndarray:
    return df[col].to_numpy(dtype=float)


def _close_ts(df: pd.DataFrame) -> pd.Index:
    return df["close_ts"] if "close_ts" in df else df.index.to_series()


# --- swings -------------------------------------------------------------------

def swings(df: pd.DataFrame, tf: str, strength: int = 1) -> list[Event]:
    h, l, cts = _arr(df, "high"), _arr(df, "low"), _close_ts(df).to_numpy()
    out = []
    for i in range(strength, len(df) - strength):
        left_h, right_h = h[i - strength:i], h[i + 1:i + 1 + strength]
        if h[i] > left_h.max() and h[i] > right_h.max():
            out.append(Event("swing_high", tf, "bear", pd.Timestamp(cts[i + strength]), df.index[i], h[i], h[i]))
        left_l, right_l = l[i - strength:i], l[i + 1:i + 1 + strength]
        if l[i] < left_l.min() and l[i] < right_l.min():
            out.append(Event("swing_low", tf, "bull", pd.Timestamp(cts[i + strength]), df.index[i], l[i], l[i]))
    return out


# --- displacement ---------------------------------------------------------------

def displacement_mask(df: pd.DataFrame, k: float = 1.5, lookback: int = 20, min_body_ratio: float = 0.6) -> np.ndarray:
    o, c, h, l = (_arr(df, x) for x in ("open", "close", "high", "low"))
    body = np.abs(c - o)
    rng = np.maximum(h - l, 1e-12)
    avg = pd.Series(body).shift(1).rolling(lookback, min_periods=lookback).mean().to_numpy()
    return (body >= k * np.nan_to_num(avg, nan=np.inf)) & (body / rng >= min_body_ratio)


def displacements(df: pd.DataFrame, tf: str, **kw) -> list[Event]:
    m = displacement_mask(df, **kw)
    o, c, cts = _arr(df, "open"), _arr(df, "close"), _close_ts(df).to_numpy()
    return [Event("displacement", tf, "bull" if c[i] > o[i] else "bear", pd.Timestamp(cts[i]), df.index[i],
                  max(o[i], c[i]), min(o[i], c[i])) for i in np.flatnonzero(m)]


# --- fair value gaps and volume imbalances --------------------------------------

def fvgs(df: pd.DataFrame, tf: str, min_size: float = 0.0, **disp_kw) -> list[Event]:
    h, l, cts = _arr(df, "high"), _arr(df, "low"), _close_ts(df).to_numpy()
    disp = displacement_mask(df, **disp_kw)
    out = []
    for i in range(2, len(df)):
        if l[i] > h[i - 2] and l[i] - h[i - 2] > min_size:
            out.append(Event("fvg", tf, "bull", pd.Timestamp(cts[i]), df.index[i - 1], l[i], h[i - 2],
                             {"displacement": bool(disp[i - 1])}))
        if h[i] < l[i - 2] and l[i - 2] - h[i] > min_size:
            out.append(Event("fvg", tf, "bear", pd.Timestamp(cts[i]), df.index[i - 1], l[i - 2], h[i],
                             {"displacement": bool(disp[i - 1])}))
    return out


def volume_imbalances(df: pd.DataFrame, tf: str) -> list[Event]:
    o, c, h, l, cts = (*(_arr(df, x) for x in ("open", "close", "high", "low")), _close_ts(df).to_numpy())
    btop, bbot = np.maximum(o, c), np.minimum(o, c)
    out = []
    for i in range(1, len(df)):
        if bbot[i] > btop[i - 1] and l[i] <= h[i - 1]:
            out.append(Event("vi", tf, "bull", pd.Timestamp(cts[i]), df.index[i], bbot[i], btop[i - 1]))
        if btop[i] < bbot[i - 1] and h[i] >= l[i - 1]:
            out.append(Event("vi", tf, "bear", pd.Timestamp(cts[i]), df.index[i], bbot[i - 1], btop[i]))
    return out


@dataclass
class GapState:
    """What happened to a gap after it formed, scanned on 1m bars (framework.md §9)."""
    touched: pd.Timestamp | None = None        # first trade into the zone
    ce: pd.Timestamp | None = None             # price reached the CE
    body_beyond_ce: pd.Timestamp | None = None # a body closed past the CE (downgrade, §3)
    filled: pd.Timestamp | None = None         # traded through the far edge
    inverted: pd.Timestamp | None = None       # body closed beyond the far edge → IFVG
    retired: pd.Timestamp | None = None        # VI: bodies closed through it

    def valid_at(self, ts: pd.Timestamp) -> bool:
        end = self.retired or self.inverted
        return end is None or ts < end


def gap_lifecycle(gap: Event, bars_1m: pd.DataFrame, until: pd.Timestamp | None = None) -> GapState:
    after = bars_1m[bars_1m.index > gap.ts]
    if until is not None:
        after = after[after.index <= until]
    st = GapState()
    if after.empty:
        return st
    o, c, h, l = (_arr(after, x) for x in ("open", "close", "high", "low"))
    idx = after.index
    bull = gap.direction == "bull"
    near, far = (gap.top, gap.bottom) if bull else (gap.bottom, gap.top)   # price comes back to `near` first
    reach_near = l <= near if bull else h >= near
    reach_ce = l <= gap.ce if bull else h >= gap.ce
    reach_far = l <= far if bull else h >= far
    body_ce = c < gap.ce if bull else c > gap.ce
    body_far = c < far if bull else c > far
    first = lambda m: idx[np.argmax(m)] if m.any() else None
    st.touched, st.ce, st.filled = first(reach_near), first(reach_ce), first(reach_far)
    st.body_beyond_ce, st.inverted = first(body_ce), first(body_far)
    if gap.kind == "vi":
        st.retired, st.inverted = st.inverted, None
    return st


def inversions(gaps: Iterable[Event], bars_1m: pd.DataFrame, min_size: float = 0.0) -> list[Event]:
    """IFVGs: each FVG whose body-close inversion happened becomes a gap of the opposite polarity."""
    out = []
    for g in gaps:
        if g.kind != "fvg":
            continue
        st = gap_lifecycle(g, bars_1m)
        if st.inverted is not None and (g.top - g.bottom) > min_size:
            out.append(Event("ifvg", g.tf, "bear" if g.direction == "bull" else "bull", st.inverted,
                             g.origin_ts, g.top, g.bottom, {"from_fvg_ts": g.ts}))
    return out


# --- liquidity sweeps -----------------------------------------------------------

@dataclass(frozen=True)
class Level:
    name: str            # pdh, asia_low, swing_high@..., eqh ...
    price: float
    side: str            # high (buy-side liquidity above) | low (sell-side below)
    valid_from: pd.Timestamp


def swing_levels(swing_events: Iterable[Event]) -> list[Level]:
    """Confirmed swings become liquidity: buy-side above a swing high, sell-side below a swing low.
    A level exists only from the moment its swing is confirmed (``ts``)."""
    out = []
    for e in swing_events:
        if e.kind == "swing_high":
            out.append(Level(f"{e.tf}_swing_high@{e.origin_ts:%H:%M}", e.top, "high", e.ts))
        elif e.kind == "swing_low":
            out.append(Level(f"{e.tf}_swing_low@{e.origin_ts:%H:%M}", e.bottom, "low", e.ts))
    return out


def sweeps(bars: pd.DataFrame, levels: Iterable[Level], tf: str = "1m", reclaim: int = 3,
           until: pd.Timestamp | None = None) -> list[Event]:
    """First trade through each level → ``sweep`` (closed back inside within ``reclaim`` bars) or ``run``."""
    h, l, c = _arr(bars, "high"), _arr(bars, "low"), _arr(bars, "close")
    cts = _close_ts(bars).to_numpy()
    idx = bars.index
    out = []
    for lv in levels:
        start = idx.searchsorted(lv.valid_from, side="left")
        stop = len(bars) if until is None else idx.searchsorted(until, side="right")
        if start >= stop:
            continue
        through = (h[start:stop] > lv.price) if lv.side == "high" else (l[start:stop] < lv.price)
        if not through.any():
            continue
        i = start + int(np.argmax(through))
        window = c[i:min(i + reclaim, len(bars))]
        back = (window < lv.price) if lv.side == "high" else (window > lv.price)
        j = i + int(np.argmax(back)) if back.any() else None
        extreme = h[i:(j or i) + 1].max() if lv.side == "high" else l[i:(j or i) + 1].min()
        kind = "sweep" if j is not None else "run"
        # sweeping buy-side (a high) is a bearish signal; sweeping sell-side is bullish
        direction = ("bear" if lv.side == "high" else "bull") if kind == "sweep" else ("bull" if lv.side == "high" else "bear")
        known = pd.Timestamp(cts[j if j is not None else min(i + reclaim - 1, len(bars) - 1)])
        top, bottom = (extreme, lv.price) if lv.side == "high" else (lv.price, extreme)
        out.append(Event(kind, tf, direction, known, idx[i], top, bottom, {"level": lv.name, "level_price": lv.price}))
    return out


# --- market structure -------------------------------------------------------------

def structure(df: pd.DataFrame, tf: str, swing_events: list[Event] | None = None, strength: int = 1,
              **disp_kw) -> list[Event]:
    """BOS/MSS: a candle CLOSE beyond the most recent confirmed, unbroken swing."""
    sw = sorted(swing_events if swing_events is not None else swings(df, tf, strength), key=lambda e: e.ts)
    c, cts = _arr(df, "close"), _close_ts(df).to_numpy()
    disp = displacement_mask(df, **disp_kw)
    out, k = [], 0
    last_high = last_low = None
    trend = None
    for i in range(len(df)):
        now = pd.Timestamp(cts[i])
        while k < len(sw) and sw[k].ts < now:          # confirmed before this bar closed
            if sw[k].kind == "swing_high":
                last_high = sw[k]
            else:
                last_low = sw[k]
            k += 1
        if last_high is not None and c[i] > last_high.top and df.index[i] > last_high.origin_ts:
            kind = "mss" if trend == "bear" else "bos"
            out.append(Event(kind, tf, "bull", now, df.index[i], c[i], last_high.top,
                             {"broken_swing": last_high.origin_ts, "displacement": bool(disp[i])}))
            trend, last_high = "bull", None
        elif last_low is not None and c[i] < last_low.bottom and df.index[i] > last_low.origin_ts:
            kind = "mss" if trend == "bull" else "bos"
            out.append(Event(kind, tf, "bear", now, df.index[i], last_low.bottom, c[i],
                             {"broken_swing": last_low.origin_ts, "displacement": bool(disp[i])}))
            trend, last_low = "bear", None
    return out
