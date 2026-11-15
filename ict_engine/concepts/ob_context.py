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
        # the run traded THROUGH it: above the candle(s)' open (bearish OB = up-close: open = body bottom), up to the
        # extreme — a close above the old high still ran its buystops (Bible p.16 step 1)
        if gone or not ((body_bot < x.price <= ext) if bear else (ext <= x.price < body_top)):
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
    """Premium / discount of the OB body in the DEALING RANGE it formed (ICT Bible pp.27–29): a range is set when
    sellstops are run to make a new low and then buystops are run to make a new high (or the mirror); premium above its
    50 %. Bearish OB: the high = the OB move's high (it ran the buystops); the low = the latest swing low before the OB
    candle that itself ran an earlier swing low's sellstops. Bullish mirrors. Falls back to the ICT look-back window
    when no such swing exists; ``lookback`` keeps the window's reading."""
    i = int((bars["close_ts"] <= ob.ts).to_numpy().nonzero()[0][-1]) if "close_ts" in bars else bars.index.get_loc(ob.ts)
    a = bars.index.get_loc(ob.origin_ts)
    bear = ob.direction == "bear"
    w = bars.iloc[max(0, i + 1 - LOOKBACK.get(tf, 20)):i + 1]
    top, bot = ob.meta["body"]
    mid = (top + bot) / 2

    def frac(lo, hi):
        return (mid - lo) / (hi - lo) if hi > lo else 0.5
    lb = (float(w.low.min()), float(w.high.max()))
    ext = float(ob.top if bear else ob.bottom)                 # the OB candle(s)' high (low): the run end
    kind = "swing_low" if bear else "swing_high"
    sw = sorted((e for e in swings(bars.iloc[:a + 1], tf) if e.kind == kind and e.ts <= bars.index[a]),
                key=lambda e: e.origin_ts)
    ran = [e for k, e in enumerate(sw[1:], 1) if ((e.bottom < sw[k - 1].bottom) if bear else (e.top > sw[k - 1].top))
           and ((e.bottom < ext) if bear else (e.top > ext))]
    if ran:
        e = ran[-1]
        lo, hi = (float(e.bottom), ext) if bear else (ext, float(e.top))
        basis = "dealing range"
    else:
        (lo, hi), basis = lb, "look-back"
    f = frac(lo, hi)
    return {"range": (round(lo, 2), round(hi, 2)), "basis": basis, "fraction": round(f, 2),
            "zone": "premium" if f >= 0.5 else "discount", "fits": (f >= 0.5) == bear,
            "lookback": {"range": (round(lb[0], 2), round(lb[1], 2)), "fraction": round(frac(*lb), 2)}}


def _htf_level(ob, htf: list | None) -> dict | None:
    """Bible p.16 step 2: the OB candle(s) came INTO a higher-timeframe resistance (bearish; support for bullish) —
    a HTF bearish FVG still open, a HTF bullish FVG closed through (now an IFVG resisting), or an old HTF swing high,
    that the OB candle(s)' range reached. Only HTF bars closed by the OB candle's own start are used."""
    if not htf:
        return None
    bear = ob.direction == "bear"
    for frame, t in htf:
        ct = frame["close_ts"] if "close_ts" in frame else pd.Series(frame.index, index=frame.index)
        k = frame[ct <= ob.origin_ts]
        if len(k) < 3:
            continue
        kc = k.close
        for g in reversed(fvgs(k, t)):
            after = kc[kc.index > g.origin_ts].iloc[1:]
            if g.direction == ("bear" if bear else "bull"):
                closed = (after > g.top).any() if bear else (after < g.bottom).any()
                name = f"{t} {'bearish' if bear else 'bullish'} FVG"
            else:
                inv = (after < g.bottom) if bear else (after > g.top)
                if not inv.any():
                    continue
                back = after[after.index > inv.idxmax()]
                closed = (back > g.top).any() if bear else (back < g.bottom).any()
                name = f"{t} {'bearish' if bear else 'bullish'} IFVG"
            if not closed and ob.bottom <= g.top and ob.top >= g.bottom:
                return {"what": name, "zone": (round(float(g.bottom), 2), round(float(g.top), 2))}
        for e in reversed(swings(k, t)):
            if e.kind == ("swing_high" if bear else "swing_low"):
                lvl = e.top if bear else e.bottom
                if ob.bottom <= lvl <= ob.top:
                    return {"what": f"{t} old {'high' if bear else 'low'}", "zone": (round(float(lvl), 2),) * 2}
    return None


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


def _state(bars: pd.DataFrame, ob, as_of: pd.Timestamp, fine: pd.DataFrame | None = None) -> str:
    """The OB's own state since it was confirmed (bearish; bullish mirrors), on closes of its timeframe up to ``as_of``:
    a close through its mean threshold = failed (ruling §11); price traded right through the body = gone; else holding
    (``fine`` adds the unfinished current candle's wick)."""
    bear = ob.direction == "bear"
    top, bot = ob.meta["body"]
    mt = (top + bot) / 2
    ct = bars["close_ts"] if "close_ts" in bars else pd.Series(bars.index, index=bars.index)
    since = bars[(ct > ob.ts) & (ct <= as_of)]
    wick = since
    if fine is not None:
        last = ct[ct <= as_of].max()
        wick = pd.concat([since[["high", "low"]], fine[(fine.index > last) & (fine.index < as_of)][["high", "low"]]])
    failed = (since.close > mt).any() if bear else (since.close < mt).any()
    gone = (wick.high > top).any() if bear else (wick.low < bot).any()
    if failed and gone:
        return "failed: closed through its MT, then traded through the body"
    if failed:
        return "failed: a close through its MT"
    if gone:
        return "body traded through (no close past MT)"
    return "holding"


def _validation(bars: pd.DataFrame, ob, as_of: pd.Timestamp) -> str:
    """How far the OB has been validated by ``as_of`` (bearish; bullish mirrors), ruling §23: its open crossed = the
    change in the state of delivery (ICT 2023, when the OB exists at all); then its low traded through (ICT Core
    Content M4: "trades through" — a wick counts); then a close below its low (ICT Bible p.16, the strictest)."""
    bear = ob.direction == "bear"
    lo, hi = ob.bottom, ob.top
    ct = bars["close_ts"] if "close_ts" in bars else pd.Series(bars.index, index=bars.index)
    a = bars.index.get_loc(ob.origin_ts)
    after = bars.iloc[a + 1:][(ct.iloc[a + 1:] <= as_of).to_numpy()]
    if ((after.close < lo) if bear else (after.close > hi)).any():
        return "closed beyond its " + ("low" if bear else "high")
    if ((after.low < lo) if bear else (after.high > hi)).any():
        return "traded through its " + ("low" if bear else "high")
    return "open crossed only"


STRENGTH = {"body_range": 0.4, "body_mean": 0.75, "push_mean": 1.5, "n": 14}


def _strength(bars: pd.DataFrame, ob, rules: dict = STRENGTH) -> dict:
    """Sharif (2026-11-16): the OB is the ONE candle just before the aggressive push, judged by its BODY — "a weak
    body cannot be a solid OB". Body strong = body ≥ ``body_range`` × its own range and ≥ ``body_mean`` × the mean
    body of the ``n`` candles before it; the push = the very next candle, closing the other way with a body ≥
    ``push_mean`` × that mean. Thresholds fitted to his two cases (US100 Sep 2026 monthly: 0.48 / 0.91, push 1.88;
    gold 9 Nov 2026 daily: 0.80 / 1.50, push 2.11) — the US100 Jul 2026 candle fails on the push (0.92)."""
    a = bars.index.get_loc(ob.origin_ts)
    body = (bars.close - bars.open).abs()
    rng = (bars.high - bars.low)
    prior = body.iloc[max(0, a - rules["n"]):a]
    mb = float(prior.mean()) if len(prior) else float(body.iloc[a])
    br = float(body.iloc[a] / rng.iloc[a]) if rng.iloc[a] > 0 else 0.0
    bm = float(body.iloc[a] / mb) if mb > 0 else 0.0
    push = None
    if a + 1 < len(bars):
        nxt = bars.iloc[a + 1]
        right = (nxt.close < nxt.open) if ob.direction == "bear" else (nxt.close > nxt.open)
        push = float(abs(nxt.close - nxt.open) / mb) if right and mb > 0 else 0.0
    strong = br >= rules["body_range"] and bm >= rules["body_mean"]
    pushed = push is not None and push >= rules["push_mean"]
    return {"body_range": round(br, 2), "body_mean": round(bm, 2), "push_mean": None if push is None else round(push, 2),
            "strong_body": strong, "aggressive_push": pushed, "ok": strong and pushed}


def ob_reads(bars: pd.DataFrame, tf: str, as_of: pd.Timestamp, last: int = 3, fine: pd.DataFrame | None = None,
             htf: list | None = None) -> list[dict]:
    """The newest ``last`` OBs (single candle, close through its open) known by ``as_of``, each with event / place / draw.
    An OB without a transitional event is still listed (``event`` None) so the read can say it is "just a candle"."""
    b = bars[(bars["close_ts"] if "close_ts" in bars else bars.index) <= as_of]
    out = []
    for ob in order_blocks(b, tf, confirm="open", single=True)[-last:]:   # ICT 2023: open crossed (ruling §23)
        top, bot = ob.meta["body"]
        out.append({"tf": tf, "direction": ob.direction, "candle": ob.origin_ts, "known": ob.ts,
                    "body": (round(bot, 2), round(top, 2)), "mt": round((top + bot) / 2, 2),
                    "event": _event(b, ob, tf), "place": _place(b, ob, tf), "draw": _draw(b, ob, tf, as_of, fine, htf), "state": _state(b, ob, as_of, fine),
                    "displacement": bool(ob.meta.get("fvg")), "htf_level": _htf_level(ob, htf),
                    "validation": _validation(b, ob, as_of), "strength": _strength(b, ob)})
    return out
