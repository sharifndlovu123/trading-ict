"""Win-rate sweep on the cached engine reads (in-sample 2022-03 → 2023-09, descriptive — a search, not a test).

    uv run python research/scripts/plan_sweep.py [--workers 9]      # → reports/plans-sweep.parquet (+ -fills.parquet)

Every cached read → plan_build.plan → an ENTRY config (how and when the trade is opened) → every MANAGEMENT variant
(where TP1 is and how much comes off there), all on 1m bars:

  entry   touch (fill at the array's near edge) | confirm (support leg: a lower-TF FVG our way after the touch) |
          confirm_disp (that FVG must come from a displacement candle, body ≥ 1.5 × the mean of 14) |
          flip (a lower-TF close through the array → the other side on the retest; same pass as confirm)
  stop    touch: range (beyond the fake-out) | zone (beyond the array);  confirm: zone | reaction
  hold    multi (the plan's horizon, days) | day (flat 16:55 NY on the decision day, no fill after 15:00)
  tp1     plan (the structural target) | pool (nearest untaken pool ≥ 1 R) | pool05 (≥ 0.5 R) | 1R | 1.5R | 2R | 3R
  partial 0.5 | 0.75 | 1.0 of the position off at TP1; stop to entry; the rest to the plan's final or the flat time

A win = TP1 traded before the stop. Costs: futures basis (instruments.futures_cost), reported as ``r_net``.
Whatever looks best here was picked from many variants on the same data: it needs a pre-registration and one
confirmation on the unseen data before it means anything.
"""
import argparse
import pickle
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.data import dukascopy  # noqa: E402
from ict_engine.data.instruments import futures_cost  # noqa: E402
from plan_build import CACHE, plan, replay, replay_confirm  # noqa: E402
from read_build import ASSETS, CUT, HIST  # noqa: E402

TP_RULES = ("plan", "pool", "pool05", "1R", "1.5R", "2R", "3R")
PARTIALS = (0.5, 0.75, 1.0)
ENTRIES = [("touch", st, day) for st in ("range", "zone") for day in (False, True)] + \
          [(m, st, day) for m in ("confirm", "confirm_disp") for st in ("zone", "reaction") for day in (False, True)]
DISP = 1.5                 # confirm_disp: the support FVG's middle candle body ≥ 1.5 × the mean body of the 14 before


def manage_np(h: np.ndarray, l: np.ndarray, c: np.ndarray, e: float, s: float, t1: float, fn: float, long: bool,
              partial: float = 0.5) -> dict:
    """plan_build.manage on arrays (same rules, same answers): from the fill bar on, ``partial`` off at TP1, stop to
    entry from the next bar, the rest to ``fn``; same bar stop + target → stop first; open at the end → last close.
    Returns r, win (TP1 before the stop), exit (stop | be | final | tp | open) and the bar index of the exit."""
    sg = 1 if long else -1
    risk = (e - s) * sg
    n = len(h)
    if partial >= 1:
        fn = t1
    first = lambda m: int(np.argmax(m)) if m.any() else n  # noqa: E731
    i_s = first(l <= s if long else h >= s)
    i_t = first(h >= t1 if long else l <= t1)
    if i_s <= i_t and i_s < n:
        return {"r": -1.0, "win": False, "exit": "stop", "i": i_s}
    if i_t == n:
        return {"r": float((c[-1] - e) * sg / risk), "win": False, "exit": "open", "i": n - 1}
    r = partial * (t1 - e) * sg / risk
    if (h[i_t] >= fn) if long else (l[i_t] <= fn):
        return {"r": float(r + (1 - partial) * (fn - e) * sg / risk), "win": True, "exit": "tp" if partial >= 1 else "final", "i": i_t}
    hh, ll = h[i_t + 1:], l[i_t + 1:]
    m = len(hh)
    i_b = int(np.argmax(ll <= e if long else hh >= e)) if (ll <= e if long else hh >= e).any() else m
    i_f = int(np.argmax(hh >= fn if long else ll <= fn)) if (hh >= fn if long else ll <= fn).any() else m
    if i_b <= i_f and i_b < m:
        return {"r": float(r), "win": True, "exit": "be", "i": i_t + 1 + i_b}
    if i_f < m:
        return {"r": float(r + (1 - partial) * (fn - e) * sg / risk), "win": True, "exit": "final", "i": i_t + 1 + i_f}
    return {"r": float(r + (1 - partial) * (c[-1] - e) * sg / risk), "win": True, "exit": "open", "i": n - 1}


def tp1_price(rule: str, e: float, s: float, long: bool, plan_tp: float, pools: list[float]) -> float | None:
    """TP1 for a rule, or None when the rule has no target for this trade.
      plan    the structural target, if it gives ≥ 1 R          pool / pool05   the nearest untaken pool ≥ 1 / 0.5 R
      1R …    a fixed multiple of the risk"""
    sg = 1 if long else -1
    risk = (e - s) * sg
    if rule == "plan":
        return plan_tp if (plan_tp - e) * sg >= risk - 1e-9 else None
    if rule in ("pool", "pool05"):
        need = (1.0 if rule == "pool" else 0.5) * risk
        ok = sorted((x for x in pools if (x - e) * sg >= need - 1e-9), key=lambda x: (x - e) * sg)
        return ok[0] if ok else None
    return e + sg * float(rule[:-1]) * risk


def excursions(h, l, e, s, long, plan_tp) -> dict:
    """What the 1m path did after the fill, in R of the trade's own risk: the best run before the stop traded (MFE),
    the worst against over the whole window (MAE), and whether the plan's target traded after the stop."""
    sg = 1 if long else -1
    risk = (e - s) * sg
    stop = (l <= s) if long else (h >= s)
    i_s = int(np.argmax(stop)) if stop.any() else len(h)
    fav = (h - e) / risk if long else (e - l) / risk
    adv = (e - l) / risk if long else (h - e) / risk
    tp = (h >= plan_tp) if long else (l <= plan_tp)
    return {"mfe_r": float(fav[:i_s].max()) if i_s else 0.0, "mae_r": float(adv.max()), "stopped": bool(stop.any()),
            "mins_to_stop": i_s if stop.any() else None,
            "tp_after_stop": bool(tp[i_s:].any()) if stop.any() else None,
            "mfe_after_stop_r": float(fav[i_s:].max()) if stop.any() else None}


def _task(args) -> tuple[list, list]:
    asset, (mode, stop_at, day) = args
    bars = dukascopy.load(asset, HIST, CUT + timedelta(days=30))
    cost = futures_cost(asset)
    rows, fills = [], []
    # the pins cache is this project's own file, written locally by plan_build.cache_pins (trusted, not external data)
    for r in pickle.loads((CACHE / f"pins-{asset}.pkl").read_bytes()):
        pin = r["pin"]
        p = plan(pin)
        if "wait" in p:
            continue
        at = r["at"]
        got = {}

        def grab(after, e, s, t1, fn, long, got=got):
            got.update(after=after, e=float(e), s=float(s), t1=float(t1), fn=float(fn), long=bool(long))
            return {"outcome": "filled", "runner_r": 0.0, "r_tp1": 0.0}

        if mode == "touch":
            res = replay(bars, at, p, day_only=day, stop_at=stop_at, manage_fn=grab)
            stage = "touch"
        else:
            res = replay_confirm(bars, at, p, flip=True, stop_at=stop_at, day_only=day, manage_fn=grab,
                                 min_disp=DISP if mode == "confirm_disp" else 0.0)
            stage = res["stage"]
        base = {"asset": asset, "day": str(r["day"]), "entry": mode, "stop_at": stop_at, "day_only": day, "stage": stage,
                "rtf": pin["rtf"], "read_kind": pin["kind"], "src": p["array"]["src"], "fast": bool(p["fast"]),
                "array_tf": p["array"]["tf"], "depth": float(p["array"]["d0"]), "plan_side": p["side"],
                "mom": float(pin["mom"] or 0), "adr_move": float(pin.get("adr_move") or 0)}
        if not got:
            fills.append(base | {"trade": False, "outcome": res["outcome"].split(":")[0]})
            continue
        a, e, s, long = got["after"], got["e"], got["s"], got["long"]
        h, l, c = a.high.to_numpy(), a.low.to_numpy(), a.close.to_numpy()
        fill = a.index[0]
        risk = abs(e - s)
        pre = bars[(bars.index >= at) & (bars.index < fill)]
        pools = [float(x["price"]) for x in (pin["bs"] if long else pin["ss"])]
        if len(pre):                                    # a pool traded between the decision and the fill is taken
            pools = [x for x in pools if ((x > pre.high.max()) if long else (x < pre.low.min()))]
        base |= {"side": "long" if long else "short", "fill": fill.strftime("%Y-%m-%d %H:%M"), "fill_hour": fill.hour,
                 "fill_min": fill.hour * 60 + fill.minute, "same_day": fill.date() == at.date(), "wd": fill.day_of_week,
                 "risk_adr": risk / p["adr"], "cost_r": cost / risk, "plan_rr": abs(got["t1"] - e) / risk}
        fills.append(base | {"trade": True, "outcome": "filled"} | excursions(h, l, e, s, long, got["t1"]))
        for rule in TP_RULES:
            t1 = tp1_price(rule, e, s, long, got["t1"], pools)
            if t1 is None:
                continue
            fn = got["fn"] if ((got["fn"] - t1) * (1 if long else -1) > 0) else t1
            for part in PARTIALS:
                m = manage_np(h, l, c, e, s, t1, fn, long, part)
                rows.append(base | {"tp": rule, "partial": part, "r": m["r"], "win": m["win"], "exit": m["exit"],
                                    "hold_min": m["i"], "tp_rr": abs(t1 - e) / risk})
    return rows, fills


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    mid, half = (p + z * z / (2 * n)) / d, z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (mid - half, mid + half)


def stats(g: pd.DataFrame, col: str = "r_net") -> dict:
    """trades, win % (TP1 before the stop) with its Wilson 95 % range, mean / total R, R without the best 3, R with each
    trade capped at 10, z per trade and z on day totals (the three indices trade the same day: not independent)."""
    n = len(g)
    if n == 0:
        return {"n": 0}
    r = g[col]
    lo, hi = wilson(int(g.win.sum()), n)
    sd = float(r.std()) if n > 1 else 0.0
    dayr = g.groupby("day")[col].sum()
    dsd = float(dayr.std()) if len(dayr) > 1 else 0.0
    return {"n": n, "win%": round(100 * g.win.mean(), 1), "w_lo": round(100 * lo, 1), "w_hi": round(100 * hi, 1),
            "mean_R": round(float(r.mean()), 3), "sum_R": round(float(r.sum()), 1),
            "ex3": round(float(r.sort_values().iloc[:-3].sum()), 1) if n > 3 else None,
            "cap10": round(float(r.clip(upper=10).sum()), 1), "median": round(float(r.median()), 2),
            "z": round(float(r.mean()) / sd * n ** 0.5, 2) if sd > 0 else None,
            "z_day": round(float(dayr.mean()) / dsd * len(dayr) ** 0.5, 2) if dsd > 0 else None,
            "gross_R": round(float(g.r.sum()), 1)}


def main():
    import multiprocessing as mp
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--assets", default=",".join(ASSETS))
    a = ap.parse_args()
    tasks = [(x, e) for x in a.assets.split(",") for e in ENTRIES]
    rows, fills = [], []
    with mp.get_context("fork").Pool(min(a.workers, 10)) as pool:
        for rs, fs in pool.imap_unordered(_task, tasks):
            rows += rs
            fills += fs
            print(len(rows), "rows", flush=True)
    df = pd.DataFrame(rows)
    df["r_net"] = df.r - df.cost_r
    df.to_parquet("reports/plans-sweep.parquet")
    pd.DataFrame(fills).to_parquet("reports/plans-sweep-fills.parquet")
    print("→ reports/plans-sweep.parquet", len(df), "rows;", len(fills), "fills")


if __name__ == "__main__":
    main()
