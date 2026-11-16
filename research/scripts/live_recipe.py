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


def build(bars_by_asset: dict[str, pd.DataFrame], day: date, now: pd.Timestamp, mode: str) -> dict:
    from ict_engine.concepts.context import build_context
    doc = {"day": str(day), "now": now.strftime("%a %Y-%m-%d %H:%M"), "mode": mode, "variant": VARIANT, "assets": {}}
    for a, full in bars_by_asset.items():
        bars = full[full.index <= now]
        item = {"last_bar": bars.index[-1].strftime("%a %H:%M"), "last": round(float(bars.close.iloc[-1]), 2)}
        try:
            item["conditions"] = conditions(a, bars, day)
            ctx = build_context(bars, day)
            item["levels"] = {k: round(float(v), 2) for k, v in ctx.levels.items()}
            item["setups"] = setups(a, bars, day, now)
            item["breaks"] = structure_breaks(bars, now)
        except Exception as e:                                   # one index failing must not blank the page
            item["error"] = f"{type(e).__name__}: {e}"
            item.setdefault("setups", [])
        midnight = pd.Timestamp(day, tz=NY)
        item["candles"] = {"5m": candles(bars, "5min", midnight - pd.Timedelta(days=1)),
                           "15m": candles(bars, "15min", midnight - pd.Timedelta(days=6)),
                           "1h": candles(bars, "1h", midnight - pd.Timedelta(days=25))}
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
