"""Live morning sheet for the recipe (paper trading beside the forward log, research/forward-recipe-v1.md).

Polls the free Dukascopy feed (about a minute behind), runs the frozen recipe on the bars up to now with the same
``run_day`` the backtests use, and writes ``out/live/today.json`` for ``viewer/live.html``:

    uv run python research/scripts/live_recipe.py                 # refresh every 60 s until 16:05 New York
    uv run python research/scripts/liqmap_server.py --port 8776 --data out/live --page viewer/live.html \
        --answers reports/reviews/live.jsonl                       # → http://127.0.0.1:8776

    ... live_recipe.py --once                                      # one refresh
    ... live_recipe.py --replay 2026-10-14 --at 10:20              # a past day cut at a time (to try the page)

Per index: the day's conditions (volatility state, scheduled high-impact news, weekday, session → is it a "recipe
day"), the session levels, candles, and every setup of the recipe with its gate trace and, once one forms, the plan
(entry / stop / TP1). Sharif's marks go to ``reports/reviews/live.jsonl`` through the server; this script never
writes there. Prices are the CFD's (not the futures': see CLAUDE.md "Feed basis").
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time as _time
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

NY = "America/New_York"
ASSETS = ("US100", "US500", "US30")
VARIANT = "recipe4: recipe3, mornings only"
OUT = Path("out/live")
AGG = {"open": "first", "high": "max", "low": "min", "close": "last"}


def fetch_recent(asset: str, day: date) -> pd.DataFrame:
    """The feed's 1m bars around ``day`` (NY-indexed); empty on any failure (the next poll tries again)."""
    from ict_engine.data import dukascopy as dk
    from ict_engine.data.instruments import get
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ["npx", "-y", dk.DUKASCOPY_NODE, "-i", get(asset).dukascopy_id, "-from", str(day - timedelta(days=4)),
               "-to", str(day + timedelta(days=2)), "-t", "m1", "-p", "bid", "-v", "true", "-f", "csv", "-r", "3", "-dir", tmp, "-s"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return pd.DataFrame()
        files = list(Path(tmp).glob("*.csv"))
        if res.returncode != 0 or not files:
            return pd.DataFrame()
        df = dk.parse_csv(files[0])
    df.index = df.index.tz_convert(NY)
    df.index.name = "ts"
    return df


def merge(base: pd.DataFrame, fresh: pd.DataFrame) -> pd.DataFrame:
    if fresh.empty:
        return base
    df = pd.concat([base, fresh[base.columns.intersection(fresh.columns)]])
    return df[~df.index.duplicated(keep="last")].sort_index()


def candles(bars: pd.DataFrame, rule: str, since: pd.Timestamp) -> list[dict]:
    """Candles for the chart; time = New York wall clock written as a UTC epoch (the chart shows NY time)."""
    b = bars[bars.index >= since][list(AGG)].resample(rule, label="left", closed="left").agg(AGG).dropna()
    t = (b.index.tz_localize(None) - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)
    return [{"time": int(x), "open": round(float(o), 2), "high": round(float(h), 2), "low": round(float(lo), 2), "close": round(float(c), 2)}
            for x, o, h, lo, c in zip(t, b.open, b.high, b.low, b.close)]


def htf_candles(h1: pd.DataFrame, tf: str) -> list[dict]:
    """4h / daily / weekly candles on the futures clock from 1h bars (NY index): 4h candles start at 18:00, 22:00,
    02:00 …; a day runs 18:00 → 17:00 and carries the date it closes on; a week is Sunday 18:00 → Friday; a month ("1M") is the calendar month of those dates.
    time = New York wall clock as a UTC epoch (midnight of the date for days; the Monday for weeks; the 1st for months)."""
    b = h1[list(AGG)]
    if tf == "4h":
        g = b.set_axis(b.index.tz_localize(None)).resample("4h", offset="2h", label="left", closed="left").agg(AGG).dropna()
        t = g.index                                              # on the wall clock, so the bins stay at 18:00 across DST changes
    else:
        d = (b.index + pd.Timedelta(hours=6)).tz_localize(None).normalize()          # 18:00 belongs to the next date
        key = d if tf == "1D" else d - pd.to_timedelta(d.dayofweek, unit="D") if tf == "1W" else d - pd.to_timedelta(d.day - 1, unit="D")
        g = b.groupby(key).agg(AGG)
        t = g.index
    sec = (t - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)
    return [{"time": int(x), "open": round(float(o), 2), "high": round(float(h), 2), "low": round(float(lo), 2), "close": round(float(c), 2)}
            for x, o, h, lo, c in zip(sec, g.open, g.high, g.low, g.close)]


_LONG: dict = {}


def long_h1(asset: str, day: date, days: int = 2600) -> pd.DataFrame:
    """1h bars of the last ~7 years from the local cache, loaded once per index and day (for the 4h / D / W charts)."""
    if (asset, day) not in _LONG:
        from ict_engine.data import dukascopy
        try:
            b = dukascopy.load(asset, day - timedelta(days=days), day)
            _LONG[(asset, day)] = b[list(AGG)].resample("1h", label="left", closed="left").agg(AGG).dropna()
        except Exception:
            _LONG[(asset, day)] = pd.DataFrame(columns=list(AGG))
    return _LONG[(asset, day)]


def conditions(asset: str, bars: pd.DataFrame, day: date) -> dict:
    """What is known before the day starts: regime, scheduled news, weekday, session. ``recipe_day`` = the forward
    test's candidate 2 (high volatility or a high-impact release)."""
    from ict_engine.concepts.liquidity_map import _daily
    from ict_engine.concepts.regime import daily_regimes
    from ict_engine.news import calendar
    from ict_engine.news.holidays import session_note
    d = _daily(bars)
    r = daily_regimes(d)
    r["day"] = pd.DatetimeIndex(d.index).strftime("%Y-%m-%d")
    row = r[r.day == str(day)]
    exact = len(row) > 0
    row = (row if exact else r).iloc[-1]
    cal = calendar.load()
    today = cal[cal.ts.dt.strftime("%Y-%m-%d") == str(day)].sort_values("ts")
    news = [{"time": t.strftime("%H:%M"), "name": n, "impact": i} for t, n, i in zip(today.ts, today.name, today.impact)]
    high_news = any(n["impact"] == "high" for n in news)
    return {"vol": row.vol, "state": row.state, "backdrop": row.backdrop, "regime_is_todays": exact, "news": news,
            "news_day": high_news, "weekday": day.strftime("%A"), "monday": day.weekday() == 0,
            "session": session_note(day) or "normal", "recipe_day": bool(row.vol == "high" or high_news)}


def _ev(e) -> dict:
    g = lambda k: getattr(e, k, None)  # noqa: E731
    f = lambda v: None if v is None else round(float(v), 2)  # noqa: E731
    ts = g("ts")
    return {"kind": g("kind"), "tf": g("tf"), "top": f(g("top")), "bottom": f(g("bottom")), "at": ts.strftime("%a %H:%M") if ts is not None else None}


def state_of(exit_reason, filled: bool, now: pd.Timestamp, close: pd.Timestamp, expires: pd.Timestamp) -> str:
    """The plan's state in words. Bars end at "now", so a simulator time exit before the close = still open."""
    if not filled:
        if exit_reason is None:
            return "not filled" if now >= expires else "waiting for the fill"
        return {"missed": "missed (TP1 traded first)", "cancelled": "cancelled (stop level traded first)",
                "not_filled": "not filled"}.get(exit_reason, exit_reason)
    if exit_reason == "time_exit" and now < close:
        return "open"
    return {"tp1": "TP1 hit", "stop": "stopped", "time_exit": "closed at the session end"}.get(exit_reason, exit_reason or "open")


def setups(asset: str, bars: pd.DataFrame, day: date, now: pd.Timestamp) -> list[dict]:
    from ict_engine.eval.variants import PD_RETURN_VARIANTS
    from ict_engine.sim.run import run_day
    close = pd.Timestamp(datetime.combine(day, time(16)), tz=NY)
    out = []
    for s in run_day(bars, day, asset, PD_RETURN_VARIANTS[VARIANT]):
        row = {"id": f"{day}-{asset}-{s.side}-{s.decided_at:%H%M}", "side": s.side, "decided": s.decided_at.strftime("%H:%M"),
               "window": s.tags.get("window"), "ok": s.plan is not None,
               "gates": [{"name": g.name, "passed": bool(g.passed), "detail": g.detail} for g in s.gates],
               "evidence": {k: _ev(v) for k, v in s.evidence.items()}, "plan": None, "result": None}
        p = s.would_plan
        if p is not None:
            row["plan"] = {"entry": round(p.entry, 2), "stop": round(p.stop, 2), "tp1": round(p.tp1, 2), "tp1_name": p.tp1_name,
                           "final": round(p.final_target, 2), "final_name": p.final_name, "risk": round(p.risk, 2),
                           "rr": round(abs(p.tp1 - p.entry) / p.risk, 2) if p.risk else None,
                           "placed": p.placed_at.strftime("%H:%M"), "expires": p.expires_at.strftime("%H:%M")}
        r = s.result
        if s.plan is not None and r is not None:
            state = state_of(r.exit_reason, r.filled_at is not None, now, close, p.expires_at)
            row["result"] = {"state": state, "filled": r.filled_at.strftime("%H:%M") if r.filled_at is not None else None,
                             "r": None if r.r is None or pd.isna(r.r) else round(float(r.r), 2)}
        out.append(row)
    return out


def structure_breaks(bars: pd.DataFrame, now: pd.Timestamp, days: int = 4) -> list[dict]:
    """The 1h structure breaks of the last few days with their range, OTE levels and where each stands (Sharif's
    BOS → OTE notes, 2026-11-16; rule in bos_ote_study.py). For him to mark which breaks count."""
    import bos_ote_study as bo
    recent = bars[bars.index >= now - pd.Timedelta(days=days + 12)]
    evs = [e for e in bo.breaks(recent) if e["ts"] >= now - pd.Timedelta(days=days)]
    idx = recent.index.tz_convert("UTC").as_unit("ns").asi8
    o, h, lo, c = (recent[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    out = []
    for n, e in enumerate(evs):
        nxt = next((x["ts"] for x in evs[n + 1:] if x["short"] != e["short"]), None)
        st = bo.live_state(idx, o, h, lo, c, e, cancel_at=nxt.tz_convert("UTC").value if nxt is not None else None)
        f = st.get("filled_at")
        out.append({"id": f"bos-{e['ts']:%Y%m%d-%H%M}-{'short' if e['short'] else 'long'}", "side": "short" if e["short"] else "long",
                    "at": e["ts"].strftime("%a %d %H:%M"), "kind": e["kind"], "displacement": e["displacement"],
                    "far": round(st["far"], 2), "near": round(st["near"], 2), "entry": round(st["entry"], 2), "ote_hi": round(st["ote_hi"], 2),
                    "eq": round(st["eq"], 2), "state": st["state"], "filled": f.strftime("%a %H:%M") if f is not None else None,
                    "r": None if st.get("r") is None else round(float(st["r"]), 2)})
    return out[::-1]                                             # newest first


def adr_of(bars: pd.DataFrame, now: pd.Timestamp, days: int = 20) -> float | None:
    d = bars[bars.index < now.normalize()].resample("1D").agg({"high": "max", "low": "min"}).dropna()
    r = (d.high - d.low).tail(days)
    return float(r.mean()) if len(r) >= 5 else None


def strength(bars: pd.DataFrame, now: pd.Timestamp, adr: float) -> dict:
    """Where the index stands against its own recent prices (for comparing the three): the move since the 18:00
    session open in ADR, and the place of the last price in the previous day's range (0% = its low, 100% = its high)."""
    last = float(bars.close.iloc[-1])
    start = (now.normalize() - pd.Timedelta(days=1) if now.hour < 18 else now.normalize()) + pd.Timedelta(hours=18)
    ses = bars[bars.index >= start]
    if ses.empty or (ses.index[0] - start) > pd.Timedelta(hours=2):       # Monday before 18:00: the session began Sunday
        ses = bars[bars.index >= bars.index[-1] - pd.Timedelta(hours=20)]
    prev_day = bars[bars.index < ses.index[0]]
    prev = prev_day[prev_day.index >= prev_day.index[-1].normalize()]
    hi, lo = float(prev.high.max()), float(prev.low.min())
    return {"session_move_adr": round((last - float(ses.open.iloc[0])) / adr, 2),
            "prev_range_pos": round(100 * (last - lo) / (hi - lo)) if hi > lo else None,
            "session_range_adr": round(float(ses.high.max() - ses.low.min()) / adr, 2)}


def gap_state(bars: pd.DataFrame, now: pd.Timestamp, adr: float) -> dict | None:
    """The session's opening gap as Sharif reads it (2026-11-16): interesting while open; a target once the equal lows
    (highs) on the other side are swept and price pushes back. Rule pieces from ndog_study / ndog_eql."""
    import ndog_eql as ne
    import ndog_study as nd
    recent = bars[bars.index >= now - pd.Timedelta(days=6)]
    t = recent.index
    mins = (t.hour * 60 + t.minute).to_numpy()
    since_prev = np.r_[0, np.diff(t.tz_convert("UTC").as_unit("ns").asi8)] / 6e10
    opens = np.flatnonzero((mins >= 1080) & (mins <= 1110) & (since_prev >= 45))   # the running session counts from its first bar
    if not len(opens):
        return None
    i = int(opens[-1])
    s = {"open_ts": t[i], "open": float(recent.open.iloc[i]), "prev_close": float(recent.close.iloc[i - 1]),
         "weekend": bool(since_prev[i] > 30 * 60)}
    gap = s["prev_close"] - s["open"]
    if gap == 0:
        return None
    long = gap > 0
    sg = 1.0 if long else -1.0
    f = recent[recent.index >= s["open_ts"]][list(AGG)].resample("15min", label="left", closed="left").agg(AGG).dropna()
    f = f[f.index + pd.Timedelta(minutes=15) <= now + pd.Timedelta(minutes=1)]                 # finished candles only
    if len(f) < 2:
        return None
    C = f.close.to_numpy() * sg
    H, L = (f.high.to_numpy(), f.low.to_numpy()) if long else (-f.low.to_numpy(), -f.high.to_numpy())
    target = s["prev_close"] * sg
    reach = (H.max() - s["open"] * sg) / abs(gap)
    out = {"side": "buy closes it (gap above)" if long else "sell closes it (gap below)", "from": round(s["open"], 2), "to": round(s["prev_close"], 2),
           "size_adr": round(abs(gap) / adr, 2), "weekend": bool(s["weekend"]), "reached_pct": round(100 * min(max(reach, 0), 1)),
           "closed": bool(H.max() >= target), "pool": None, "sweep": None, "push": None}
    n = len(C)
    lows = [i for i in range(0, n - 2) if (i == 0 or L[i] < L[max(0, i - 2):i].min()) and L[i] < L[i + 1:i + 3].min()]
    sw = ne.sweep_of(f.open.to_numpy() * sg, H, L, C, target, adr, True)       # equal lows only: that is his condition
    k = sw["k"] if sw else n
    untaken = [L[i] for i in lows if i < k - 2 and L[i] <= L[i + 1:k].min()] if k > 2 else []
    if untaken:
        base = sw["level"] if sw else min(untaken)
        near = [v for v in untaken if abs(v - base) <= ne.EQ_TOL * adr]
        out["pool"] = {"level": round(base * sg, 2), "count": len(near), "spread_adr": round((max(near) - min(near)) / adr, 3) if near else 0.0,
                       "equal": len(near) >= 2}
    if sw:
        out["sweep"] = {"at": f.index[k].strftime("%a %H:%M"), "depth_adr": round((sw["level"] - float(L[k:].min())) / adr, 2)}
        rng = H - L
        for m in range(k, n):                                                # the first displacement closing back above the pool
            base = float(np.median(rng[max(0, k - 20):k])) if k >= 4 else 0.0
            if C[m] > sw["top"] and base > 0 and rng[m] >= 1.5 * base and C[m] >= L[m] + 0.6 * rng[m]:
                out["push"] = {"at": f.index[m].strftime("%H:%M"), "range_adr": round(float(rng[m]) / adr, 2),
                               "close_pct": round(100 * float(C[m] - L[m]) / float(rng[m]))}
                break
    out["state"] = ("closed" if out["closed"] else "equal lows / highs swept and price pushed back: the gap is a target" if out["push"] else
                    "equal lows / highs swept, no push back yet" if out["sweep"] else "open: interesting, not a trade yet")
    return out


def _epoch(ts: pd.Timestamp) -> int:
    """New York wall clock written as a UTC epoch, as the chart's candles are."""
    return int((ts.tz_convert(NY).tz_localize(None) - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1))


def engulfed_blocks(df: pd.DataFrame, tf: str) -> list:
    """Order blocks as Sharif taught them (2026-11-16, Sunday 15 Nov open): the last opposite candle is an order block
    only when the VERY NEXT candle engulfs it — one move strong enough to close beyond the candle's open. Two candles
    doing it together do not count on that timeframe (the 1h 18:00 candle was invalid; the 15m 19:45 one valid).
    The block = that candle's body; known when the engulfing candle closes. ``meta['beyond_wick']``: the close is
    also beyond the candle's wick."""
    from ict_engine.concepts.events import Event
    o, h, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    cts = (df["close_ts"] if "close_ts" in df else df.index.to_series()).to_numpy()
    out = []
    for i in range(len(df) - 1):
        if c[i] > o[i] and c[i + 1] < o[i]:                       # an up candle, then one candle closing under its open
            out.append(Event("ob", tf, "bear", pd.Timestamp(cts[i + 1]), df.index[i], float(c[i]), float(o[i]),
                             {"beyond_wick": bool(c[i + 1] < lo[i])}))
        elif c[i] < o[i] and c[i + 1] > o[i]:
            out.append(Event("ob", tf, "bull", pd.Timestamp(cts[i + 1]), df.index[i], float(o[i]), float(c[i]),
                             {"beyond_wick": bool(c[i + 1] > h[i])}))
    return out


def entry_areas(bars: pd.DataFrame, now: pd.Timestamp, adr: float, breaks: list[dict] | None = None,
                days: int = 6, reach: float = 1.0, per_side: int = 4) -> list[dict]:
    """The 1h entry areas near price, all looked for the same way (Sharif 2026-11-16: a breaker is an entry area like
    an OTE or an order block; the idea and the target come first, the area is only where to get in).
      breaker      body of the last candle before the leg, after a close back through it (``merge`` + ``block="body"``);
                   ``body_pct`` = the body's share of that candle (he rejects "more wick than body")
      order block  ``engulfed_blocks`` on 1h and 15m (15m: the last two days): the last opposite candle, engulfed by
                   the very next candle; its body
      FVG  unfilled and not closed through; OTE  62–79% of a break still waiting
    Only areas known by ``now`` (closed 1h candles), still valid, within ``reach`` ADR of price; nearest ``per_side``
    above and below plus any that price is in. A buy area is support (bull), a sell area resistance (bear)."""
    from ict_engine.concepts.bars import resample
    from ict_engine.concepts.events import breaker_blocks, fvgs, gap_lifecycle
    recent = bars[(bars.index > now - pd.Timedelta(days=days + 4)) & (bars.index <= now)]
    h1 = resample(recent[list(AGG)], "1h")
    h1 = h1[h1.index + pd.Timedelta(hours=1) <= now + pd.Timedelta(minutes=1)]       # closed candles only
    last = float(recent.close.iloc[-1])
    evs = [(e, "breaker") for e in breaker_blocks(h1, "1h", merge=True, block="body") if e.kind == "breaker"]
    m15 = resample(recent[recent.index > now - pd.Timedelta(days=2)][list(AGG)], "15m")
    m15 = m15[m15.index + pd.Timedelta(minutes=15) <= now + pd.Timedelta(minutes=1)]
    evs += [(e, "order block") for e in engulfed_blocks(h1, "1h") + engulfed_blocks(m15, "15m")]
    evs += [(e, "FVG") for e in fvgs(h1, "1h")]
    out = []
    for e, name in evs:
        if e.ts > now or e.ts < now - pd.Timedelta(days=days) or e.top <= e.bottom:
            continue
        st = gap_lifecycle(e, recent, until=now)                 # touched / filled: on the 1m path
        own = gap_lifecycle(e, m15 if e.tf == "15m" else h1)     # still valid: judged on closed candles of its own timeframe
        if own.retired is not None or own.inverted is not None or (name == "FVG" and st.filled is not None):
            continue
        item = {"kind": name, "tf": e.tf, "side": "buy" if e.direction == "bull" else "sell", "top": round(e.top, 2),
                "bottom": round(e.bottom, 2), "t0": _epoch(e.origin_ts), "from": e.origin_ts.strftime("%a %d %H:%M"),
                "known": e.ts.strftime("%a %d %H:%M"), "touched": st.touched is not None}
        src = m15 if e.tf == "15m" else h1
        if name == "order block":
            item["beyond_wick"] = bool(e.meta.get("beyond_wick"))
        if name in ("breaker", "order block") and e.origin_ts in src.index:
            rng = float(src.high[e.origin_ts] - src.low[e.origin_ts])
            item["body_pct"] = round(100 * (e.top - e.bottom) / rng) if rng > 0 else None
        out.append(item)
    for b in breaks or []:
        if str(b.get("state", "")).startswith("waiting"):
            top, bottom = max(b["entry"], b["ote_hi"]), min(b["entry"], b["ote_hi"])
            ts = pd.Timestamp(datetime.strptime(b["id"][4:17], "%Y%m%d-%H%M"), tz=NY)
            out.append({"kind": "OTE", "tf": "1h", "side": "sell" if b["side"] == "short" else "buy", "top": top, "bottom": bottom,
                        "t0": _epoch(ts), "from": b["at"], "known": b["at"], "touched": False})
    for a in out:
        a["inside"] = a["bottom"] <= last <= a["top"]
        a["dist_adr"] = 0.0 if a["inside"] else round(min(abs(last - a["top"]), abs(last - a["bottom"])) / adr, 2)
        a["where"] = "price is in it" if a["inside"] else "above" if a["bottom"] > last else "below"
    # an entry area is on the retrace side: a buy area under (or at) price, a sell area over (or at) it
    out = [a for a in out if a["dist_adr"] <= reach and (a["inside"] or a["where"] == ("below" if a["side"] == "buy" else "above"))]
    keep = [a for a in out if a["inside"]]
    for w in ("above", "below"):
        keep += sorted((a for a in out if a["where"] == w), key=lambda a: a["dist_adr"])[:per_side]
    return sorted(keep, key=lambda a: -a["top"])


def hunting(now: pd.Timestamp) -> bool:
    """Sharif 2026-11-16: areas are only pointed out from an hour before London (01:00 New York) through the New York
    session (to 16:00), Monday to Friday. Outside that the chart stays clean (never the Asian session)."""
    return now.weekday() < 5 and time(1, 0) <= now.time() < time(16, 0)


def build(bars_by_asset: dict[str, pd.DataFrame], day: date, now: pd.Timestamp, mode: str) -> dict:
    from ict_engine.concepts.context import build_context
    doc = {"day": str(day), "now": now.strftime("%a %Y-%m-%d %H:%M"), "mode": mode, "variant": VARIANT, "hunting": hunting(now), "assets": {}}
    for a, full in bars_by_asset.items():
        bars = full[full.index <= now]
        item = {"last_bar": bars.index[-1].strftime("%a %H:%M"), "last": round(float(bars.close.iloc[-1]), 2)}
        try:
            item["conditions"] = conditions(a, bars, day)
            ctx = build_context(bars, day)
            item["levels"] = {k: round(float(v), 2) for k, v in ctx.levels.items()}
            item["setups"] = setups(a, bars, day, now)
            item["breaks"] = structure_breaks(bars, now)
            adr = adr_of(bars, now)
            if adr:
                item["adr"] = round(adr, 1)
                item["strength"] = strength(bars, now, adr)
                item["gap"] = gap_state(bars, now, adr)
                item["areas"] = entry_areas(bars, now, adr, item["breaks"]) if doc["hunting"] else []
                for b in item["breaks"]:
                    rng = abs(b["far"] - b["near"])
                    b["range_adr"] = round(rng / adr, 2)
                    b["retrace_pct"] = round(100 * abs(item["last"] - b["near"]) / rng) if rng else None
        except Exception as e:                                   # one index failing must not blank the page
            item["error"] = f"{type(e).__name__}: {e}"
            item.setdefault("setups", [])
        midnight = pd.Timestamp(day, tz=NY)
        item["candles"] = {"1m": candles(bars, "1min", midnight - pd.Timedelta(hours=6)),      # since the 18:00 open
                           "5m": candles(bars, "5min", midnight - pd.Timedelta(days=1)),
                           "15m": candles(bars, "15min", midnight - pd.Timedelta(days=6)),
                           "1h": candles(bars, "1h", midnight - pd.Timedelta(days=25))}
        try:                                                     # higher timeframes for the bias: cache history + the live bars
            live_h1 = bars[list(AGG)].resample("1h", label="left", closed="left").agg(AGG).dropna()
            old = long_h1(a, day)
            h1 = pd.concat([old[old.index < live_h1.index[0]], live_h1])
            h1 = h1[h1.index <= now]
            item["candles"].update({"4h": htf_candles(h1[h1.index >= now - pd.Timedelta(days=120)], "4h"),
                                    "1D": htf_candles(h1[h1.index >= now - pd.Timedelta(days=500)], "1D"),
                                    "1W": htf_candles(h1[h1.index >= now - pd.Timedelta(days=1100)], "1W"), "1M": htf_candles(h1, "1M")})
        except Exception as e:
            item["htf_error"] = f"{type(e).__name__}: {e}"
        doc["assets"][a] = item
    return doc


def write(doc: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "today.json.tmp"
    tmp.write_text(json.dumps(doc, default=str))
    tmp.replace(OUT / "today.json")                              # atomic: the page never reads half a file
    (OUT / "index.json").write_text(json.dumps({"ids": ["today"]}))


def main():
    from ict_engine.eval.backtest import load_range
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60, help="seconds between refreshes")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--replay", type=date.fromisoformat, help="a past day from the cache (no fetch)")
    ap.add_argument("--at", default="10:30", help="with --replay: the New York time the bars are cut at")
    ap.add_argument("--assets", nargs="+", default=list(ASSETS))
    a = ap.parse_args()
    if a.replay:
        now = pd.Timestamp(f"{a.replay} {a.at}", tz=NY)
        bars = {x: load_range(x, a.replay, a.replay) for x in a.assets}
        write(build(bars, a.replay, now, "replay"))
        print(f"replay {now:%Y-%m-%d %H:%M} written to {OUT / 'today.json'}")
        return
    day = pd.Timestamp.now(tz=NY).date()
    base = {x: load_range(x, day, day) for x in a.assets}
    while True:
        now = pd.Timestamp.now(tz=NY)
        for x in a.assets:
            base[x] = merge(base[x], fetch_recent(x, day))
        doc = build(base, day, now, "live")
        write(doc)
        n = sum(1 for v in doc["assets"].values() for s in v["setups"] if s["ok"])
        print(f"{now:%H:%M:%S} refreshed · last bars {[v['last_bar'] for v in doc['assets'].values()]} · plans {n}", flush=True)
        if a.once or now.time() >= time(16, 5) or now.date() != day:
            break
        _time.sleep(a.interval)


if __name__ == "__main__":
    main()
