"""Day context — pipeline stage 1. Built once per trading day, then frozen.

``build_context(bars_1m, day)`` uses only bars before ``as_of`` (default 00:00
NY of ``day``), so nothing from the session itself leaks in. Intraday levels
(London high/low, pre-market swings) are added later as events.

Contents:
    levels      PDH/PDL, PWH/PWL, Asia high/low, midnight open, NDOG, NWOG
    ranges      20/40/60-trading-day high/low (HTF dealing ranges, framework §3)
    bias        daily bias (default rule, framework §1) with its reason
    biases      every named bias rule in ``BIAS_RULES`` → (bias, reason)
    liquidity   Level objects for sweep detection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Callable

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.clock import trading_day
from ict_engine.concepts.events import Level

NY = "America/New_York"


def _ts(d: date, t: time) -> pd.Timestamp:
    return pd.Timestamp(datetime.combine(d, t), tz=NY)


# --- pricing ------------------------------------------------------------------

@dataclass(frozen=True)
class Pricing:
    fraction: float      # 0 = range low, 1 = range high
    zone: str            # discount | premium | equilibrium
    quadrant: int        # 1 (lowest 25%) … 4 (highest 25%)


def pricing(price: float, low: float, high: float, eq_band: float = 0.0) -> Pricing:
    """Where ``price`` sits in a dealing range (framework §3). ``eq_band`` = half-width of the
    equilibrium band as a fraction (0 = exactly 50% only)."""
    if high <= low:
        raise ValueError("range high must be above range low")
    f = (price - low) / (high - low)
    zone = "equilibrium" if abs(f - 0.5) <= eq_band else ("premium" if f > 0.5 else "discount")
    quadrant = min(4, max(1, int(f * 4) + 1)) if 0 <= f <= 1 else (1 if f < 0 else 4)
    return Pricing(f, zone, quadrant)


# --- context ------------------------------------------------------------------

@dataclass(frozen=True)
class Gap:
    name: str
    close: float         # price before the gap
    open: float          # price after the gap

    @property
    def top(self) -> float:
        return max(self.close, self.open)

    @property
    def bottom(self) -> float:
        return min(self.close, self.open)

    @property
    def ce(self) -> float:
        return (self.close + self.open) / 2


@dataclass(frozen=True)
class DayContext:
    day: date
    as_of: pd.Timestamp
    levels: dict[str, float]
    ranges: dict[int, tuple[float, float]]       # lookback days -> (low, high)
    bias: str                                    # bull | bear | neutral
    bias_reason: str
    gaps: tuple[Gap, ...] = ()
    liquidity: tuple[Level, ...] = field(default=(), compare=False)
    biases: dict[str, tuple[str, str]] = field(default_factory=dict, compare=False)

    def pricing(self, price: float, lookback: int = 20) -> Pricing:
        lo, hi = self.ranges[lookback]
        return pricing(price, lo, hi)


# --- daily bias rules (a strategy: scored by hit rate in eval/bias.py, never trades) ---
# Each rule takes COMPLETED daily bars (resample(..., "1d"), oldest first) and returns
# (bias, reason) with bias in bull | bear | neutral.

BiasRule = Callable[[pd.DataFrame], tuple[str, str]]


def bias_prev_day(daily: pd.DataFrame) -> tuple[str, str]:
    """v1 heuristic (framework §1): compare the last two completed trading days.

    bear: yesterday took the prior day's low and made a lower high (sell-side being taken)
    bull: yesterday took the prior day's high and made a higher low
    else neutral.
    """
    if len(daily) < 2:
        return "neutral", "not enough history"
    d2, d1 = daily.iloc[-2], daily.iloc[-1]
    if d1.low < d2.low and d1.high < d2.high:
        return "bear", "previous day took the prior low with a lower high"
    if d1.high > d2.high and d1.low > d2.low:
        return "bull", "previous day took the prior high with a higher low"
    if d1.high > d2.high and d1.low < d2.low:
        return "neutral", "outside day (both sides taken)"
    return "neutral", "inside day"


daily_bias = bias_prev_day   # backwards-compatible name


def bias_htf20(daily: pd.DataFrame, n: int = 20) -> tuple[str, str]:
    """HTF dealing range: last close above the equilibrium of the last ``n`` completed days → bull,
    else bear (framework §3: buy in discount of a bullish range, i.e. bias follows where price sits)."""
    if len(daily) < n:
        return "neutral", f"not enough history (<{n} days)"
    w = daily.tail(n)
    eq = (float(w.high.max()) + float(w.low.min())) / 2
    close = float(daily.close.iloc[-1])
    if close > eq:
        return "bull", f"close above {n}-day equilibrium"
    return "bear", f"close at/below {n}-day equilibrium"


def bias_htf40(daily: pd.DataFrame) -> tuple[str, str]:
    """Weekly-scale trend: ``htf20`` over 40 completed days (≈ 8 weeks). Used to size the target, not to gate:
    against it a trade takes the near liquidity only (Sharif: "you can't expect distanced areas to be reached")."""
    return bias_htf20(daily, 40)


def bias_draw(daily: pd.DataFrame) -> tuple[str, str]:
    """ICT's daily bias: the side of the previous day's range not yet run, in line with the HTF draw.

    Previous day took only the prior day's high → bull (draw continues higher); only the low → bear;
    inside day → neutral; outside day → neutral (indecision), except an outside day closing in its
    lower half while the HTF range is bullish → bull ("an outside day with a down close... typically
    bullish... if we're in a bullish market" — ICT, Essentials To Trading The Daily Bias,
    13 Dec 2017), and the mirror (upper-half close in a bearish HTF range → bear).
    """
    if len(daily) < 2:
        return "neutral", "not enough history"
    d2, d1 = daily.iloc[-2], daily.iloc[-1]
    took_high, took_low = d1.high > d2.high, d1.low < d2.low
    if took_high and not took_low:
        return "bull", "previous day ran the prior high only"
    if took_low and not took_high:
        return "bear", "previous day ran the prior low only"
    if not took_high and not took_low:
        return "neutral", "inside day"
    htf, _ = bias_htf20(daily)
    mid = (float(d1.high) + float(d1.low)) / 2
    if float(d1.close) < mid and htf == "bull":
        return "bull", "outside day closing in its lower half, HTF bullish"
    if float(d1.close) > mid and htf == "bear":
        return "bear", "outside day closing in its upper half, HTF bearish"
    return "neutral", "outside day (both sides taken)"


def bias_draw_htf(daily: pd.DataFrame) -> tuple[str, str]:
    """``draw``; when it is neutral, fall back to ``htf20``."""
    b, why = bias_draw(daily)
    if b != "neutral":
        return b, why
    hb, hwhy = bias_htf20(daily)
    return hb, f"{why}; fallback: {hwhy}"


def _untaken_swings(w: pd.DataFrame) -> tuple[list[float], list[float]]:
    """Daily swing highs/lows (3-bar fractals) in ``w`` that no later bar in ``w`` has traded through
    (old highs/lows still holding resting liquidity)."""
    h, lo = w.high.to_numpy(float), w.low.to_numpy(float)
    highs, lows = [], []
    for i in range(1, len(w) - 1):
        if h[i] > h[i - 1] and h[i] > h[i + 1] and h[i + 1:].max() < h[i]:
            highs.append(float(h[i]))
        if lo[i] < lo[i - 1] and lo[i] < lo[i + 1] and lo[i + 1:].min() > lo[i]:
            lows.append(float(lo[i]))
    return highs, lows


def _open_fvgs(w: pd.DataFrame) -> tuple[list[float], list[float]]:
    """Daily FVGs in ``w`` whose consequent encroachment (50%) no later bar has reached, as the
    gap's near edge: bearish gaps → their bottom (a draw up), bullish gaps → their top (a draw down)."""
    h, lo = w.high.to_numpy(float), w.low.to_numpy(float)
    bear_bottoms, bull_tops = [], []
    for i in range(2, len(w)):
        later_h, later_l = h[i + 1:], lo[i + 1:]
        if h[i - 2] < lo[i]:                                  # bullish FVG [h[i-2], lo[i]]
            ce = (h[i - 2] + lo[i]) / 2
            if not len(later_l) or later_l.min() > ce:
                bull_tops.append(float(lo[i]))
        if lo[i - 2] > h[i]:                                  # bearish FVG [h[i], lo[i-2]]
            ce = (h[i] + lo[i - 2]) / 2
            if not len(later_h) or later_h.max() < ce:
                bear_bottoms.append(float(h[i]))
    return bear_bottoms, bull_tops


def bias_dol(daily: pd.DataFrame, n: int = 60) -> tuple[str, str]:
    """HTF draw on liquidity: the side of the nearest untaken daily liquidity from the last close.

    Candidates over the last ``n`` completed days (IPDA 60-day look-back): old swing highs above /
    swing lows below not yet traded through, and unfilled daily FVGs (CE not reached; near edge used).
    Nearest above → bull, nearest below → bear; nothing on either side → neutral. ICT: "where's the
    next inefficiency it may be drawing to" / the nearest old high or low price is reaching for.
    """
    if len(daily) < n:
        return "neutral", f"not enough history (<{n} days)"
    w = daily.tail(n)
    c = float(daily.close.iloc[-1])
    sh, sl = _untaken_swings(w)
    fa, fb = _open_fvgs(w)
    above = [(x - c, "old high") for x in sh if x > c] + [(x - c, "bearish FVG") for x in fa if x > c]
    below = [(c - x, "old low") for x in sl if x < c] + [(c - x, "bullish FVG") for x in fb if x < c]
    if not above and not below:
        return "neutral", "no untaken liquidity either side"
    up = min(above) if above else (float("inf"), "")
    dn = min(below) if below else (float("inf"), "")
    if up[0] < dn[0]:
        return "bull", f"nearest draw is {up[1]} {up[0]:.2f} above"
    return "bear", f"nearest draw is {dn[1]} {dn[0]:.2f} below"


def _weekly(daily: pd.DataFrame) -> tuple[pd.DataFrame, date] | None:
    """Weekly high/low from completed daily bars (grouped by the Monday of each trading day) and
    the last trading day. ``None`` when the bars carry no timestamps."""
    if "close_ts" in daily:
        ts = pd.DatetimeIndex(daily["close_ts"])
    elif isinstance(daily.index, pd.DatetimeIndex):
        ts = daily.index
    else:
        return None
    if ts.tz is None:
        return None
    days = pd.to_datetime(pd.Index(trading_day(ts.tz_convert(NY))))
    monday = days - pd.to_timedelta(days.day_of_week, unit="D")
    g = daily.groupby(monday.to_numpy()).agg(high=("high", "max"), low=("low", "min"))
    return g, days[-1].date()


def bias_dol_weekly(daily: pd.DataFrame) -> tuple[str, str]:
    """Weekly draw: the side of the previous week's range this week has run so far.

    This week's completed days took PWH only → bull, PWL only → bear, both → neutral. A new week
    (last completed day is a Friday) or a week that has taken neither side falls back to which side
    of the week before the previous week ran. ICT: weekly range expansion is "the stage for all".
    """
    wk = _weekly(daily) if len(daily) else None
    if wk is None:
        return "neutral", "no timestamps for weekly grouping"
    g, last = wk
    done, cur = (g, None) if last.weekday() == 4 else (g.iloc[:-1], g.iloc[-1])

    def side(new, old, what):
        th, tl = new.high > old.high, new.low < old.low
        if th and tl:
            return "neutral", f"{what} took both sides of the prior week"
        if th:
            return "bull", f"{what} ran the prior week's high only"
        if tl:
            return "bear", f"{what} ran the prior week's low only"
        return None

    if cur is not None and len(done) >= 1:
        r = side(cur, done.iloc[-1], "this week")
        if r is not None:
            return r
    if len(done) < 2:
        return "neutral", "not enough weekly history"
    return side(done.iloc[-1], done.iloc[-2], "last week") or ("neutral", "last week was an inside week")


WEEKLY_BREAK_ATR = 0.25          # a weekly break must close this many weekly ATRs (14 weeks) beyond the protected level


def _weekly_bars(daily: pd.DataFrame) -> pd.DataFrame | None:
    """Completed weeks (high, low, close; index = Monday) from completed daily bars; the unfinished current week dropped."""
    wk = _weekly(daily) if len(daily) else None
    if wk is None:
        return None
    g, last = wk
    ts = pd.DatetimeIndex(daily["close_ts"]) if "close_ts" in daily else daily.index
    days = pd.to_datetime(pd.Index(trading_day(ts.tz_convert(NY))))
    monday = days - pd.to_timedelta(days.day_of_week, unit="D")
    g["close"] = daily.groupby(monday.to_numpy()).close.last()
    return g if last.weekday() == 4 else g.iloc[:-1]


def _term_swings(w: pd.DataFrame) -> tuple[list, list]:
    """ICT's hierarchy (Core Content Month 12): a short-term high is a week with a lower high either side (known one week
    later); an intermediate-term high is a short-term high with a lower short-term high either side (known once the next
    short-term high is). Lows mirror. Returns ([(i, price, known_at_i)] ITH, same ITL)."""
    h, lo = w.high.to_numpy(float), w.low.to_numpy(float)
    sth = [(i, h[i]) for i in range(1, len(w) - 1) if h[i] > h[i - 1] and h[i] > h[i + 1]]
    stl = [(i, lo[i]) for i in range(1, len(w) - 1) if lo[i] < lo[i - 1] and lo[i] < lo[i + 1]]

    def it(xs, high):
        return [(xs[a][0], float(xs[a][1]), xs[a + 1][0] + 1) for a in range(1, len(xs) - 1)
                if ((xs[a][1] > xs[a - 1][1] and xs[a][1] > xs[a + 1][1]) if high
                    else (xs[a][1] < xs[a - 1][1] and xs[a][1] < xs[a + 1][1]))]
    return it(sth, True), it(stl, False)


def weekly_structure_state(w: pd.DataFrame, m: float = WEEKLY_BREAK_ATR, n_atr: int = 14):
    """Walk completed weeks; return (state, guard, flips). Sharif 2026-11-16 + ruling §21 (shift ≠ break):
    - bear: the guard is the intermediate-term high the latest intermediate-term low came from (the protected lower
      high). Higher highs below it are shifts, not a change. A weekly close above guard + m × weekly ATR is a break →
      bull. Price trading above the guard without such a close → the guard rises to that high (the range top).
    - bull: mirror with the protected higher low. neutral until the first break of an intermediate-term level.
    Swings count only from the week they are known (no look-ahead)."""
    ith, itl = _term_swings(w)
    c, h, lo = w.close.to_numpy(float), w.high.to_numpy(float), w.low.to_numpy(float)
    rng = h - lo
    state, guard, flips, seen_low, seen_high = "neutral", None, [], None, None
    for i in range(len(w)):
        atr = rng[max(0, i - n_atr):i].mean() if i else rng[0]
        hs = [(j, p) for j, p, k in ith if k <= i]
        ls = [(j, p) for j, p, k in itl if k <= i]
        if state == "neutral":
            if hs and c[i] > hs[-1][1] + m * atr:
                state, guard, seen_high = "bull", (ls[-1][1] if ls else lo[i]), hs[-1]; flips.append((w.index[i], "bull"))
            elif ls and c[i] < ls[-1][1] - m * atr:
                state, guard, seen_low = "bear", (hs[-1][1] if hs else h[i]), ls[-1]; flips.append((w.index[i], "bear"))
        elif state == "bear":
            if ls and ls[-1] != seen_low and hs and hs[-1][0] < ls[-1][0]:      # a new lower low → its lower high guards
                guard, seen_low = hs[-1][1], ls[-1]
            if c[i] > guard + m * atr:
                state, guard, seen_high = "bull", (ls[-1][1] if ls else lo[i]), (hs[-1] if hs else None)
                flips.append((w.index[i], "bull"))
            elif h[i] > guard:
                guard = float(h[i])
        else:
            if hs and hs[-1] != seen_high and ls and ls[-1][0] < hs[-1][0]:
                guard, seen_high = ls[-1][1], hs[-1]
            if c[i] < guard - m * atr:
                state, guard, seen_low = "bear", (hs[-1][1] if hs else h[i]), (ls[-1] if ls else None)
                flips.append((w.index[i], "bear"))
            elif lo[i] < guard:
                guard = float(lo[i])
    return state, guard, flips


def weekly_swings(daily: pd.DataFrame) -> tuple[pd.DataFrame, list, list] | None:
    """Completed weeks and their intermediate-term swings [(week_start, price)] (for display), or None."""
    w = _weekly_bars(daily)
    if w is None:
        return None
    ith, itl = _term_swings(w)
    return w, [(w.index[i], p) for i, p, _ in ith], [(w.index[i], p) for i, p, _ in itl]


def bias_weekly_structure(daily: pd.DataFrame) -> tuple[str, str]:
    """Weekly trend from structure: lower highs + lower lows = bear, until a weekly close breaks the protected lower high
    (intermediate-term) with displacement. See ``weekly_structure_state``. Needs ~1–2 years of daily bars."""
    w = _weekly_bars(daily)
    if w is None:
        return "neutral", "no timestamps for weekly grouping"
    state, guard, flips = weekly_structure_state(w)
    if state == "neutral":
        return "neutral", f"no intermediate-term break yet ({len(w)} weeks)"
    since = flips[-1][0]
    return state, f"{state} since week of {pd.Timestamp(since).date()}; protected {'high' if state == 'bear' else 'low'} {guard:.2f}"


def bias_prev_day_dol(daily: pd.DataFrame) -> tuple[str, str]:
    """``prev_day``; on its neutral days (inside/outside), the HTF draw ``dol`` breaks the tie."""
    b, why = bias_prev_day(daily)
    if b != "neutral":
        return b, why
    db, dwhy = bias_dol(daily)
    return db, f"{why}; tie-break: {dwhy}"


def bias_draw_dol(daily: pd.DataFrame) -> tuple[str, str]:
    """ICT's full sentence: the unrun side of yesterday's range (``draw``) *in line with* the HTF draw
    on liquidity (``dol``). Call only when both agree, else neutral (wait for the 09:30–10:00 move)."""
    b, why = bias_draw(daily)
    db, dwhy = bias_dol(daily)
    if b != "neutral" and b == db:
        return b, f"{why}; {dwhy}"
    return "neutral", f"draw={b}, dol={db} (not aligned)"


BIAS_RULES: dict[str, BiasRule] = {
    "prev_day": bias_prev_day,
    "htf20": bias_htf20,
    "htf40": bias_htf40,
    "weekly_structure": bias_weekly_structure,
    "draw": bias_draw,
    "draw_htf": bias_draw_htf,
    "dol": bias_dol,
    "dol_weekly": bias_dol_weekly,
    "prev_day_dol": bias_prev_day_dol,
    "draw_dol": bias_draw_dol,
}
DEFAULT_BIAS_RULE = "prev_day"


def completed_daily(daily: pd.DataFrame, day: date, as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Daily bars (from ``resample(..., "1d")``) that were complete before ``day``'s context:
    closed before 17:00 NY the evening before ``day`` (and before ``as_of``)."""
    as_of = as_of or _ts(day, time(0))
    cut = min(_ts(day - timedelta(days=1), time(17)), as_of)
    return daily[daily["close_ts"] < cut]


def all_biases(daily: pd.DataFrame) -> dict[str, tuple[str, str]]:
    return {name: rule(daily) for name, rule in BIAS_RULES.items()}


def build_context(bars_1m: pd.DataFrame, day: date, as_of: pd.Timestamp | None = None) -> DayContext:
    as_of = as_of or _ts(day, time(0))
    past = bars_1m[bars_1m.index < as_of]
    if past.empty:
        raise ValueError(f"no bars before {as_of}")

    daily = resample(past, "1d")
    daily = completed_daily(daily, day, as_of)   # completed days only
    if daily.empty:
        raise ValueError(f"no completed trading day before {day}")
    weekly = resample(past, "1w")
    this_week_start = _ts(day - timedelta(days=day.weekday() + 1), time(18))   # Sunday 18:00
    prev_weeks = weekly[weekly["close_ts"] < this_week_start]

    lv: dict[str, float] = {"pdh": float(daily.high.iloc[-1]), "pdl": float(daily.low.iloc[-1])}
    if not prev_weeks.empty:
        lv["pwh"], lv["pwl"] = float(prev_weeks.high.iloc[-1]), float(prev_weeks.low.iloc[-1])

    asia = past[(past.index >= _ts(day - timedelta(days=1), time(20))) & (past.index < _ts(day, time(0)))]
    if not asia.empty:
        lv["asia_high"], lv["asia_low"] = float(asia.high.max()), float(asia.low.min())
    mid = bars_1m[bars_1m.index == _ts(day, time(0))]
    if not mid.empty and as_of >= _ts(day, time(0)):
        lv["midnight_open"] = float(mid.open.iloc[0])

    gaps = []
    # NDOG: last print before 17:00 → first print from 18:00 the evening before `day`
    prev_eve = day - timedelta(days=1)
    before = past[(past.index < _ts(prev_eve, time(17))) & (past.index >= _ts(prev_eve, time(16)))]
    after = past[past.index >= _ts(prev_eve, time(18))]
    if not before.empty and not after.empty and day.weekday() != 0:
        gaps.append(Gap("ndog", float(before.close.iloc[-1]), float(after.open.iloc[0])))
    # NWOG: Friday's last print → Sunday's first print of this week
    fri = this_week_start - timedelta(days=2)
    fri_bars = past[(past.index < _ts(fri.date(), time(17))) & (past.index >= _ts(fri.date(), time(9)))]
    sun_bars = past[past.index >= this_week_start]
    if not fri_bars.empty and not sun_bars.empty:
        gaps.append(Gap("nwog", float(fri_bars.close.iloc[-1]), float(sun_bars.open.iloc[0])))

    ranges = {}
    for n in (20, 40, 60):
        w = daily.tail(n)
        ranges[n] = (float(w.low.min()), float(w.high.max()))

    biases = all_biases(daily)
    bias, reason = biases[DEFAULT_BIAS_RULE]

    sides = {"pdh": "high", "pwh": "high", "asia_high": "high", "pdl": "low", "pwl": "low", "asia_low": "low"}
    liquidity = tuple(Level(name, lv[name], side, as_of) for name, side in sides.items() if name in lv)
    return DayContext(day, as_of, lv, ranges, bias, reason, tuple(gaps), liquidity, biases)
