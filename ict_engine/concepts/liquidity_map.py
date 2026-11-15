"""Liquidity map: what liquidity and which areas matter *from where price is now* (concept layer — detected, not
scored). Sharif 2026-11-15: "a task to identify liquidity … daily is important and the others help … based on where
price currently is when we open the chart to hunt".

``build(bars_1m, as_of)`` reads only bars before ``as_of`` and returns:
    price      last price
    adr        mean daily range of the last 20 days (distances are also given in ADR)
    items      every untaken level / unfilled area within ``max_adr`` ADR of price, each tagged:
                 tf     1w | 1d | 4h | 1h | session
                 kind   pdh pdl pwh pwl pmh pml asia_high asia_low london_high london_low   (context)
                        swing_high swing_low                                                (untaken swings)
                        eqh eql                                                             (equal highs / lows)
                        fvg vi                                                              (unfilled imbalances)
                        nwog                                                                (new week opening gap)
                 where  above | below (price)
                 role   buyside | sellside (resting stops) | area (imbalance: a draw or a place to react)
    key        nearest buyside above / sellside below per timeframe, the daily dealing range and where price sits
               in it (premium / discount), the daily bias reads, and the daily draw in the bias direction
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import build_context
from ict_engine.concepts.events import equal_levels, fvgs, gap_lifecycle, swings, volume_imbalances

NY = "America/New_York"
LOOKBACK = {"1w": timedelta(days=730), "1d": timedelta(days=180), "4h": timedelta(days=30), "1h": timedelta(days=7)}
EQ_BP = {"1w": 20.0, "1d": 10.0, "4h": 4.0, "1h": 2.0}
REACH = {"1w": 2.0}                     # weekly levels may sit up to 2× max_adr away
PER_SIDE = {"swing": 4, "eq": 2, "gap": 3}
TF_ORDER = {"1w": -1, "1d": 0, "4h": 1, "1h": 2, "session": 3}


@dataclass
class Item:
    id: str
    tf: str
    kind: str
    where: str
    role: str
    price: float                 # the level, or the near edge of an area
    top: float | None = None     # areas only
    bottom: float | None = None
    formed: str = ""
    dist: float = 0.0            # |price − last|
    dist_adr: float = 0.0
    label: str = ""
    also: tuple[str, ...] = ()   # the same price found on other timeframes / as other kinds (confluence)


def _ny(ts) -> pd.Timestamp:
    return pd.Timestamp(ts).tz_convert(NY)


def _untaken(bars: pd.DataFrame, since: pd.Timestamp, price: float, high: bool) -> bool:
    seg = bars[bars.index > since]
    return seg.empty or (seg.high.max() < price if high else seg.low.min() > price)


def _daily(hist: pd.DataFrame) -> pd.DataFrame:
    """NY trading days (18:00 → 17:00) as daily bars, index = session date 00:00."""
    h = hist.copy()
    h["session"] = (h.index + pd.Timedelta(hours=6)).normalize()
    d = h.groupby("session").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    d["close_ts"] = [hist.index[hist.index < s + pd.Timedelta(hours=18)].max() for s in d.index]
    return d


CTX_KINDS = ("pmh", "pml", "pwh", "pwl", "pdh", "pdl", "london_high", "london_low", "asia_high", "asia_low")


def _merge(items: list[Item], last: float, bp: float = 0.5) -> list[Item]:
    """One item per price and role: context names first, then the highest timeframe; the rest go to ``also``."""
    def rank(it):
        return (0 if it.kind in CTX_KINDS else 1, TF_ORDER[it.tf], it.kind)
    out: list[Item] = []
    for it in sorted(items, key=rank):
        twin = next((o for o in out if o.role == it.role and abs(o.price - it.price) <= last * bp / 1e4
                     and (it.role != "area" or (o.top, o.bottom) == (it.top, it.bottom))), None)
        if twin is None:
            out.append(it)
        else:
            twin.also = twin.also + (f"{it.tf} {it.kind}",)
    return sorted(out, key=lambda it: (it.dist, TF_ORDER[it.tf]))


def weekly(daily: pd.DataFrame) -> pd.DataFrame:
    """Completed-session daily bars → weekly bars (Monday-dated; a week's Sunday evening belongs to its Monday)."""
    if daily.empty:
        return daily
    wk = daily.index - pd.to_timedelta(daily.index.weekday, unit="D")
    return daily.groupby(wk).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                 close=("close", "last"), close_ts=("close_ts", "last"))


def build(bars_1m: pd.DataFrame, as_of: pd.Timestamp, max_adr: float = 4.0) -> dict:
    as_of = _ny(as_of)
    hist = bars_1m[(bars_1m.index >= as_of - LOOKBACK["1w"]) & (bars_1m.index < as_of)]
    if hist.empty:
        raise ValueError("no bars before as_of")
    last = float(hist.close.iloc[-1])
    daily = _daily(hist)
    done = daily[daily.close_ts < as_of - pd.Timedelta(minutes=1)]
    done = done.iloc[:-1] if len(done) and done.index[-1] >= (as_of + pd.Timedelta(hours=6)).normalize() else done
    adr = float((done.high - done.low).tail(20).mean()) if len(done) else float(hist.high.max() - hist.low.min())
    items: list[Item] = []

    def add(tf, kind, role, price, formed, label, top=None, bottom=None):
        where = "above" if price > last else "below"
        d = abs(price - last)
        if d > max_adr * REACH.get(tf, 1.0) * adr:
            return
        items.append(Item(f"{tf}:{kind}:{price:.2f}", tf, kind, where, role, round(float(price), 2),
                          None if top is None else round(float(top), 2), None if bottom is None else round(float(bottom), 2),
                          str(formed), round(d, 2), round(d / adr, 2) if adr else 0.0, label))

    # context levels (session tf for the intraday ones)
    day = (as_of + pd.Timedelta(hours=6)).date()
    try:
        ctx = build_context(bars_1m[bars_1m.index < as_of], day)
    except ValueError:
        ctx = None
    d0 = pd.Timestamp(datetime.combine(day, time(0)), tz=NY)
    if ctx is not None:
        names = {"pdh": ("1d", "buyside", "previous day high"), "pdl": ("1d", "sellside", "previous day low"),
                 "pwh": ("1d", "buyside", "previous week high"), "pwl": ("1d", "sellside", "previous week low"),
                 "asia_high": ("session", "buyside", "Asia high"), "asia_low": ("session", "sellside", "Asia low")}
        for n, (tf, role, label) in names.items():
            v = ctx.levels.get(n)
            since = d0 if n.startswith("asia") else d0 - pd.Timedelta(hours=6)    # Asia ends at 00:00
            if v is not None and _untaken(hist, since, v, role == "buyside"):
                add(tf, n, role, v, "", label)
    month = done[done.index < pd.Timestamp(datetime.combine(day.replace(day=1), time(0)), tz=NY)]
    if len(month):
        pm = month[month.index >= (month.index[-1] - pd.offsets.MonthBegin(1)).normalize()]
        pm = pm[pm.index.month == month.index[-1].month]
        for n, v, role, label in (("pmh", pm.high.max(), "buyside", "previous month high"),
                                  ("pml", pm.low.min(), "sellside", "previous month low")):
            if _untaken(hist, pm.index[-1] + pd.Timedelta(hours=17), v, role == "buyside"):
                add("1d", n, role, v, "", label)
    lon = hist[(hist.index >= d0 + pd.Timedelta(hours=2)) & (hist.index < d0 + pd.Timedelta(hours=5))]
    if as_of >= d0 + pd.Timedelta(hours=5) and len(lon):
        for n, v, role, label in (("london_high", lon.high.max(), "buyside", "London high"),
                                  ("london_low", lon.low.min(), "sellside", "London low")):
            if _untaken(hist, d0 + pd.Timedelta(hours=5), v, role == "buyside"):
                add("session", n, role, v, "", label)

    # swings, equal highs/lows, imbalances per timeframe
    for tf in ("1w", "1d", "4h", "1h"):
        seg = hist[hist.index >= as_of - LOOKBACK[tf]]
        b = weekly(done) if tf == "1w" else done if tf == "1d" else resample(seg, tf)
        b = b[b.index >= as_of - LOOKBACK[tf]]
        if tf == "1w":                                       # drop the week still forming
            sess = (as_of + pd.Timedelta(hours=6)).normalize()
            b = b[b.index < sess - pd.Timedelta(days=sess.weekday())]
        b = b[b.close_ts < as_of]
        if len(b) < 3:
            continue
        sw = [e for e in swings(b, tf) if e.ts < as_of]
        cand = {"above": [], "below": []}
        for e in sw:
            high = e.kind == "swing_high"
            p = e.top if high else e.bottom
            if _untaken(hist, e.ts, p, high) and ((p > last) == high):
                cand["above" if high else "below"].append((abs(p - last), e, p, high))
        for side, lst in cand.items():
            for _, e, p, high in sorted(lst, key=lambda x: x[0])[:PER_SIDE["swing"]]:
                add(tf, "swing_high" if high else "swing_low", "buyside" if high else "sellside", p, _ny(e.origin_ts),
                    f"{tf} swing {'high' if high else 'low'}")
        tol = last * EQ_BP[tf] / 1e4
        eqs = {"above": [], "below": []}
        for lv in equal_levels(b, sw, tol):
            high = lv.side == "high"
            if lv.valid_from < as_of and (lv.price > last) == high and _untaken(hist, lv.valid_from, lv.price, high):
                eqs["above" if high else "below"].append(lv)
        for side, lst in eqs.items():
            for lv in sorted(lst, key=lambda l: abs(l.price - last))[:PER_SIDE["eq"]]:
                high = lv.side == "high"
                add(tf, "eqh" if high else "eql", "buyside" if high else "sellside", lv.price, _ny(lv.valid_from),
                    f"{tf} equal {'highs' if high else 'lows'}")
        gaps = {"above": [], "below": []}
        for g in list(fvgs(b, tf)) + list(volume_imbalances(b, tf)):
            if g.ts >= as_of:
                continue
            st = gap_lifecycle(g, hist, until=as_of)
            if not st.valid_at(as_of) or st.filled is not None:
                continue
            if g.bottom > last:
                gaps["above"].append((g.bottom - last, g))
            elif g.top < last:
                gaps["below"].append((last - g.top, g))
            else:
                gaps["above"].append((0.0, g))                       # price inside it
        for side, lst in gaps.items():
            for _, g in sorted(lst, key=lambda x: x[0])[:PER_SIDE["gap"]]:
                near = g.bottom if side == "above" else g.top
                kind = "fvg" if g.kind == "fvg" else "vi"
                add(tf, kind, "area", near, _ny(g.origin_ts),
                    f"{tf} {'bullish' if g.direction == 'bull' else 'bearish'} {'FVG' if kind == 'fvg' else 'volume imbalance'}",
                    top=g.top, bottom=g.bottom)

    # new week opening gaps (last 4 weeks): Friday's last price → Sunday's first
    wk = hist[hist.index >= as_of - timedelta(days=30)]
    gaps_idx = wk.index[1:][(wk.index[1:] - wk.index[:-1]) > pd.Timedelta(hours=40)]
    for t in gaps_idx:
        i = wk.index.get_loc(t)
        a, b2 = float(wk.close.iloc[i - 1]), float(wk.open.iloc[i])
        top, bottom = max(a, b2), min(a, b2)
        if top - bottom <= 0:
            continue
        after = hist[hist.index >= t]
        if not after.empty and after.low.min() <= bottom and after.high.max() >= top:
            continue                                                 # fully traded through
        near = bottom if bottom > last else (top if top < last else bottom)
        add("1d", "nwog", "area", near, _ny(t), "new week opening gap", top=top, bottom=bottom)

    items = _merge(items, last)

    # key points
    key = {"nearest": {}}
    for tf in ("1w", "1d", "4h", "1h", "session"):
        on = lambda it: it.tf == tf or any(a.startswith(f"{tf} ") for a in it.also)
        up = [it for it in items if on(it) and it.role == "buyside" and it.where == "above"]
        dn = [it for it in items if on(it) and it.role == "sellside" and it.where == "below"]
        key["nearest"][tf] = {"buyside": up[0].id if up else None, "sellside": dn[0].id if dn else None}
    sw = sorted((e for e in swings(done, "1d") if e.ts < as_of), key=lambda e: e.ts) if len(done) >= 3 else []
    hs = [e.top for e in sw if e.kind == "swing_high"]
    ls = [e.bottom for e in sw if e.kind == "swing_low"]
    hi = next((hs[i] for i in range(len(hs) - 1, 0, -1) if hs[i] > hs[i - 1]), None)
    lo = next((ls[i] for i in range(len(ls) - 1, 0, -1) if ls[i] < ls[i - 1]), None)
    if hi is not None and lo is not None and hi > lo:
        frac = (last - lo) / (hi - lo)
        key["daily_range"] = {"low": round(float(lo), 2), "high": round(float(hi), 2), "eq": round(float(hi + lo) / 2, 2),
                              "fraction": round(float(frac), 2),
                              "zone": "premium" if frac > 0.5 else "discount"}
    if ctx is not None:
        key["bias"] = {k: v[0] for k, v in ctx.biases.items() if k in ("prev_day_dol", "dol_weekly", "draw", "prev_day")}
        b = ctx.biases.get("prev_day_dol", ("neutral", ""))[0]
        if b in ("bull", "bear"):
            want = ("above", "buyside") if b == "bull" else ("below", "sellside")
            d = [it for it in items if (it.tf == "1d" or any(a.startswith("1d ") for a in it.also))
                 and it.where == want[0] and it.role == want[1]]
            key["daily_draw"] = d[0].id if d else None
    return {"as_of": str(as_of), "price": round(last, 2), "adr": round(adr, 2),
            "items": [asdict(it) for it in items], "key": key}
