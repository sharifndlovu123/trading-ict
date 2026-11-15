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
                    a VI is retired once bodies close through it; a block (OB / breaker / mitigation)
                    is retired on a BODY close beyond its 50%
    order block     last down-close candle(s) before a close above their high (bull; Bible p.16)
    breaker / MB    swing low → high → lower low (breaker) / higher low (MB) → close above the high;
                    block = last up-close candle(s) in that high (bull; Bible pp.19-26)
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
    elif gap.kind in BLOCK_KINDS:          # OB / breaker / mitigation: a body close beyond the 50% ends it
        st.retired, st.inverted = st.body_beyond_ce, None
    return st


def inversions(gaps: Iterable[Event], bars_1m: pd.DataFrame, min_size: float = 0.0,
               tf_bars: dict[str, pd.DataFrame] | None = None) -> list[Event]:
    """IFVGs: each FVG whose body-close inversion happened becomes a gap of the opposite polarity.

    By default the inversion is the first **1m** body close beyond the far edge. With ``tf_bars`` ({tf: bars of
    that timeframe, with ``close_ts``}), a FVG of a listed timeframe inverts only on a close of **its own
    timeframe** beyond the far edge (a daily FVG fails on a daily close; Sharif 2026-11-14, ICT rulings §10), and
    the IFVG becomes known at that candle's ``close_ts`` (no look-ahead)."""
    out = []
    for g in gaps:
        if g.kind != "fvg" or (g.top - g.bottom) <= min_size:
            continue
        if tf_bars is not None and g.tf in tf_bars:
            when = _tf_close_beyond(g, tf_bars[g.tf])
        else:
            when = gap_lifecycle(g, bars_1m).inverted
        if when is not None:
            out.append(Event("ifvg", g.tf, "bear" if g.direction == "bull" else "bull", when,
                             g.origin_ts, g.top, g.bottom, {"from_fvg_ts": g.ts}))
    return out


def _tf_close_beyond(g: Event, bars: pd.DataFrame) -> pd.Timestamp | None:
    """close_ts of the first bar after the gap formed whose close is beyond the gap's far edge."""
    cts = _close_ts(bars)
    after = bars[cts > g.ts]
    if after.empty:
        return None
    c = _arr(after, "close")
    hit = c < g.bottom if g.direction == "bull" else c > g.top
    return pd.Timestamp(_close_ts(after).to_numpy()[np.argmax(hit)]) if hit.any() else None


# --- order blocks, breakers, mitigation blocks (ICT Bible pp.16-26) ---------------
# All three are "blocks": a zone [low, high] of one or more same-colour candles. A block stops counting once a
# candle BODY closes beyond its 50% (OB mean threshold, Bible p.17; breaker 50%, framework.md §9).

BLOCK_KINDS = ("ob", "breaker", "mitigation")


def order_blocks(df: pd.DataFrame, tf: str, max_wait: int = 5, confirm: str = "extreme", single: bool = False) -> list[Event]:
    """Bullish OB: the last down-close candle(s) before a candle CLOSES above their high (the close that
    validates it, Bible p.16 step 3, is ``ts``). Bearish is the mirror (last up-close candles, close below
    their low). ``confirm="open"`` validates earlier, on a close through the block's opening price (Sharif,
    2026-11-14: the sell candle "closing the green candle"). ``max_wait``: the validating close must come
    within this many bars of the block. ``meta['fvg']``: a FVG formed in the move away by the validating bar
    (a higher-quality OB, p.17 step 4). ``meta['body']`` = (body top, body bottom) for quadrant levels.
    ``single=True``: the block is only the LAST opposite-close candle of the run (Sharif 2026-11-16: September alone,
    not August + September). Whether it is a real OB (a transitional event, the place) is ``ob_context``'s job."""
    if confirm not in ("extreme", "open"):
        raise ValueError(f"confirm must be 'extreme' or 'open', got {confirm!r}")
    o, h, l, c, cts = (*(_arr(df, x) for x in ("open", "high", "low", "close")), _close_ts(df).to_numpy())
    out = []
    for bull in (True, False):
        run = None                                   # (first, last) index of the current same-colour run
        for i in range(len(df)):
            against = c[i] < o[i] if bull else c[i] > o[i]
            if against:
                run = (run[0], i) if run is not None and run[1] == i - 1 else (i, i)
                continue
            if run is None:
                continue
            a, b = run
            if single:
                a = b
            if i - b > max_wait:
                run = None
                continue
            hi, lo = h[a:b + 1].max(), l[a:b + 1].min()
            lvl = (o[a:b + 1].max() if bull else o[a:b + 1].min()) if confirm == "open" else (hi if bull else lo)
            if (bull and c[i] > lvl) or (not bull and c[i] < lvl):
                fvg = any((l[j] > h[j - 2]) if bull else (h[j] < l[j - 2]) for j in range(b + 2, i + 1))
                out.append(Event("ob", tf, "bull" if bull else "bear", pd.Timestamp(cts[i]), df.index[a],
                                 float(hi), float(lo), {"fvg": fvg, "candles": b - a + 1,
                                 "body": (float(max(o[a:b + 1].max(), c[a:b + 1].max())),
                                          float(min(o[a:b + 1].min(), c[a:b + 1].min())))}))
                run = None
    return sorted(out, key=lambda e: e.ts)


def quadrants(top: float, bottom: float) -> dict[str, float]:
    """0/25/50/75/100 % levels of a zone, measured from ``bottom``; 50 % is the mean threshold."""
    return {f"{q}%": bottom + (top - bottom) * q / 100 for q in (0, 25, 50, 75, 100)}


def _colour_run(o: np.ndarray, c: np.ndarray, at: int, up: bool, lo: int) -> tuple[int, int] | None:
    """The last run of up-close (``up``) or down-close candles ending at or before ``at`` (not before ``lo``)."""
    j = at
    while j >= lo and not ((c[j] > o[j]) if up else (c[j] < o[j])):
        j -= 1
    if j < lo:
        return None
    k = j
    while k - 1 >= lo and ((c[k - 1] > o[k - 1]) if up else (c[k - 1] < o[k - 1])):
        k -= 1
    return k, j


def breaker_blocks(df: pd.DataFrame, tf: str, strength: int = 1, swing_events: list[Event] | None = None) -> list[Event]:
    """Breakers and mitigation blocks (Bible pp.19-26). Bullish (bearish is the mirror):
        swing low L1 → swing high H → swing low L2 → a candle CLOSES above H.
        L2 < L1 (sell stops taken) → ``breaker``; L2 > L1 (a higher low, no sweep) → ``mitigation``.
        The block = the last up-close candle(s) in the swing high H; known at the closing break (and not before
        L2 is confirmed). Only consecutive swings in strict low/high/low order count (no merging, no look-ahead)."""
    sw = sorted(swing_events if swing_events is not None else swings(df, tf, strength), key=lambda e: e.origin_ts)
    o, h, l, c, cts = (*(_arr(df, x) for x in ("open", "high", "low", "close")), _close_ts(df).to_numpy())
    pos = {t: i for i, t in enumerate(df.index)}
    out = []
    for s1, s2, s3 in zip(sw, sw[1:], sw[2:]):
        if [s.kind for s in (s1, s2, s3)] == ["swing_low", "swing_high", "swing_low"]:
            bull, mid, level = True, s2, s2.top
            kind = "breaker" if s3.bottom < s1.bottom else "mitigation" if s3.bottom > s1.bottom else None
        elif [s.kind for s in (s1, s2, s3)] == ["swing_high", "swing_low", "swing_high"]:
            bull, mid, level = False, s2, s2.bottom
            kind = "breaker" if s3.top > s1.top else "mitigation" if s3.top < s1.top else None
        else:
            continue
        if kind is None or mid.origin_ts not in pos or s3.origin_ts not in pos:
            continue
        i3 = pos[s3.origin_ts]
        extreme = l[i3] if bull else h[i3]
        after = range(i3 + 1, len(df))
        k = None
        for j in after:
            if (bull and l[j] < extreme) or (not bull and h[j] > extreme):
                break                                # the second swing was not the low/high after all
            if (bull and c[j] > level) or (not bull and c[j] < level):
                k = j
                break
        if k is None:
            continue
        run = _colour_run(o, c, pos[mid.origin_ts], up=bull, lo=pos[s1.origin_ts] + 1)
        if run is None:
            continue
        a, b = run
        known = max(pd.Timestamp(cts[k]), s3.ts)
        out.append(Event(kind, tf, "bull" if bull else "bear", known, df.index[a],
                         float(h[a:b + 1].max()), float(l[a:b + 1].min()),
                         {"swept": kind == "breaker", "broke": float(level)}))
    return sorted(out, key=lambda e: e.ts)


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


def equal_levels(bars: pd.DataFrame, swing_events: Iterable[Event], tol: float) -> list[Level]:
    """Relative equal highs/lows: two or more swing highs (lows) within ``tol`` of each other, with no trade beyond
    the cluster in between. Buy stops rest above equal highs, sell stops below equal lows; ICT calls them a larger
    pool and a stronger draw than a single high (Jan 12 2026; rulings §12). Each cluster becomes a Level from the
    moment its second swing is confirmed; a further touch emits an updated level (name ``eqh3@…``).
    ``bars`` = the bars the swings came from (to check nothing traded through the cluster between touches)."""
    h, l = _arr(bars, "high"), _arr(bars, "low")
    idx = bars.index
    out = []
    for side, kind in (("high", "swing_high"), ("low", "swing_low")):
        sw = sorted((e for e in swing_events if e.kind == kind), key=lambda e: e.origin_ts)
        clusters = []          # [extreme, touches, last_origin_pos, first_origin]
        for e in sw:
            pos = int(idx.searchsorted(e.origin_ts))
            price = e.top if side == "high" else e.bottom
            alive = []
            for c in clusters:
                between = slice(c[2] + 1, pos)
                if side == "high":
                    taken = h[between].size and h[between].max() > c[0] + tol
                else:
                    taken = l[between].size and l[between].min() < c[0] - tol
                if not taken:
                    alive.append(c)
            clusters = alive
            match = next((c for c in clusters if abs(price - c[0]) <= tol), None)
            if match is None:
                clusters.append([price, 1, pos, e.origin_ts])
                continue
            match[0] = max(match[0], price) if side == "high" else min(match[0], price)
            match[1] += 1
            match[2] = pos
            tag = ("eqh" if side == "high" else "eql") + (str(match[1]) if match[1] > 2 else "")
            out.append(Level(f"{e.tf}_{tag}@{match[3]:%m-%d %H:%M}", float(match[0]), side, e.ts))
    return sorted(out, key=lambda lv: lv.valid_from)


@dataclass(frozen=True)
class Pool:
    """Liquidity levels on one side that sit within ``tol`` of each other (e.g. equal highs just under the PDH):
    one pool, priced at its outermost member (where all the stops are taken)."""
    side: str
    price: float
    inner: float
    members: tuple[str, ...]
    prices: tuple[float, ...] = ()

    @property
    def strength(self) -> int:
        """How many stops the pool likely holds: each distinct single level counts 1, plus the touches of the
        best equal-highs/lows cluster in it (eqh = 2, eqh3 = 3). The same highs seen again on another timeframe
        or re-emitted after an extra touch are not counted twice."""
        singles, eq = set(), 0
        prices = self.prices or (None,) * len(self.members)
        for m, px in zip(self.members, prices):
            k = m.split("@")[0].split("_")[-1]
            if k.startswith(("eqh", "eql")):
                eq = max(eq, int(k[3:] or 2))
            else:
                singles.add(px if px is not None else m)     # one high named PDH, D high and 4H high = one level
        return len(singles) + eq


def liquidity_pools(levels: Iterable[Level], tol: float) -> list[Pool]:
    """Group same-side levels whose prices lie within ``tol`` of the next one (single-linkage). Pass only levels
    that exist and are still untaken at the moment of use."""
    out = []
    for side in ("high", "low"):
        lv = sorted((x for x in levels if x.side == side), key=lambda x: x.price)
        group = []
        for x in lv + [None]:
            if x is not None and (not group or x.price - group[-1].price <= tol):
                group.append(x)
                continue
            if group:
                prices = [g.price for g in group]
                outer, inner = (max(prices), min(prices)) if side == "high" else (min(prices), max(prices))
                out.append(Pool(side, outer, inner, tuple(g.name for g in group), tuple(g.price for g in group)))
            group = [x] if x is not None else []
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
