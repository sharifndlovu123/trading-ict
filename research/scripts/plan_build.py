"""Engine trade plans for review (local only, in-sample before 2023-09-29): at a moment the engine reads the chart
(read_build.read) and, if it has a side, proposes ONE trade — one PD array, entry, stop, TP1, final — on a clean chart.
Sharif 2026-11-16: "a clean chart is better, for a cleaner trade … dont stack FVG, OB, mitigation, breaker … based on
the movement you can decide and denote which is better for the play."

    uv run python research/scripts/plan_build.py [--n 12] [--seed 7]        # review set → out/plans
    uv run python research/scripts/plan_build.py --all [--assets US100]     # every in-sample day, descriptive stats only
    uv run python research/scripts/liqmap_server.py --port 8774 --data out/plans --page viewer/plan.html \
        --answers reports/reviews/plans.jsonl                               # → http://127.0.0.1:8774

The plan (descriptive rules, not a tested model — the review decides what changes):
  side      the read's play side (weekly; daily when counter-weekly). Mixed / no weekly side → wait.
  range     the read's current range: fake-out swing against us → the extreme of the move since.
  array     ONE, ahead of price on the pullback: a tradeable OB (event, strong body + push, right half, HTF level)
            beats any gap (HTF array + sweep beat depth — his US100 sell); else by momentum: a fast move (≥ FAST ADR
            per candle) → the first gap at/past EQ (shallow, price may not give more); a slow move → the gap in the OTE
            (0.62–0.79), else the deepest past EQ.
  entry     the array's near edge (entry drill: first touch).   stop  beyond the fake-out + 0.05 ADR (swing point).
  TP1       the move's extreme (the liquidity there), or the first pool beyond it giving ≥ 1 R.
  final     the monthly draw (BOS → EQ → FVG) when on our side and further; else the next pool beyond TP1.
  validity  until the horizon (4H range 5 days, 1H 2, D 10); cancelled if TP1 or the stop trades before the fill.
Replay on 1m: 50 % at TP1, stop to entry, rest to final; same bar stop + target → stop first.
"""
import argparse
import json
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.data import dukascopy  # noqa: E402
from liqmap_build import num, panel, wall  # noqa: E402
from read_build import ASSETS, CLOSED, CUT, HIST, NY, START, read  # noqa: E402

OUT = Path("out/plans")
HORIZON = {"4h": timedelta(days=5), "1h": timedelta(days=2), "1d": timedelta(days=10)}
FAST = {"4h": 0.2, "1h": 0.1, "1d": 0.5}          # ADR per candle of the move = fast
SPAN = {"1w": timedelta(days=730), "1d": timedelta(days=170), "4h": timedelta(days=20), "1h": timedelta(days=5),
        "15m": timedelta(hours=40), "5m": timedelta(hours=14)}


def plan(pin: dict) -> dict:
    """ONE trade from the read's inputs, or a wait with the reason."""
    ws, R = pin["want_side"], pin["range"]
    if pin["kind"] in ("mixed", "no_weekly") or ws not in ("bull", "bear"):
        return {"wait": f"no side: {pin['kind'].replace('_', ' ')}"}
    if not R:
        return {"wait": "no range on our side (no protected level to trade from)"}
    bear, lo, hi, adr, now = ws == "bear", R["lo"], R["hi"], pin["adr"], pin["now"]
    dep = (lambda p: (p - lo) / (hi - lo)) if bear else (lambda p: (hi - p) / (hi - lo))
    cands = [{**a, "src": "gap"} for a in pin["arrays"]]
    for o in pin["obs"]:
        # an entry array must be small next to the range it is traded in (a monthly body can span the whole range)
        if (o["direction"] == "bear") == bear and lo < o["bottom"] and o["top"] < hi and o["top"] - o["bottom"] <= 0.35 * (hi - lo):
            d0, d1 = sorted((dep(o["top"]), dep(o["bottom"])))
            cands.append({"tf": o["tf"], "bottom": o["bottom"], "top": o["top"], "d0": d0, "d1": d1, "src": "ob",
                          "label": f"{o['tf']} {'bearish' if bear else 'bullish'} OB", "formed": o["formed"]})
    ahead = [c for c in cands if c["d1"] > now + 0.02]
    if not ahead:
        return {"wait": "no array left between price and the fake-out"}
    obs = [c for c in ahead if c["src"] == "ob"]
    fast = (pin["mom"] or 0) >= FAST.get(pin["rtf"], 0.2)
    if obs:
        pick, why = max(obs, key=lambda c: ("1d", "1w", "1M").index(c["tf"])), "an order block (HTF array + its sweep) beats depth"
    elif fast:
        past_eq = [c for c in ahead if c["d1"] >= 0.45]
        pick = min(past_eq or ahead, key=lambda c: c["d0"])
        why = f"fast move ({pin['mom']:.2f} ADR per candle) → the first array at/past EQ; deeper may not come"
    else:
        ote = [c for c in ahead if c["d1"] >= 0.62 and c["d0"] <= 0.79]
        deep = [c for c in ahead if c["d1"] >= 0.5]
        pick = min(ote, key=lambda c: c["d0"]) if ote else max(deep or ahead, key=lambda c: c["d1"])
        why = (f"slow move ({pin['mom']:.2f} ADR per candle) → " + ("the array in the OTE" if ote else
               "the deepest array past EQ" if deep else "the only array (shallow)"))
    entry = pick["bottom"] if bear else pick["top"]
    stop = hi + 0.05 * adr if bear else lo - 0.05 * adr
    risk = abs(stop - entry)
    pools = sorted([p["price"] for p in (pin["ss"] if bear else pin["bs"])], reverse=bear)
    beyond = [x for x in pools if ((x < lo) if bear else (x > hi))]
    tps = [lo if bear else hi] + beyond
    tp1 = next((x for x in tps if abs(entry - x) >= risk), None)
    if tp1 is None:
        return {"wait": f"no room: the move's extreme and the pools beyond give < 1 R from {entry:.2f} (stop {stop:.2f})"}
    final, final_name = None, None
    ch = pin["chain"]
    if ch and ch.get("draw") and not ch["draw"]["reached"] and ch["bos"]["direction"] == ws:
        e = ch["draw"]["edge"]
        if (e < tp1) if bear else (e > tp1):
            final, final_name = e, f"monthly draw: 1M FVG {ch['draw']['fvg'][0]:.2f}–{ch['draw']['fvg'][1]:.2f} (after the BOS + EQ)"
    if final is None:
        nxt = [x for x in beyond if ((x < tp1) if bear else (x > tp1))]
        final, final_name = (nxt[0], "the next pool beyond TP1") if nxt else (tp1, "TP1 (nothing further)")
    return {"side": "short" if bear else "long", "array": pick, "why": why, "entry": round(entry, 2), "stop": round(stop, 2),
            "tp1": round(tp1, 2), "tp1_name": "the move's extreme" if tp1 == tps[0] else "a pool beyond the extreme",
            "final": round(final, 2), "final_name": final_name, "risk": round(risk, 2), "rtf": pin["rtf"],
            "range": {"lo": round(lo, 2), "hi": round(hi, 2), "t": R["t"]}, "fast": fast}


def replay(bars: pd.DataFrame, at: pd.Timestamp, p: dict) -> dict:
    end = at + HORIZON[p["rtf"]]
    path = bars[(bars.index >= at) & (bars.index < end)]
    long = p["side"] == "long"
    sg = 1 if long else -1
    e, s, t1, fn = p["entry"], p["stop"], p["tp1"], p["final"]
    risk = (e - s) * sg
    filled = None
    for ts, h, l in zip(path.index, path.high, path.low):
        if filled is None:
            if (h >= s) if not long else (l <= s):
                if (l <= e) if long else (h >= e):
                    filled = ts                      # filled and stopped in the same bar → counted below
                else:
                    return {"outcome": "cancelled: the stop level traded before the fill", "r_tp1": 0.0, "runner_r": 0.0}
            elif (h >= t1) if long else (l <= t1):
                return {"outcome": "missed: price ran to TP1 without filling", "r_tp1": 0.0, "runner_r": 0.0, "missed_at": wall(ts)}
            elif (l <= e) if long else (h >= e):
                filled = ts
            if filled is None:
                continue
        break
    if filled is None:
        return {"outcome": "not filled before the horizon", "r_tp1": 0.0, "runner_r": 0.0}
    after = path[path.index >= filled]
    cur, half, r, ev, exit_at = s, False, 0.0, [], None
    for ts, h, l in zip(after.index, after.high, after.low):
        if (l <= cur) if long else (h >= cur):
            r += (0.5 if half else 1.0) * (cur - e) * sg / risk
            ev.append(f"{'stop at entry' if half else 'stopped'} {ts:%a %H:%M}")
            exit_at = ts
            break
        if not half and ((h >= t1) if long else (l <= t1)):
            half, cur = True, e
            r += 0.5 * (t1 - e) * sg / risk
            ev.append(f"TP1 {ts:%a %H:%M}")
        if half and ((h >= fn) if long else (l <= fn)):
            r += 0.5 * (fn - e) * sg / risk
            ev.append(f"final {ts:%a %H:%M}")
            exit_at = ts
            break
    else:
        px = float(after.close.iloc[-1])
        r += (0.5 if half else 1.0) * (px - e) * sg / risk
        ev.append(f"horizon end, closed ≈ {px:.2f}")
        exit_at = after.index[-1]
    r_tp1 = (t1 - e) * sg / risk if half else (-1.0 if "stopped" in " ".join(ev) else r)
    outcome = "TP1 then " + ev[-1] if half else ev[-1]
    return {"outcome": outcome, "filled": wall(filled), "exit_at": wall(exit_at), "runner_r": round(r, 2),
            "r_tp1": round(r_tp1, 2), "events": ev, "exit": "tp" if half else "stop" if "stopped" in ev[-1] else "open"}


def item(asset: str, bars: pd.DataFrame, d: date, at: pd.Timestamp) -> dict | None:
    it = read(asset, bars, d, at=at)
    if not it:
        return None
    pin = it.pop("_plan")
    p = plan(pin)
    end = at + HORIZON.get(pin["rtf"] or "4h", timedelta(days=5))
    out = {"id": f"plan-{asset}-{at:%Y%m%d-%H%M}", "asset": asset, "day": str(d), "decided": wall(at),
           "label": f"{asset} · {at:%a %d %b %Y %H:%M} NY", "kind": "plan", "model": "engine plan",
           "read": [s for s in it["statements"] if s["id"] in ("s_mbos", "s_1w", "s_1d", "s_4h", "s_1h", "s_play", "s_range")],
           "price": it["price"], "adr": it["adr"], "read_kind": pin["kind"],
           "panels": {tf: panel(bars, tf, at - span, end) for tf, span in SPAN.items()}}
    if "wait" in p:
        out.update(side="wait", wait=p["wait"], entry=None, stop=None, tp1=None, final=None, risk=None, runner_r=None, path=[])
        return out
    rr = replay(bars, at, p)
    path = bars[(bars.index >= at) & (bars.index < end)]
    out.update(side=p["side"], entry=p["entry"], stop=p["stop"], tp1=p["tp1"], final=p["final"], tp1_name=p["tp1_name"],
               final_name=p["final_name"], risk=p["risk"], array=p["array"], why=p["why"], range=p["range"], rtf=p["rtf"],
               poi=f"{p['array']['label']} {p['array']['bottom']:.2f}–{p['array']['top']:.2f}",
               filled=rr.get("filled"), exit_at=rr.get("exit_at"), exit=rr.get("exit"), outcome=rr["outcome"],
               r=rr["r_tp1"], runner_r=rr["runner_r"], events=rr.get("events", []),
               path=[[wall(t), num(h), num(l)] for t, h, l in zip(path.index, path.high, path.low)])
    return out


def days():
    ds = [START + timedelta(days=i) for i in range((CUT - START).days)]
    return [d for d in ds if d.weekday() < 5 and d not in CLOSED]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--all", action="store_true", help="every in-sample day at 08:30 → reports/plans-insample.parquet")
    ap.add_argument("--assets", default=",".join(ASSETS))
    a = ap.parse_args()
    assets = a.assets.split(",")
    bars = {x: dukascopy.load(x, HIST, CUT + timedelta(days=30)) for x in assets}
    at_of = lambda d: pd.Timestamp(datetime.combine(d, time(8, 30)), tz=NY)
    if a.all:
        rows = []
        for x in assets:
            for d in days():
                try:
                    it = item(x, bars[x], d, at_of(d))
                except (ValueError, KeyError, IndexError):
                    continue
                if it:
                    rows.append({k: it.get(k) for k in ("asset", "day", "side", "read_kind", "wait", "entry", "stop", "tp1",
                                                         "final", "risk", "rtf", "why", "outcome", "r", "runner_r")}
                                | {"array": (it.get("array") or {}).get("label")})
            print(x, len(rows), flush=True)
        df = pd.DataFrame(rows)
        Path("reports").mkdir(exist_ok=True)
        df.to_parquet(f"reports/plans-insample-{'-'.join(assets)}.parquet")
        print(df.groupby("asset").size())
        return
    rnd = random.Random(a.seed)
    pool = [(x, d) for x in assets for d in days()]
    rnd.shuffle(pool)
    items, used, waits = [], [], 0
    for x, d in pool:
        if len(items) >= a.n:
            break
        if any(abs((d - u).days) < 14 for u in used):
            continue
        try:
            it = item(x, bars[x], d, at_of(d))
        except (ValueError, KeyError, IndexError):
            continue
        if not it:
            continue
        if it["side"] == "wait":
            if waits >= max(1, a.n // 6):
                continue
            waits += 1
        items.append(it); used.append(d)
        print(it["id"], it["side"], it.get("poi") or it.get("wait"), it.get("outcome", ""), it.get("runner_r"), flush=True)
    (OUT / "s").mkdir(parents=True, exist_ok=True)
    for it in items:
        (OUT / "s" / f"{it['id']}.json").write_text(json.dumps(it, separators=(",", ":"), default=str))
    (OUT / "index.json").write_text(json.dumps({"generated": str(date.today()), "seed": a.seed,
                                                "ids": [it["id"] for it in items]}, indent=1))
    print(len(items), "plans →", OUT / "index.json")


if __name__ == "__main__":
    main()
