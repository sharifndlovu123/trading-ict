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
    """Premium / discount of the OB body. The range is the dealing range the OB's move retraced into: for a bearish
    OB, the last swing high above the move's extreme (known before the OB candle) → the lowest low since it (Sharif's
    gold sell, 2026-11-09 daily OB: 0.44 of the 40-day window, premium of the 4,217 → 3,869 leg). With no such swing
    (a new high) it falls back to the ICT look-back window. Bullish mirrors. ``lookback`` keeps the window's reading."""
    i = int((bars["close_ts"] <= ob.ts).to_numpy().nonzero()[0][-1]) if "close_ts" in bars else bars.index.get_loc(ob.ts)
    a = bars.index.get_loc(ob.origin_ts)
    bear = ob.direction == "bear"
    w = bars.iloc[max(0, i + 1 - LOOKBACK.get(tf, 20)):i + 1]
    top, bot = ob.meta["body"]
    mid = (top + bot) / 2

    def frac(lo, hi):
        return (mid - lo) / (hi - lo) if hi > lo else 0.5
    lb = (float(w.low.min()), float(w.high.max()))
    move = bars.iloc[a:i + 1]
    ext = float(move.high.max() if bear else move.low.min())
    known_by = bars.index[a]
    sw = [e for e in swings(bars.iloc[:a + 1], tf) if e.ts <= known_by and
          e.kind == ("swing_high" if bear else "swing_low") and ((e.top > ext) if bear else (e.bottom < ext))]
    if sw:
        e = max(sw, key=lambda x: x.origin_ts)
        leg = bars.loc[e.origin_ts:bars.index[i]]
        lo, hi = (float(leg.low.min()), float(e.top)) if bear else (float(e.bottom), float(leg.high.max()))
        basis = "dealing range"
    else:
        (lo, hi), basis = lb, "look-back"
    f = frac(lo, hi)
    return {"range": (round(lo, 2), round(hi, 2)), "basis": basis, "fraction": round(f, 2),
            "zone": "premium" if f >= 0.5 else "discount", "fits": (f >= 0.5) == bear,
            "lookback": {"range": (round(lb[0], 2), round(lb[1], 2)), "fraction": round(frac(*lb), 2)}}


def _remaining(frame: pd.DataFrame, tf: str, bear: bool, ref: float, known_ts: pd.Timestamp) -> list:
    """Open FVGs on the retrace side of ``ref`` (below for a bearish OB) on bars closed by ``known_ts``; one price has
    already traded right through (wick beyond its far edge) is used up."""
    known = frame[frame["close_ts"] <= known_ts] if "close_ts" in frame else frame[frame.index <= known_ts]
    out = []
    for g in fvgs(known, tf):
        if g.direction != ("bull" if bear else "bear"):
            continue
        after = known[known.index > g.origin_ts].iloc[1:]
        filled = (after.low < g.bottom).any() if bear else (after.high > g.top).any()
        if not filled and ((g.top < ref) if bear else (g.bottom > ref)):
            out.append(g)
    return out


def _draw(bars: pd.DataFrame, ob, tf: str, as_of: pd.Timestamp, fine: pd.DataFrame | None = None,
          htf: list | None = None) -> dict | None:
    """The remaining FVG on the retrace side (below a bearish OB) still open when the OB was confirmed, the liquidity
    resting at its near edge, and what price has done in it since: closes of this timeframe up to ``as_of``, plus the
    unfinished current candle from ``fine`` (lower-timeframe bars) — its close is still pending.
    ``htf`` = [(bars, tf), …] highest first: the draw is the nearest gap on the highest of those timeframes that has
    one (Sharif's gold sell, daily OB → the monthly FVG); gaps on lower timeframes between price and it are
    ``on_way``. Without ``htf`` the OB's own timeframe is used."""
    bear = ob.direction == "bear"
    known = bars[bars["close_ts"] <= ob.ts] if "close_ts" in bars else bars[bars.index <= ob.ts]
    ref = float(known.close.iloc[-1])
    near = (lambda gs: max(gs, key=lambda x: x.top)) if bear else (lambda gs: min(gs, key=lambda x: x.bottom))
    frames = list(htf or []) + [(bars, tf)]
    found = [(t, near(gs)) for f, t in frames if (gs := _remaining(f, t, bear, ref, ob.ts))]
    if not found:
        return None
    gtf, g = found[0]
    on_way = [{"tf": t, "fvg": (round(float(x.bottom), 2), round(float(x.top), 2))} for t, x in found[1:]
              if ((x.bottom > g.top) if bear else (x.top < g.bottom))]
    lf = dict((t, f) for f, t in frames)[gtf]                 # liquidity from the gap's own timeframe
    lk = lf[lf["close_ts"] <= ob.ts] if "close_ts" in lf else lf[lf.index <= ob.ts]
    sw = swing_levels(e for e in swings(lk, gtf))
    edge = [x for x in sw if x.side == ("low" if bear else "high") and
            ((g.bottom <= x.price <= ref) if bear else (ref <= x.price <= g.top))]
    edge = [x for x in edge if not ((lk.loc[x.valid_from:].low < x.price).any() if bear
                                    else (lk.loc[x.valid_from:].high > x.price).any())]   # still resting (untaken)
    liq = (min if bear else max)(edge, key=lambda x: x.price).price if edge else None
    sframe = dict((t, f) for f, t in frames)[gtf]          # the gap is judged on its own timeframe's closes
    sct = sframe["close_ts"] if "close_ts" in sframe else pd.Series(sframe.index, index=sframe.index)
    since = sframe[(sct > ob.ts) & (sct <= as_of)]
    last_close = sct[sct <= as_of].iloc[-1] if (sct <= as_of).any() else ob.ts
    ce = (g.top + g.bottom) / 2
    pending = ""
    bct = bars["close_ts"] if "close_ts" in bars else pd.Series(bars.index, index=bars.index)
    closed = bars[(bct > last_close) & (bct <= as_of)] if gtf != tf else bars.iloc[:0]   # the higher candle so far
    parts = [closed] if len(closed) else []
    lower_close = bct[closed.index].max() if len(closed) else last_close
    if fine is not None:
        parts.append(fine[(fine.index > lower_close) & (fine.index < as_of)])
    cur = pd.concat([x[["open", "high", "low", "close"]] for x in parts]) if parts else pd.DataFrame()
    if len(cur):
        lo, hi = float(cur.low.min()), float(cur.high.max())
        into = (lo <= g.top) if bear else (hi >= g.bottom)
        if into:
            depth = ((g.top - lo) / (g.top - g.bottom)) if bear else ((hi - g.bottom) / (g.top - g.bottom))
            how = ("right through it (wick)" if depth > 1 else f"{depth:.0%} into it"
                   + (" — past its midpoint" if depth > 0.5 else ""))
            pending = (f"; the current {gtf} candle (close pending) reached {lo if bear else hi:.2f} = {how}, "
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
    return {"tf": gtf, "on_way": on_way, "fvg": (round(float(g.bottom), 2), round(float(g.top), 2)), "ce": round(float(ce), 2),
            "liquidity": round(float(liq), 2) if liq is not None else None, "state": state + pending}


def ob_reads(bars: pd.DataFrame, tf: str, as_of: pd.Timestamp, last: int = 3, fine: pd.DataFrame | None = None,
             htf: list | None = None) -> list[dict]:
    """The newest ``last`` OBs (single candle, close through its open) known by ``as_of``, each with event / place / draw.
    An OB without a transitional event is still listed (``event`` None) so the read can say it is "just a candle"."""
    b = bars[(bars["close_ts"] if "close_ts" in bars else bars.index) <= as_of]
    out = []
    for ob in order_blocks(b, tf, confirm="open", single=True)[-last:]:
        top, bot = ob.meta["body"]
        out.append({"tf": tf, "direction": ob.direction, "candle": ob.origin_ts, "known": ob.ts,
                    "body": (round(bot, 2), round(top, 2)), "mt": round((top + bot) / 2, 2),
                    "event": _event(b, ob, tf), "place": _place(b, ob, tf), "draw": _draw(b, ob, tf, as_of, fine, htf)})
    return out
