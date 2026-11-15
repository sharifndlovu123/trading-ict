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
from ict_engine.concepts.liquidity_map import _daily  # noqa: E402
from liqmap_build import candles, num, panel, wall  # noqa: E402
from read_build import ASSETS, CLOSED, CUT, HIST, NY, START, read  # noqa: E402

OUT = Path("out/plans")
HORIZON = {"4h": timedelta(days=5), "1h": timedelta(days=2), "1d": timedelta(days=10)}
FAST = {"4h": 0.2, "1h": 0.1, "1d": 0.5}          # ADR per candle of the move = fast
SPAN = {"1w": timedelta(days=730), "1d": timedelta(days=170), "4h": timedelta(days=20), "1h": timedelta(days=5),
        "15m": timedelta(hours=40), "5m": timedelta(days=7)}       # 5m back a week: builds the forming candle in watch mode


def months(bars: pd.DataFrame, a: pd.Timestamp, b: pd.Timestamp) -> list:
    """Monthly candles from NY trading days (a session that starts on the 31st at 18:00 belongs to the next month);
    the last one runs only to ``b`` (the unfinished month so far)."""
    d = _daily(bars[(bars.index >= a) & (bars.index < b)])
    if d.empty:
        return []
    key = pd.DatetimeIndex(d.index).to_period("M")
    g = d.groupby(key)
    m = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()})
    m.index = pd.DatetimeIndex([x.start_time for x in m.index]).tz_localize(NY)
    return candles(m)


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
    considered = [{k: c[k] for k in ("label", "bottom", "top", "d0", "d1", "src")} for c in ahead]
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
            "range": {"lo": round(lo, 2), "hi": round(hi, 2), "t": R["t"]}, "fast": fast, "adr": adr,
            "pools_against": [x["price"] for x in (pin["bs"] if bear else pin["ss"])], "considered": considered}


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
    return {**manage(path[path.index >= filled], e, s, t1, fn, long), "filled": wall(filled)}


def manage(after: pd.DataFrame, e: float, s: float, t1: float, fn: float, long: bool) -> dict:
    """From the fill bar on: 50 % at TP1, stop to entry, the rest to final; same bar stop + target → stop first;
    whatever is open at the end of ``after`` closes at its last close."""
    sg = 1 if long else -1
    risk = (e - s) * sg
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
    return {"outcome": outcome, "exit_at": wall(exit_at), "runner_r": round(r, 2), "r_tp1": round(r_tp1, 2),
            "events": ev, "exit": "tp" if half else "stop" if "stopped" in ev[-1] else "open"}


CTF = {"1h": "5m", "4h": "5m", "1d": "15m"}       # the lower timeframe that must confirm the zone
MIN_RISK = 0.1                                     # ADR: a confirmation stop is never tighter than this


def _limit(path: pd.DataFrame, long: bool, e: float, s: float, t1: float) -> tuple[pd.Timestamp | None, str | None]:
    """A resting limit: filled when price trades back to ``e``; cancelled if ``s`` trades first; missed (no chase) if
    ``t1`` trades first. Returns (fill ts, None) or (None, reason)."""
    for ts, h, l in zip(path.index, path.high, path.low):
        if (l <= s) if long else (h >= s):
            return (ts, None) if ((l <= e) if long else (h >= e)) else (None, "cancelled: stop traded before the retest")
        if (l <= e) if long else (h >= e):
            return ts, None
        if (h >= t1) if long else (l <= t1):
            return None, "missed: ran to TP1 without the retest"
    return None, "no retest before the horizon"


def replay_confirm(bars: pd.DataFrame, at: pd.Timestamp, p: dict, flip: bool = True) -> dict:
    """Sharif 2026-11-16: "we wait for any PD array action that supports what we are aiming to achieve or against."
      arm      the first 1m touch of the array's near edge (before it: stop traded → cancelled, TP1 → missed)
      support  a new FVG our way on the confirmation TF (CTF), its third candle closing after the arm → limit at its
               near edge, stop beyond the reaction extreme since the arm (+0.02 ADR, risk ≥ MIN_RISK ADR)
      against  a CTF close through the array's far edge → (flip) the array failed: the other side on the retest of
               that far edge (the inversion), stop beyond the array's other edge + 0.05 ADR, TP1 = the range
               fake-out the first plan used as its stop (≥ 1 R, else the next pool), final = the next pool
      neither  the stop level / TP1 trades with no confirmation → no trade
    Each closed CTF candle is used only from its close (no look-ahead); fills and management on 1m."""
    from ict_engine.concepts.bars import resample
    end = at + HORIZON[p["rtf"]]
    path = bars[(bars.index >= at) & (bars.index < end)]
    long = p["side"] == "long"
    e, s, t1, fn, adr = p["entry"], p["stop"], p["tp1"], p["final"], p["adr"]
    a = p["array"]
    far = a["bottom"] if long else a["top"]
    base = {"mode": "confirm_flip" if flip else "confirm", "r_tp1": 0.0, "runner_r": 0.0, "stage": "none"}
    armed = None
    for ts, h, l in zip(path.index, path.high, path.low):
        if (l <= s) if long else (h >= s):
            if (l <= e) if long else (h >= e):
                armed = ts
                break
            return {**base, "outcome": "cancelled: the stop level traded before the zone"}
        if (h >= t1) if long else (l <= t1):
            return {**base, "outcome": "missed: price ran to TP1 without reaching the zone"}
        if (l <= e) if long else (h >= e):
            armed = ts
            break
    if armed is None:
        return {**base, "outcome": "zone not reached before the horizon"}
    c = resample(path[path.index >= armed.floor(CTF[p["rtf"]].replace("m", "min"))], CTF[p["rtf"]])
    cts = c["close_ts"] + pd.Timedelta(minutes=1)          # close_ts = its last 1m bar; known at that bar's end
    for i in range(len(c)):
        bar = c.iloc[i]
        seen = path[(path.index >= armed) & (path.index < cts.iloc[i])]
        # 1) the stop or TP1 traded inside this candle without a confirmation yet → no trade
        if ((seen.low <= s).any() if long else (seen.high >= s).any()):
            return {**base, "stage": "armed", "armed": wall(armed), "outcome": "stop level traded with no confirmation"}
        if ((seen.high >= t1).any() if long else (seen.low <= t1).any()):
            return {**base, "stage": "armed", "armed": wall(armed), "outcome": "TP1 traded with no confirmation (missed)"}
        # 2) against: a close through the far edge
        if (bar.close < far) if long else (bar.close > far):
            if not flip:
                return {**base, "stage": "against", "armed": wall(armed), "outcome": "against: closed through the zone, no trade"}
            fl = not long
            fe = far                                                  # the retest of the failed array's far edge
            fs = (a["bottom"] - 0.05 * adr) if fl else (a["top"] + 0.05 * adr)   # beyond the array's other edge
            frisk = abs(fe - fs)
            pools = sorted([x for x in p["pools_against"] if ((x > fe) if fl else (x < fe))], reverse=not fl)
            fake = p["range"]["hi"] if fl else p["range"]["lo"]
            tps = sorted({fake, *pools}, reverse=not fl)
            tps = [x for x in tps if ((x > fe) if fl else (x < fe))]
            ft1 = next((x for x in tps if abs(x - fe) >= frisk), None)
            if ft1 is None:
                return {**base, "stage": "against", "armed": wall(armed), "outcome": "against: flip has no room (< 1 R)"}
            nxt = [x for x in tps if ((x > ft1) if fl else (x < ft1))]
            ffn = nxt[0] if nxt else ft1
            rest = path[path.index >= cts.iloc[i]]
            fill, why = _limit(rest, fl, fe, fs, ft1)
            info = {**base, "stage": "flip", "armed": wall(armed), "side": "long" if fl else "short", "entry": round(fe, 2),
                    "stop": round(fs, 2), "tp1": round(ft1, 2), "final": round(ffn, 2), "confirmed": wall(cts.iloc[i])}
            if fill is None:
                return {**info, "outcome": "flip " + why}
            m = manage(rest[rest.index >= fill], fe, fs, ft1, ffn, fl)
            return {**info, **m, "outcome": "flip: " + m["outcome"], "filled": wall(fill)}
        # 3) support: a new FVG our way whose third candle closed after the arm
        if i >= 2:
            c0, c2 = c.iloc[i - 2], bar
            gap = (c2.low > c0.high) if long else (c2.high < c0.low)
            if gap:
                ge = c2.low if long else c2.high                     # the gap's near edge from above (long) / below (short)
                react = path[(path.index >= armed) & (path.index < cts.iloc[i])]
                ext = react.low.min() if long else react.high.max()
                cs = ext - 0.02 * adr if long else ext + 0.02 * adr
                if abs(ge - cs) < MIN_RISK * adr:
                    cs = ge - MIN_RISK * adr if long else ge + MIN_RISK * adr
                crisk = abs(ge - cs)
                tps = [t1, fn] if abs(t1 - ge) >= crisk else [fn]
                ct1 = tps[0]
                if abs(ct1 - ge) < crisk:
                    return {**base, "stage": "support", "armed": wall(armed), "outcome": "support but < 1 R to the targets"}
                rest = path[path.index >= cts.iloc[i]]
                fill, why = _limit(rest, long, ge, cs, ct1)
                info = {**base, "stage": "support", "armed": wall(armed), "side": p["side"], "entry": round(float(ge), 2),
                        "stop": round(float(cs), 2), "tp1": round(ct1, 2), "final": round(fn, 2),
                        "confirmed": wall(cts.iloc[i])}
                if fill is None:
                    return {**info, "outcome": "support " + why}
                m = manage(rest[rest.index >= fill], ge, cs, ct1, fn, long)
                return {**info, **m, "outcome": "support: " + m["outcome"], "filled": wall(fill)}
    return {**base, "stage": "armed", "armed": wall(armed), "outcome": "no confirmation before the horizon"}


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
    out["panels"]["1M"] = months(bars, at - timedelta(days=1500), end)          # after the save: to the horizon
    out["panels"]["1M_pre"] = months(bars, at - timedelta(days=1500), at)       # before: the current month so far
    if "wait" in p:
        out.update(side="wait", wait=p["wait"], entry=None, stop=None, tp1=None, final=None, risk=None, runner_r=None, path=[])
        return out
    rr = replay(bars, at, p)
    cf = replay_confirm(bars, at, p, flip=True)
    path = bars[(bars.index >= at) & (bars.index < end)]
    out["considered"] = [c | {"picked": c["label"] == p["array"]["label"] and c["bottom"] == p["array"]["bottom"]}
                         for c in p["considered"]]
    out["touch"] = {"r": rr["r_tp1"], "runner_r": rr["runner_r"], "outcome": rr["outcome"]}
    out["conf"] = {k: (round(float(v), 2) if isinstance(v, float) else v) for k, v in cf.items() if k != "events"}
    out["ctf"] = CTF[p["rtf"]]
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


CACHE = Path("reports/cache")
_W: dict = {}


def at_of(d: date) -> pd.Timestamp:
    return pd.Timestamp(datetime.combine(d, time(8, 30)), tz=NY)


def _init(asset: str):
    _W["asset"], _W["bars"] = asset, dukascopy.load(asset, HIST, CUT + timedelta(days=30))


def _pin(d: date):
    try:
        it = read(_W["asset"], _W["bars"], d, at=at_of(d))
    except (ValueError, KeyError, IndexError):
        return None
    return None if not it else {"asset": _W["asset"], "day": d, "at": at_of(d), "pin": it["_plan"]}


def cache_pins(asset: str, workers: int):
    """The read's plan inputs for every in-sample day at 08:30 (slow: ~6 s a day) → reports/cache/pins-<asset>.pkl."""
    import multiprocessing as mp
    import pickle
    f = CACHE / f"pins-{asset}.pkl"
    if f.exists():
        print(f, "cached", flush=True)
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    with mp.get_context("fork").Pool(min(workers, 10), initializer=_init, initargs=(asset,)) as pool:
        rows = [r for r in pool.imap(_pin, days(), chunksize=4) if r]
    f.write_bytes(pickle.dumps(rows))
    print(asset, len(rows), "reads →", f, flush=True)


MODES = ("touch", "confirm", "confirm_flip")


def simulate(assets: list[str]) -> pd.DataFrame:
    """Every cached read → the plan → three entry modes on 1m (in-sample, descriptive):
      touch         fill at the array's near edge (the first plan)
      confirm       wait in the zone for a lower-TF FVG our way; a close through the zone = no trade
      confirm_flip  as confirm, and a close through the zone flips to the other side on the retest"""
    import pickle
    rows = []
    for x in assets:
        bars = dukascopy.load(x, HIST, CUT + timedelta(days=30))
        for r in pickle.loads((CACHE / f"pins-{x}.pkl").read_bytes()):
            p = plan(r["pin"])
            base = {"asset": x, "day": str(r["day"]), "read_kind": r["pin"]["kind"], "rtf": r["pin"]["rtf"]}
            if "wait" in p:
                rows.append(base | {"mode": "wait", "wait": p["wait"]})
                continue
            base |= {"side": p["side"], "array": p["array"]["label"], "src": p["array"]["src"], "fast": p["fast"],
                     "risk_adr": round(p["risk"] / p["adr"], 3)}
            t = replay(bars, r["at"], p)
            rows.append(base | {"mode": "touch", "stage": "touch", "trade": "filled" in t, "outcome": t["outcome"],
                                "r_tp1": t["r_tp1"], "runner_r": t["runner_r"]})
            for flip in (False, True):
                c = replay_confirm(bars, r["at"], p, flip=flip)
                rows.append(base | {"mode": c["mode"], "stage": c["stage"], "trade": "filled" in c,
                                    "outcome": c["outcome"], "r_tp1": c["r_tp1"], "runner_r": c["runner_r"],
                                    "trade_side": c.get("side", p["side"]) if "filled" in c else None})
        print(x, "simulated", flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet("reports/plans-sim.parquet")
    report(df)
    return df


def _stats(g: pd.DataFrame) -> dict:
    t = g[g.trade == True]  # noqa: E712
    n = len(t)
    r = t.runner_r
    sd = float(r.std()) if n > 1 else 0.0
    return {"days": len(g), "trades": n, "win%": round(100 * (r > 0).mean(), 1) if n else None,
            "tp1_hit%": round(100 * (t.r_tp1 > 0).mean(), 1) if n else None,
            "sum_R": round(float(r.sum()), 1), "mean_R": round(float(r.mean()), 3) if n else None,
            "z": round(float(r.mean()) / sd * n ** 0.5, 2) if n > 1 and sd > 0 else None,
            "sum_R_tp1only": round(float(t.r_tp1.sum()), 1)}


def report(df: pd.DataFrame):
    pd.set_option("display.width", 200)
    tr = df[df["mode"] != "wait"]
    days_n = len(df[df["mode"].isin(["wait", "touch"])])
    print(f"\nreads: {days_n}, waits: {(df['mode'] == 'wait').sum()}, plans: {(df['mode'] == 'touch').sum()}")
    print("\n== by mode ==")
    print(pd.DataFrame({m: _stats(tr[tr["mode"] == m]) for m in MODES}).T)
    for key in ("asset", "src", "fast", "rtf", "stage"):
        print(f"\n== mode × {key} ==")
        print(pd.DataFrame({(m, k): _stats(g) for (m, k), g in tr.groupby(["mode", key])}).T)


BUCKETS = (("support win", lambda r: r.stage == "support" and r.trade and r.runner_r > 0),
           ("support loss", lambda r: r.stage == "support" and r.trade and r.runner_r <= 0),
           ("flip", lambda r: r.stage == "flip" and r.trade),
           ("no confirmation / no fill", lambda r: r["mode"] == "confirm_flip" and not r.trade and r.stage != "none"),
           ("missed / zone not reached", lambda r: r["mode"] == "confirm_flip" and r.stage == "none"),
           ("wait", lambda r: r["mode"] == "wait"))


def sample_trades(n: int, seed: int, out_dir: Path):
    """A stratified review set from reports/plans-sim.parquet: confirmed wins, losses, flips, no-confirmation days,
    missed days and waits — the engine's full process on each (zone, considered areas, confirmation, entry, stop)."""
    df = pd.read_parquet("reports/plans-sim.parquet")
    df = df[df["mode"].isin(["confirm_flip", "wait"])].reset_index(drop=True)
    rnd = random.Random(seed)
    per = {"support win": 3, "support loss": 3, "flip": 2, "no confirmation / no fill": 2,
           "missed / zone not reached": 1, "wait": 1}
    scale = n / sum(per.values())
    bars, items, used = {}, [], []
    for name, f in BUCKETS:
        rows = [r for _, r in df.iterrows() if f(r)]
        rnd.shuffle(rows)
        k = 0
        for r in rows:
            if k >= max(1, round(per[name] * scale)):
                break
            d = date.fromisoformat(r.day)
            if any(x == r.asset and abs((d - u).days) < 14 for x, u in used):
                continue
            if r.asset not in bars:
                bars[r.asset] = dukascopy.load(r.asset, HIST, CUT + timedelta(days=30))
            it = item(r.asset, bars[r.asset], d, at_of(d))
            if not it:
                continue
            it["bucket"] = name
            items.append(it); used.append((r.asset, d)); k += 1
            print(name, "·", it["id"], it.get("conf", {}).get("outcome") or it.get("wait"), flush=True)
    rnd.shuffle(items)                              # no bucket order on the page: the outcome stays hidden
    (out_dir / "s").mkdir(parents=True, exist_ok=True)
    for it in items:
        (out_dir / "s" / f"{it['id']}.json").write_text(json.dumps(it, separators=(",", ":"), default=str))
    (out_dir / "index.json").write_text(json.dumps({"generated": str(date.today()), "seed": seed,
                                                    "ids": [it["id"] for it in items]}, indent=1))
    print(len(items), "trades →", out_dir / "index.json")


def main_all(a, assets):
    if a.all:
        for x in assets:
            cache_pins(x, a.workers)
    simulate(assets)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--all", action="store_true", help="every in-sample day at 08:30 → reports/plans-insample.parquet")
    ap.add_argument("--assets", default=",".join(ASSETS))
    ap.add_argument("--sim", action="store_true", help="re-run the entry modes on the cached reads → reports/plans-sim.parquet")
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--trades", action="store_true", help="stratified review set of confirmed trades → out/trades")
    a = ap.parse_args()
    assets = a.assets.split(",")
    if a.all or a.sim:
        return main_all(a, assets)
    if a.trades:
        return sample_trades(a.n, a.seed, Path("out/trades"))
    bars = {x: dukascopy.load(x, HIST, CUT + timedelta(days=30)) for x in assets}
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
