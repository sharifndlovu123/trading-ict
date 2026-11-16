"""Facts for a post-trade review (the trade-review skill reads this; the judgement is written by the reviewer).

Two kinds of facts, kept apart on purpose so a review never blames a trader for something only hindsight shows:
  known   — only bars before the entry: the engine's read (monthly chain, W/D/4H/1H structure, the play, the range,
            premium/discount), the liquidity map (pools above/below, arrays), the liquidity taken in the hours before
            the entry (a sweep or not), the clock window and the nearest scheduled news, and checks of the stop and
            targets against that liquidity.
  after   — the 1m path from the entry: fill, MFE/MAE in R, the exit under the trader's own management, the same trade
            flat at 16:55 NY (day-only), which pools price took next and when, and whether a stopped trade later
            reached its target (stop placement) or a closed one ran much further (target placement).

    uv run python research/scripts/trade_eval.py US100 short "2026-11-11 09:42" --entry 21050 --stop 21110 \
        --tp 20950:50 --tp 20800:50 [--be] [--exit-time "2026-11-11 11:30" --exit 20990] [--note "..."]
    uv run python research/scripts/trade_eval.py --item out/trades/s/plan-US500-20220527-0830.json   # an engine trade

Prints a markdown fact sheet; --json writes the facts as JSON too.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import time, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
NY = "America/New_York"
FLAT = time(16, 55)                       # futures: flat before the 17:00 break (instruments.cost_at)
PRE_SWEEP = timedelta(hours=6)            # how far back "liquidity taken before the entry" looks


# ---------------------------------------------------------------------------------------------------- the path (after)

def simulate(path: pd.DataFrame, long: bool, entry: float, stop: float, tps: list[tuple[float, float]],
             start: pd.Timestamp, be: bool = False, flat_at: pd.Timestamp | None = None,
             filled_at: pd.Timestamp | None = None) -> dict:
    """The trade on 1m bars from ``start``: a limit at ``entry`` (or filled at ``filled_at``), partials at each TP
    (price, fraction of the position), stop to entry after TP1 when ``be``; whatever is open closes at ``flat_at``
    (or at the end of ``path``). Same bar stop + target → stop first. R is on the initial risk."""
    sg = 1 if long else -1
    risk = (entry - stop) * sg
    if risk <= 0:
        raise ValueError("the stop must be on the far side of the entry")
    tps = sorted(tps, key=lambda t: t[0] * sg)
    if any((p - entry) * sg <= 0 for p, _ in tps):
        raise ValueError("every TP must be beyond the entry")
    tot = sum(f for _, f in tps) or 1.0
    p = path[path.index >= start]
    if flat_at is not None:
        p = p[p.index < flat_at]
    fill = filled_at
    if fill is None:
        hit = p[(p.low <= entry) if long else (p.high >= entry)]
        if hit.empty:
            return {"filled": None, "r": 0.0, "events": ["not filled"], "exit": None}
        fill = hit.index[0]
    cur, left, r, k, ev, mfe, mae = stop, 1.0, 0.0, 0, [f"filled {fill:%a %d %b %H:%M}"], 0.0, 0.0
    exit_ts, why = None, None
    for ts, h, l in zip(p.index, p.high, p.low):
        if ts < fill:
            continue
        mfe = max(mfe, ((h - entry) if long else (entry - l)) / risk)
        if (l <= cur) if long else (h >= cur):
            mae = min(mae, ((cur - entry) * sg) / risk)
            r += left * (cur - entry) * sg / risk
            ev.append(f"{'stop at entry' if k and be else 'stopped'} {ts:%a %H:%M} at {cur:.2f}")
            exit_ts, why, left = ts, "stop", 0.0
            break
        mae = min(mae, ((l - entry) if long else (entry - h)) / risk)
        while k < len(tps) and ((h >= tps[k][0]) if long else (l <= tps[k][0])):
            part = min(left, tps[k][1] / tot)
            r += part * (tps[k][0] - entry) * sg / risk
            left -= part
            ev.append(f"TP{k + 1} {ts:%a %H:%M} at {tps[k][0]:.2f} ({part:.0%})")
            if k == 0 and be:
                cur = entry
            k += 1
        if left <= 1e-9:
            exit_ts, why = ts, "targets"
            break
    if left > 1e-9:
        last = p[p.index >= fill]
        px = float(last.close.iloc[-1])
        r += left * (px - entry) * sg / risk
        exit_ts, why = last.index[-1], "flat" if flat_at is not None else "open at the end"
        ev.append(f"{'flat' if flat_at is not None else 'still open'} {exit_ts:%a %H:%M} ≈ {px:.2f}")
    return {"filled": fill, "r": round(r, 2), "events": ev, "exit": exit_ts, "why": why, "tp_hits": k,
            "mfe_r": round(mfe, 2), "mae_r": round(mae, 2), "risk": round(risk, 4),
            "overnight": exit_ts is not None and _session(exit_ts) != _session(fill)}


def _session(ts: pd.Timestamp):
    """The futures trading day a timestamp belongs to (a new one starts at 18:00 NY)."""
    return (ts + timedelta(hours=6)).date()


def flat_time(fill: pd.Timestamp) -> pd.Timestamp:
    """16:55 NY of the fill's trading day (a fill after 18:00 belongs to the next day)."""
    d = _session(fill)
    return pd.Timestamp.combine(d, FLAT).tz_localize(NY)


def reach(path: pd.DataFrame, long: bool, entry: float, risk: float, start: pd.Timestamp) -> dict:
    """Best and worst excursion in R from ``start`` to the end of ``path`` (hindsight: where price went)."""
    p = path[path.index >= start]
    if p.empty:
        return {"best_r": None, "worst_r": None}
    best = ((p.high.max() - entry) if long else (entry - p.low.min())) / risk
    worst = ((p.low.min() - entry) if long else (entry - p.high.max())) / risk
    bt = p.high.idxmax() if long else p.low.idxmin()
    return {"best_r": round(float(best), 2), "best_at": bt, "worst_r": round(float(worst), 2)}


def turn_point(path: pd.DataFrame, long: bool, entry: float, stop: float, fill: pd.Timestamp, items: list[dict],
               adr: float) -> dict | None:
    """Hindsight: where price actually turned. From the fill to the best favourable price in the window, the worst
    price against the trade is the turn — the price a perfect entry/stop would have used. Reports how far it was
    from our entry and stop (in R and ADR) and which levels known at the entry sat there (an area containing it
    within 0.02 ADR, or a pool within 0.05 ADR): "the pricing we should have looked at"."""
    p = path[path.index >= fill]
    if p.empty:
        return None
    best_at = p.high.idxmax() if long else p.low.idxmin()
    seg = p[p.index <= best_at]
    ext = float(seg.low.min() if long else seg.high.max())
    at = seg.low.idxmin() if long else seg.high.idxmax()
    risk = abs(entry - stop)
    sg = 1 if long else -1
    depth = (entry - ext) * sg                                  # > 0: price went this far past our entry first
    beyond_stop = (stop - ext) * sg                             # > 0: the turn was beyond our stop
    near = []
    for it in items:
        if it["role"] == "area" and it.get("top") is not None:
            if it["bottom"] - 0.02 * adr <= ext <= it["top"] + 0.02 * adr:
                near.append(f"{it['label']} {it['bottom']:.2f}–{it['top']:.2f}")
        elif it["role"] in ("buyside", "sellside") and abs(it["price"] - ext) <= 0.05 * adr:
            near.append(f"{it['label'] or it['kind']} {it['price']:.2f}")
    best = float(p.high.max() if long else p.low.min())
    return {"price": round(ext, 2), "at": at, "depth_r": round(depth / risk, 2), "depth_adr": round(depth / adr, 3),
            "beyond_stop": beyond_stop > 0, "beyond_stop_adr": round(max(beyond_stop, 0) / adr, 3),
            "levels": near[:5], "at_known_level": bool(near),
            "run_after_r": round((best - ext) * sg / risk, 2), "run_after_adr": round((best - ext) * sg / adr, 2)}


def taken(items: list[dict], path: pd.DataFrame, start: pd.Timestamp, entry: float, risk: float, long: bool) -> list[dict]:
    """Pools (buyside / sellside levels from the map at the entry) that price traded through after ``start``, in
    time order, with their distance from the entry in R (+ = in the trade's favour)."""
    p = path[path.index >= start]
    out = []
    for it in items:
        if it["role"] not in ("buyside", "sellside"):
            continue
        px = it["price"]
        hit = p[p.high >= px] if it["role"] == "buyside" else p[p.low <= px]
        if hit.empty:
            continue
        out.append({"label": it["label"] or f"{it['tf']} {it['kind']}", "price": px, "role": it["role"],
                    "at": hit.index[0], "r": round((px - entry) * (1 if long else -1) / risk, 2)})
    return sorted(out, key=lambda x: x["at"])


# ---------------------------------------------------------------------------------------------- the context (known)

def swept_before(items_before: list[dict], bars: pd.DataFrame, t0: pd.Timestamp, t1: pd.Timestamp) -> list[dict]:
    """Pools on the map at ``t0`` that price took between ``t0`` and ``t1`` (the entry): the liquidity run before it."""
    p = bars[(bars.index >= t0) & (bars.index < t1)]
    out = []
    for it in items_before:
        if it["role"] == "buyside" and (p.high >= it["price"]).any():
            out.append({"label": it["label"], "price": it["price"], "role": "buyside", "at": p.index[(p.high >= it["price"]).argmax()]})
        elif it["role"] == "sellside" and (p.low <= it["price"]).any():
            out.append({"label": it["label"], "price": it["price"], "role": "sellside", "at": p.index[(p.low <= it["price"]).argmax()]})
    return sorted(out, key=lambda x: x["at"])


def level_checks(items: list[dict], long: bool, entry: float, stop: float, tps: list[float], adr: float) -> dict:
    """Stop and targets against the liquidity known at the entry.
      stop: the nearest pool on the stop side — is the stop beyond it (behind liquidity) or short of it (the pool is
            the magnet that takes the stop first)? within 0.1 ADR of a pool = sits at the liquidity.
      TP1:  pools between the entry and TP1 (where price may stall first); a TP placed just past a pool."""
    pools = [it for it in items if it["role"] in ("buyside", "sellside")]
    against = [it for it in pools if ((it["price"] < entry) if long else (it["price"] > entry))]
    favour = [it for it in pools if ((it["price"] > entry) if long else (it["price"] < entry))]
    sg = 1 if long else -1
    near_stop = min(against, key=lambda it: abs(it["price"] - stop), default=None)
    out = {"stop": None, "tp1": None}
    if near_stop:
        beyond = (stop < near_stop["price"]) if long else (stop > near_stop["price"])
        gap = abs(stop - near_stop["price"]) / adr
        out["stop"] = {"pool": near_stop["label"], "price": near_stop["price"], "beyond_it": bool(beyond),
                       "gap_adr": round(gap, 3), "at_liquidity": gap <= 0.1}
    if tps:
        t1 = tps[0]
        inside = [it for it in favour if (it["price"] - entry) * sg < (t1 - entry) * sg]
        just_past = [it for it in inside if abs(it["price"] - t1) / adr <= 0.1]
        out["tp1"] = {"pools_before": [f"{it['label']} {it['price']:.2f}" for it in sorted(inside, key=lambda x: (x["price"] - entry) * sg)],
                      "just_past_a_pool": [f"{it['label']} {it['price']:.2f}" for it in just_past]}
    return out


def activity(bars: pd.DataFrame, at: pd.Timestamp, adr: float, mins: int = 60, days: int = 20) -> dict:
    """How active the market was in the ``mins`` before ``at`` (Sharif 2026-11-16: "be in the market when price is
    moving and active, not sit in a dry consolidation"). Known at ``at``.
      range_adr  the high–low of the last ``mins`` minutes, in ADR
      relative   that range ÷ the median range of the same clock window over the previous ``days`` trading days
                 (1 = normal for this time of day; < 0.6 quiet, > 1.5 busy)
      net_adr    |close − open| of the window in ADR (directional movement, not just chop)"""
    w = bars[(bars.index >= at - timedelta(minutes=mins)) & (bars.index < at)]
    if w.empty or not adr:
        return {"range_adr": None, "relative": None, "net_adr": None, "state": None}
    rng = float(w.high.max() - w.low.min())
    past = []
    for k in range(1, days * 2):
        t = at - timedelta(days=k)
        if t.weekday() >= 5:
            continue
        p = bars[(bars.index >= t - timedelta(minutes=mins)) & (bars.index < t)]
        if len(p) >= mins // 2:
            past.append(float(p.high.max() - p.low.min()))
        if len(past) >= days:
            break
    med = float(pd.Series(past).median()) if past else None
    rel = rng / med if med else None
    state = None if rel is None else "quiet" if rel < 0.6 else "busy" if rel > 1.5 else "normal"
    return {"range_adr": round(rng / adr, 3), "relative": round(rel, 2) if rel is not None else None,
            "net_adr": round(abs(float(w.close.iloc[-1] - w.open.iloc[0])) / adr, 3), "state": state}


FLOW_FILES = {"US100": "data/orderflow/NQ-flow1m-{year}.parquet"}      # real CME trades per minute (buy, sell, delta)
_FLOW: dict = {}


def order_flow(asset: str, at: pd.Timestamp, long: bool, flow: pd.DataFrame | None = None) -> dict | None:
    """Microstructure facts known at ``at``, from CME futures trades (aggressor side) where we have them (NQ 2024):
    the aligned imbalance I = (buy − sell) / (buy + sell), sign flipped for shorts so I > 0 = flow with the trade, over
    the last 5 minutes (the trigger) and the last 60 (the approach), and the last hour's volume ÷ the median of the
    same clock hour on the previous 20 weekdays. Descriptive: the three pre-registered order-flow rules failed on
    NQ 2024 (research/orderflow-results-NQ-2024.md), so this is a review fact, not a gate."""
    if flow is None:
        pat = FLOW_FILES.get(asset)
        f = Path(__file__).resolve().parents[2] / pat.format(year=at.year) if pat else None
        if f is None or not f.exists():
            return None
        if f not in _FLOW:
            _FLOW[f] = pd.read_parquet(f)
        flow = _FLOW[f]
    def imb(mins):
        w = flow.loc[at - timedelta(minutes=mins): at - timedelta(microseconds=1)]
        tot = float(w.buy.sum() + w.sell.sum())
        return None if len(w) < mins // 2 or tot == 0 else round(float(w.buy.sum() - w.sell.sum()) / tot * (1 if long else -1), 3)
    w = flow.loc[at - timedelta(minutes=60): at - timedelta(microseconds=1)]
    if len(w) < 30:
        return None
    past = []
    for k in range(1, 40):
        t = at - timedelta(days=k)
        if t.weekday() < 5:
            p = flow.loc[t - timedelta(minutes=60): t - timedelta(microseconds=1)]
            if len(p) >= 30:
                past.append(float(p.volume.sum()))
        if len(past) >= 20:
            break
    med = float(pd.Series(past).median()) if len(past) >= 5 else None
    i5, i60 = imb(5), imb(60)
    return {"imb_5m": i5, "imb_60m": i60, "rel_volume": round(float(w.volume.sum()) / med, 2) if med else None,
            "with_trade_5m": None if i5 is None else i5 > 0, "with_trade_60m": None if i60 is None else i60 > 0}


def range_place(pin: dict, long: bool, price: float) -> dict | None:
    """Where the entry sits in the read's current range for this side: 0 = the move's extreme, 1 = the fake-out.
    A short wants premium (≥ 0.5 from the low), a long discount."""
    R = pin.get("range")
    if not R:
        return None
    lo, hi = R["lo"], R["hi"]
    if hi <= lo:
        return None
    f = (price - lo) / (hi - lo)
    good = f >= 0.5 if not long else f <= 0.5
    return {"lo": lo, "hi": hi, "fraction_from_low": round(f, 3),
            "zone": "premium" if f > 0.5 else "discount", "right_half": bool(good),
            "ote": bool(0.62 <= (f if not long else 1 - f) <= 0.79)}


# --------------------------------------------------------------------------------------------------------- assembly

def load_bars(asset: str, entry_time: pd.Timestamp, after: timedelta) -> pd.DataFrame:
    """~4 years of history before the entry, or from the first cached month (US indices start 2019-10, others 2021-10)."""
    from datetime import date
    from ict_engine.data import dukascopy
    end = (entry_time + after + timedelta(days=2)).date()
    for start in ((entry_time - timedelta(days=1500)).date(), date(2019, 10, 1), date(2021, 10, 1)):
        if start >= entry_time.date():
            continue
        try:
            return dukascopy.load(asset, start, end)
        except FileNotFoundError:
            continue
    raise FileNotFoundError(f"no cached {asset} history before {entry_time:%Y-%m-%d}; fetch it with "
                            f"uv run python -m ict_engine.data.dukascopy fetch {asset} <start> <end>")


def intraday_pools(bars: pd.DataFrame, at: pd.Timestamp) -> list[dict]:
    """Intraday liquidity the map leaves out: the trading day's high/low so far and the last 4 h high/low (known
    at ``at``). Sharif's stops are often taken by exactly these."""
    day0 = pd.Timestamp.combine(_session(at) - timedelta(days=1), time(18, 0)).tz_localize(NY)
    out = []
    for name, t0 in (("session so far", day0), ("last 4 h", at - timedelta(hours=4))):
        p = bars[(bars.index >= t0) & (bars.index < at)]
        if len(p):
            out += [{"role": "buyside", "price": float(p.high.max()), "label": f"{name} high", "tf": "intraday", "kind": "high"},
                    {"role": "sellside", "price": float(p.low.min()), "label": f"{name} low", "tf": "intraday", "kind": "low"}]
    return out

def evaluate(asset: str, side: str, entry_time: pd.Timestamp, entry: float, stop: float,
             tps: list[tuple[float, float]], be: bool = False, exit_time=None, exit_px=None,
             after: timedelta = timedelta(days=2), bars: pd.DataFrame | None = None) -> dict:
    from ict_engine.concepts.clock import active
    from ict_engine.concepts.liquidity_map import build
    from ict_engine.data import dukascopy, instruments
    from ict_engine.news import calendar
    from read_build import read
    long = side == "long"
    if bars is None:
        bars = load_bars(asset, entry_time, after)
    if bars.index.max() < entry_time:
        raise ValueError(f"no {asset} data at {entry_time} (data ends {bars.index.max()}); fetch it first")
    # known at the entry
    rd = read(asset, bars, entry_time.date(), at=entry_time) or {}
    pin = rd.get("_plan", {})
    m = build(bars, entry_time)
    items, adr = m["items"], m["adr"]
    pre = build(bars, entry_time - PRE_SWEEP)["items"]
    try:
        clock = instruments.get(asset).clock
    except Exception:
        clock = "futures"
    try:
        ev, mins = calendar.nearest(entry_time)
        news = {"event": ev.name, "at": ev.ts, "mins": round(mins)} if ev is not None else None
    except Exception:
        news = None
    try:
        tab = calendar.load()
        hold = tab[(tab.ts >= entry_time - timedelta(minutes=30)) & (tab.ts < entry_time + after)]
        news_ahead = [f"{r.name} {r.ts:%a %d %b %H:%M} ({r.impact})" for r in hold.itertuples()]
    except Exception:
        news_ahead = []
    want = pin.get("want_side")
    known = {
        "price_at_entry": m["price"], "adr": adr, "read_kind": pin.get("kind"),
        "read_side": want, "side_matches_read": (want == ("bull" if long else "bear")) if want in ("bull", "bear") else None,
        "statements": [s["text"] for s in rd.get("statements", [])],
        "range": range_place(pin, long, entry), "momentum_adr_per_candle": pin.get("mom"), "range_tf": pin.get("rtf"),
        "activity": activity(bars, entry_time, adr), "order_flow": order_flow(asset, entry_time, long),
        "clock_windows": active(entry_time, clock, include_optional=True), "news": news, "news_ahead": news_ahead,
        "swept_before": swept_before(pre, bars, entry_time - PRE_SWEEP, entry_time),
        "levels": level_checks(items + intraday_pools(bars, entry_time), long, entry, stop, [p for p, _ in tps], adr),
        "pools_above": [f"{it['label']} {it['price']:.2f} ({it['dist_adr']:.2f} ADR)" for it in
                        sorted([i for i in items if i["role"] == "buyside" and i["where"] == "above"], key=lambda x: x["dist"])[:4]],
        "pools_below": [f"{it['label']} {it['price']:.2f} ({it['dist_adr']:.2f} ADR)" for it in
                        sorted([i for i in items if i["role"] == "sellside" and i["where"] == "below"], key=lambda x: x["dist"])[:4]],
        "arrays_near": [f"{it['label']} {it['bottom']:.2f}–{it['top']:.2f}" for it in
                        sorted([i for i in items if i["role"] == "area" and i["top"] is not None], key=lambda x: x["dist"])[:5]],
        "risk_adr": round(abs(entry - stop) / adr, 3),
        "rr_tp1": round(abs(tps[0][0] - entry) / abs(entry - stop), 2) if tps else None,
    }
    # after the entry (hindsight)
    path = bars[(bars.index >= entry_time) & (bars.index < entry_time + after)]
    sim = simulate(path, long, entry, stop, tps, entry_time, be=be)
    out = {"asset": asset, "side": side, "entry_time": entry_time, "entry": entry, "stop": stop, "tps": tps, "be": be,
           "known": known, "after": {"own": sim}}
    if sim["filled"] is not None:
        risk = sim["risk"]
        out["after"]["day_only"] = simulate(path, long, entry, stop, tps, entry_time, be=be, flat_at=flat_time(sim["filled"]),
                                            filled_at=sim["filled"])
        out["after"]["reach"] = reach(path, long, entry, risk, sim["filled"])
        out["after"]["pools_taken"] = taken(items, path, sim["filled"], entry, risk, long)[:10]
        out["after"]["turn"] = turn_point(path, long, entry, stop, sim["filled"], items + intraday_pools(bars, entry_time), adr)
        if sim["why"] == "stop":
            later = path[path.index > sim["exit"]]
            t1 = tps[0][0]
            hit = later[(later.high >= t1) if long else (later.low <= t1)]
            out["after"]["stopped_then_target"] = None if hit.empty else hit.index[0]
        if exit_time is not None and exit_px is not None:
            out["after"]["actual_exit"] = {"at": exit_time, "price": exit_px,
                                           "r": round((exit_px - entry) * (1 if long else -1) / risk, 2)}
    return out


def markdown(f: dict, note: str = "") -> str:
    k, a = f["known"], f["after"]
    L = [f"# Trade facts — {f['asset']} {f['side']} {f['entry_time']:%a %d %b %Y %H:%M} NY",
         f"entry {f['entry']} · stop {f['stop']} · TPs {', '.join(f'{p} ({int(x * 100)}%)' for p, x in f['tps'])}"
         + (" · stop to entry after TP1" if f["be"] else ""), ""]
    if note:
        L += [f"**Trader's note:** {note}", ""]
    L += ["## Known at the entry (only bars before it)",
          f"- price {k['price_at_entry']} · ADR {k['adr']} · risk {k['risk_adr']} ADR · R:R to TP1 {k['rr_tp1']}",
          f"- engine read: **{k['read_kind']}**, side {k['read_side']} → trade side matches the read: **{k['side_matches_read']}**",
          f"- clock windows: {', '.join(k['clock_windows']) or 'none'} · news: "
          + (f"{k['news']['event']} {k['news']['at']:%a %H:%M} ({k['news']['mins']:+d} min)" if k["news"] else "none near"),
          f"- scheduled news during the hold window (known in advance): {'; '.join(k['news_ahead']) or 'none'}"]
    ac = k.get("activity") or {}
    if ac.get("range_adr") is not None:
        L.append(f"- market activity, last 60 min: range {ac['range_adr']} ADR = **{ac['state']}** ({ac['relative']}× the normal "
                 f"for this time of day), net move {ac['net_adr']} ADR")
    of = k.get("order_flow")
    if of:
        L.append(f"- order flow (CME futures trades): aligned imbalance last 5 min {of['imb_5m']}, last 60 min {of['imb_60m']} "
                 f"(> 0 = flow with the trade); volume {of['rel_volume']}× normal for this hour")
    if k["range"]:
        r = k["range"]
        L.append(f"- current {k['range_tf']} range {r['lo']}–{r['hi']}: entry at {r['fraction_from_low']} from the low = "
                 f"**{r['zone']}** ({'right' if r['right_half'] else 'WRONG'} half for a {f['side']}){' · in the OTE' if r['ote'] else ''}"
                 + (f" · momentum {k['momentum_adr_per_candle']:.2f} ADR/candle" if k["momentum_adr_per_candle"] else ""))
    sw = k["swept_before"]
    L.append("- liquidity taken in the 6 h before: " + ("; ".join(f"{s['role']} {s['label']} {s['price']:.2f} at {s['at']:%H:%M}" for s in sw) if sw else "**none** (no sweep before the entry)"))
    s = k["levels"]["stop"]
    if s:
        L.append(f"- stop vs liquidity: nearest pool on the stop side {s['pool']} {s['price']:.2f} — stop is "
                 f"{'beyond it' if s['beyond_it'] else 'SHORT of it'} by {s['gap_adr']} ADR" + (" (sits at the liquidity)" if s["at_liquidity"] else ""))
    t = k["levels"]["tp1"]
    if t:
        L.append(f"- TP1 vs liquidity: pools before TP1: {', '.join(t['pools_before']) or 'none'}"
                 + (f"; TP1 just past {', '.join(t['just_past_a_pool'])}" if t["just_past_a_pool"] else ""))
    L += [f"- pools above: {'; '.join(k['pools_above']) or '–'}", f"- pools below: {'; '.join(k['pools_below']) or '–'}",
          f"- arrays near: {'; '.join(k['arrays_near']) or '–'}", "", "<details><summary>engine read statements</summary>", ""]
    L += [f"- {x}" for x in k["statements"]] + ["", "</details>", "", "## After the entry (hindsight — not knowable at the entry)"]
    o = a["own"]
    L.append(f"- your management: **{o['r']:+.2f} R** — " + " → ".join(o["events"]))
    if o["filled"] is not None:
        L.append(f"- MFE {o['mfe_r']} R · MAE {o['mae_r']} R before the exit · held overnight: {o['overnight']}")
        d = a["day_only"]
        L.append(f"- same trade, flat 16:55 NY that day: **{d['r']:+.2f} R** — " + " → ".join(d["events"][1:]))
        rc = a["reach"]
        L.append(f"- price went on to {rc['best_r']} R in favour (at {rc['best_at']:%a %H:%M}) and {rc['worst_r']} R against within the window")
        tn = a.get("turn")
        if tn:
            L.append(f"- **where price actually turned:** {tn['price']} at {tn['at']:%a %H:%M} — {tn['depth_r']} R ({tn['depth_adr']} ADR) past our entry"
                     + (f", {tn['beyond_stop_adr']} ADR beyond our stop" if tn["beyond_stop"] else ", inside our stop")
                     + f"; from there it ran {tn['run_after_r']} R ({tn['run_after_adr']} ADR) our way. Known levels at that price: "
                     + ("; ".join(tn["levels"]) if tn["levels"] else "**none on the map**"))
        if a.get("stopped_then_target"):
            L.append(f"- **stopped, then TP1 traded at {a['stopped_then_target']:%a %H:%M}** — the idea was right, the stop or timing wasn't")
        if a.get("actual_exit"):
            x = a["actual_exit"]
            L.append(f"- actual exit {x['price']} at {x['at']:%a %H:%M} = {x['r']:+.2f} R")
        L.append("- pools price took next: " + ("; ".join(f"{p['label']} {p['price']:.2f} ({p['r']:+} R) {p['at']:%a %H:%M}" for p in a["pools_taken"]) or "none"))
    return "\n".join(L)


def _ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz=NY)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset", nargs="?")
    ap.add_argument("side", nargs="?", choices=["long", "short"])
    ap.add_argument("entry_time", nargs="?", help='NY time, e.g. "2026-11-11 09:42"')
    ap.add_argument("--entry", type=float)
    ap.add_argument("--stop", type=float)
    ap.add_argument("--tp", action="append", default=[], help="price[:percent], repeatable")
    ap.add_argument("--be", action="store_true", help="stop to entry after TP1")
    ap.add_argument("--exit-time"); ap.add_argument("--exit", type=float)
    ap.add_argument("--after", type=float, default=2.0, help="days of path to look at after the entry")
    ap.add_argument("--item", help="an engine plan/trade JSON (out/plans/s/*.json or out/trades/s/*.json)")
    ap.add_argument("--use", choices=["conf", "touch"], default="conf",
                    help="--item: grade the confirmation trade (default, when it filled) or the plan's touch entry")
    ap.add_argument("--note", default="")
    ap.add_argument("--json", help="also write the facts here")
    a = ap.parse_args()
    if a.item:
        it = json.loads(Path(a.item).read_text())
        use_conf = a.use == "conf" and (it.get("conf") or {}).get("entry") is not None
        c = it["conf"] if use_conf else it
        a.note = (a.note + " " if a.note else "") + (f"[engine {it['conf']['stage']} entry (confirmation)]" if use_conf
                                                     else "[engine plan entry: limit at the zone, fill on touch]")
        if c.get("entry") is None:
            sys.exit(f"{a.item}: the engine took no trade ({(it.get('conf') or {}).get('outcome') or it.get('wait')})")
        a.asset, a.side = it["asset"], c.get("side") or it["side"]
        t = (c.get("filled") or c.get("confirmed")) if use_conf else it["decided"]
        a.entry_time = str(pd.Timestamp(t, unit="s"))                 # wall seconds → NY wall time
        a.entry, a.stop = c["entry"], c["stop"]
        a.tp = [f"{c['tp1']}:50", f"{c['final']}:50"] if abs(c["final"] - c["tp1"]) > 1e-9 else [f"{c['tp1']}:100"]
        a.be = True
    if not (a.asset and a.side and a.entry_time and a.entry is not None and a.stop is not None and a.tp):
        ap.error("need asset, side, entry_time, --entry, --stop and at least one --tp (or --item)")
    tps = []
    for t in a.tp:
        p, _, pct = t.partition(":")
        tps.append((float(p), float(pct or 100) / 100))
    f = evaluate(a.asset, a.side, _ts(a.entry_time), a.entry, a.stop, tps, be=a.be,
                 exit_time=_ts(a.exit_time) if a.exit_time else None, exit_px=a.exit, after=timedelta(days=a.after))
    print(markdown(f, a.note))
    if a.json:
        Path(a.json).write_text(json.dumps(f, default=str, indent=1))


if __name__ == "__main__":
    main()
