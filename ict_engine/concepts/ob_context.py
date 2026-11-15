"""Order blocks in their place (concept layer: facts, no score). Ruling §22 (ictindex): an OB is a change in the state of
delivery AFTER a transitional event — liquidity traded to, or an inefficiency revisited; "not every down-closed candle
is an order block". Sharif (2026-11-16): body only; "a OB at an unimportant zone means nothing"; after a bearish OB the
next interest is the remaining FVG below (and the liquidity on its edge) — what happens in that FVG decides the leg.

    period_bars(daily, "M"|"W", as_of)   completed monthly / weekly OHLC bars from completed daily bars
    ob_reads(bars, tf, as_of)            every OB on ``bars`` known by ``as_of`` with: event (what it took / revisited),
                                         place (premium / discount of the look-back range, its fraction), draw (the
                                         next unfilled FVG on the retrace side + liquidity at its edge) and how price
                                         has behaved in that FVG since (untouched / respected / closed through → IFVG)

Bearish described; bullish mirrors. Everything is measured from bars closed by ``as_of`` (no look-ahead).
"""
from __future__ import annotations

import pandas as pd

from ict_engine.concepts.clock import trading_day
from ict_engine.concepts.events import equal_levels, fvgs, order_blocks, swing_levels, swings

NY = "America/New_York"
LOOKBACK = {"1M": 12, "1w": 20, "1d": 40, "4h": 60, "1h": 60}     # ICT's 20/40/60 IPDA look-back; 12 months on 1M


def period_bars(daily: pd.DataFrame, freq: str, as_of: pd.Timestamp) -> pd.DataFrame:
    """Completed months ("M") or weeks ("W") from completed daily bars (``close_ts`` = the session's last minute).
    Grouped by trading day, so a session that starts on the 31st at 18:00 belongs to the next month. The period that
    contains ``as_of``'s trading day is unfinished and dropped."""
    ts = pd.DatetimeIndex(daily["close_ts"]) if "close_ts" in daily else daily.index
    days = pd.to_datetime(pd.Index(trading_day(ts.tz_convert(NY))))
    key = days.to_period(freq)
    g = daily.groupby(key.to_numpy())
    out = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()})
    out["close_ts"] = pd.DatetimeIndex(g.apply(lambda x: (x["close_ts"] if "close_ts" in x else x.index.to_series()).iloc[-1]))
    out.index = pd.DatetimeIndex([p.start_time for p in out.index]).tz_localize(NY)
    now = pd.Timestamp(trading_day(pd.DatetimeIndex([as_of]))[0]).to_period(freq)
    keep = [pd.Timestamp(i).tz_localize(None).to_period(freq) != now for i in out.index]
    return out[keep]


def _event(bars: pd.DataFrame, ob, tf: str) -> dict | None:
    """What the OB's move (OB candle → validating candle) traded to: the highest buyside level (equal highs first, then
    a swing high) above the OB body, known before the OB candle and not taken before it — or a bearish FVG above that
    it revisited. Bullish mirrors."""
    bear = ob.direction == "bear"
    a = bars.index.get_loc(ob.origin_ts)
    i = int(bars.index.searchsorted(ob.ts, side="left"))
    if "close_ts" in bars:
        i = int((bars["close_ts"] <= ob.ts).to_numpy().nonzero()[0][-1])
    move = bars.iloc[a:i + 1]
    ext = move.high.max() if bear else move.low.min()
    hist = bars.iloc[:a]
    sw = [e for e in swings(hist, tf) if e.ts <= bars.index[a]]
    tol = 0.1 * float((hist.high - hist.low).tail(14).mean()) if len(hist) else 0.0
    side = "high" if bear else "low"
    lv = [x for x in equal_levels(hist, sw, tol) + swing_levels(sw) if x.side == side]
    body_top, body_bot = ob.meta["body"]
    taken = []
    for x in lv:
        later = bars.loc[x.valid_from:bars.index[a - 1]] if a else bars.iloc[:0]
        gone = (later.high.max() > x.price) if bear else (later.low.min() < x.price)
        if gone or not ((body_top < x.price <= ext) if bear else (ext <= x.price < body_bot)):
            continue
        taken.append(x)
    if taken:
        own = float(bars.high.iloc[a] if bear else bars.low.iloc[a])          # the OB candle's own high (low)
        eq = [x for x in taken if "eq" in x.name or abs(x.price - own) <= tol]   # a swing level the OB candle matched
        best = (max if bear else min)(eq or taken, key=lambda x: x.price)
        return {"kind": "liquidity", "what": "equal highs" if bear and eq else "equal lows" if eq else
                ("swing high" if bear else "swing low"), "price": round(float(best.price), 2), "extreme": round(float(ext), 2)}
    hit = []
    for g in fvgs(hist, tf):                      # an open gap beyond the OB body that the move reached into
        if g.direction != ("bear" if bear else "bull"):
            continue
        if not ((body_bot < g.bottom <= ext) if bear else (ext <= g.top < body_top)):   # reached; may overlap the body
            continue
        later = hist[hist.index > g.origin_ts].iloc[1:]
        if len(later) and ((later.high.max() >= g.bottom) if bear else (later.low.min() <= g.top)):
            continue                              # already revisited before: not this move's event
        hit.append(g)
    if hit:
        g = min(hit, key=lambda x: x.bottom) if bear else max(hit, key=lambda x: x.top)
        return {"kind": "inefficiency", "what": f"{tf} {'bearish' if bear else 'bullish'} FVG revisited",
                "price": round(float(g.bottom if bear else g.top), 2), "extreme": round(float(ext), 2)}
    return None


def _place(bars: pd.DataFrame, ob, tf: str) -> dict:
    i = int((bars["close_ts"] <= ob.ts).to_numpy().nonzero()[0][-1]) if "close_ts" in bars else bars.index.get_loc(ob.ts)
    w = bars.iloc[max(0, i + 1 - LOOKBACK.get(tf, 20)):i + 1]
    lo, hi = float(w.low.min()), float(w.high.max())
    top, bot = ob.meta["body"]
    f = ((top + bot) / 2 - lo) / (hi - lo) if hi > lo else 0.5
    return {"range": (round(lo, 2), round(hi, 2)), "fraction": round(f, 2), "zone": "premium" if f >= 0.5 else "discount",
            "fits": (f >= 0.5) == (ob.direction == "bear")}


def _draw(bars: pd.DataFrame, ob, tf: str, as_of: pd.Timestamp, fine: pd.DataFrame | None = None) -> dict | None:
    """The nearest FVG on the retrace side (below a bearish OB) still open when the OB was confirmed, the liquidity
    resting at its near edge, and what price has done in it since: closes of this timeframe up to ``as_of``, plus the
    unfinished current candle from ``fine`` (lower-timeframe bars) — its close is still pending."""
    bear = ob.direction == "bear"
    known = bars[bars["close_ts"] <= ob.ts] if "close_ts" in bars else bars[bars.index <= ob.ts]
    ref = float(known.close.iloc[-1])
    gaps = []
    for g in fvgs(known, tf):
        if g.direction != ("bull" if bear else "bear"):
            continue
        after = known[known.index > g.origin_ts].iloc[1:]
        # "the remaining FVG": one price has already traded right through (wick beyond its far edge) is used up
        filled = (after.low < g.bottom).any() if bear else (after.high > g.top).any()
        if not filled and ((g.top < ref) if bear else (g.bottom > ref)):
            gaps.append(g)
    if not gaps:
        return None
    g = max(gaps, key=lambda x: x.top) if bear else min(gaps, key=lambda x: x.bottom)
    sw = swing_levels(e for e in swings(known, tf))
    edge = [x for x in sw if x.side == ("low" if bear else "high") and
            ((g.bottom <= x.price <= ref) if bear else (ref <= x.price <= g.top))]
    liq = (min if bear else max)(edge, key=lambda x: x.price).price if edge else None
    since = bars[(bars.index > known.index[-1]) & ((bars["close_ts"] if "close_ts" in bars else bars.index) <= as_of)]
    ce = (g.top + g.bottom) / 2
    pending = ""
    if fine is not None:
        last_close = (since["close_ts"].iloc[-1] if len(since) and "close_ts" in since else known["close_ts"].iloc[-1]
                      if "close_ts" in known else known.index[-1])
        cur = fine[(fine.index > last_close) & (fine.index < as_of)]
        if len(cur):
            lo, hi = float(cur.low.min()), float(cur.high.max())
            into = (lo <= g.top) if bear else (hi >= g.bottom)
            if into:
                depth = ((g.top - lo) / (g.top - g.bottom)) if bear else ((hi - g.bottom) / (g.top - g.bottom))
                how = ("right through it (wick)" if depth > 1 else f"{depth:.0%} into it"
                       + (" — past its midpoint" if depth > 0.5 else ""))
                pending = (f"; the current {tf} candle (close pending) reached {lo if bear else hi:.2f} = {how}, "
                           f"now {float(cur.close.iloc[-1]):.2f}")
    if since.empty or ((since.low.min() > g.top) if bear else (since.high.max() < g.bottom)):
        state = "not reached yet"
    elif (since.close < g.bottom).any() if bear else (since.close > g.top).any():
        state = "closed through → IFVG, continuation"
    elif ((since[["open", "close"]].min(axis=1) < ce).any() if bear else (since[["open", "close"]].max(axis=1) > ce).any()):
        state = "inside, a body past its midpoint — weakening"
    else:
        state = "reached and respected so far (no body past its midpoint)"
    if pending and state == "not reached yet":
        state = "reached by the current candle"
    return {"fvg": (round(float(g.bottom), 2), round(float(g.top), 2)), "ce": round(float(ce), 2),
            "liquidity": round(float(liq), 2) if liq is not None else None, "state": state + pending}


def ob_reads(bars: pd.DataFrame, tf: str, as_of: pd.Timestamp, last: int = 3, fine: pd.DataFrame | None = None) -> list[dict]:
    """The newest ``last`` OBs (single candle, close through its open) known by ``as_of``, each with event / place / draw.
    An OB without a transitional event is still listed (``event`` None) so the read can say it is "just a candle"."""
    b = bars[(bars["close_ts"] if "close_ts" in bars else bars.index) <= as_of]
    out = []
    for ob in order_blocks(b, tf, confirm="open", single=True)[-last:]:
        top, bot = ob.meta["body"]
        out.append({"tf": tf, "direction": ob.direction, "candle": ob.origin_ts, "known": ob.ts,
                    "body": (round(bot, 2), round(top, 2)), "mt": round((top + bot) / 2, 2),
                    "event": _event(b, ob, tf), "place": _place(b, ob, tf), "draw": _draw(b, ob, tf, as_of, fine)})
    return out
