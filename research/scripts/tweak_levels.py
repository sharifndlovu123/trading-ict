"""Level-based tweaks from the 30-trade review (2026-11-16), screened on every trade (a what-if, not a backtest).

The reviewers' leads: losers had the stop inside the array being traded or just short of an untaken pool, and price
turned ~0.4 ADR further at an HTF array / PDH-PDL; winners entered on the edge of a 1h/4h/1d array. Each lead becomes a
tweak that uses only levels on the liquidity map at the fill (known then):

  stop beyond array   the stop (or entry) sits inside a same-side 1h/4h/1d array → stop past its far edge + 0.02 ADR
  stop beyond pool    an untaken pool lies within 0.15 ADR beyond the stop → stop past it + 0.02 ADR
  skip: pool near     the same condition as a gate: skip the trade
  TP1 front-run       a pool lies between the entry and TP1 → TP1 0.01 ADR in front of the first one (if ≥ 1 R)
  entry at HTF array  a same-side 1h/4h/1d array starts within 0.3 ADR beyond the entry → limit at its near edge,
                      stop past its far edge + 0.02 ADR (missed if price never comes)
  skip: no HTF array  no same-side 1h/4h/1d array within 0.1 ADR of the entry → skip

    uv run python research/scripts/tweak_levels.py [--workers 4] [--out research/tweaks/<date>-levels.md]

The levels per trade are cached in reports/cache/trade-levels.pkl (slow part: one liquidity map per trade).
"""
from __future__ import annotations

import argparse
import math
import multiprocessing as mp
import pickle
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tweak_lab as tl  # noqa: E402
from ict_engine.concepts.liquidity_map import build  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402

CACHE = Path("reports/cache/trade-levels.pkl")
HTF = ("1h", "4h", "1d")
_W: dict = {}


def levels_for(bars: pd.DataFrame, at: pd.Timestamp, long: bool) -> dict:
    """Same-side HTF arrays and the pools on both sides, from the map at ``at`` (only bars before it)."""
    try:
        items = build(bars, at)["items"]
    except ValueError:
        return {"arrays": [], "pools_stop": [], "pools_tp": []}
    word = "bullish" if long else "bearish"
    arrays = [(it["tf"], it["kind"], float(it["bottom"]), float(it["top"])) for it in items
              if it["role"] == "area" and it["top"] is not None and it["tf"] in HTF and word in (it["label"] or "")]
    stop_side, tp_side = ("sellside", "buyside") if long else ("buyside", "sellside")
    return {"arrays": arrays,
            "pools_stop": sorted(float(it["price"]) for it in items if it["role"] == stop_side),
            "pools_tp": sorted(float(it["price"]) for it in items if it["role"] == tp_side)}


def tweak(name: str, long: bool, e: float, s: float, t: float, adr: float, L: dict):
    """(entry, stop, target, entry is a deeper limit?) for one trade under tweak ``name``; None = skip the trade;
    the unchanged trade when the tweak's condition does not apply."""
    sg = 1 if long else -1
    same = (e, s, t, False)
    if name == "stop beyond array":
        inside = [a for a in L["arrays"] if a[2] - 1e-9 <= s <= a[3] + 1e-9 or a[2] - 1e-9 <= e <= a[3] + 1e-9]
        if not inside:
            return same
        far = min(a[2] for a in inside) if long else max(a[3] for a in inside)
        s2 = far - sg * 0.02 * adr
        return (e, s2, t, False) if (e - s2) * sg > (e - s) * sg else same
    if name in ("stop beyond pool", "skip: pool near the stop"):
        near = [p for p in L["pools_stop"] if 0 < (s - p) * sg <= 0.15 * adr]
        if not near:
            return same
        if name.startswith("skip"):
            return None
        p = min(near) if long else max(near)
        return e, p - sg * 0.02 * adr, t, False
    if name == "TP1 front-run the first pool":
        between = [p for p in L["pools_tp"] if 0 < (p - e) * sg < (t - e) * sg]
        if not between:
            return same
        p = min(between) if long else max(between)
        t2 = p - sg * 0.01 * adr
        return (e, s, t2, False) if (t2 - e) * sg >= (e - s) * sg else same
    if name == "entry at the HTF array":
        beyond = [a for a in L["arrays"] if 0 < (e - (a[3] if long else a[2])) * sg <= 0.3 * adr]
        if not beyond:
            return same
        a = max(beyond, key=lambda x: x[3]) if long else min(beyond, key=lambda x: x[2])   # the nearest one
        e2 = a[3] if long else a[2]
        s2 = (a[2] if long else a[3]) - sg * 0.02 * adr
        return (e2, s2, t, True) if (t - e2) * sg > 0 else same
    if name == "skip: no HTF array at the entry":
        near = [a for a in L["arrays"] if a[2] - 0.1 * adr <= e <= a[3] + 0.1 * adr]
        return same if near else None
    raise ValueError(name)


NAMES = ("stop beyond array", "stop beyond pool", "skip: pool near the stop", "TP1 front-run the first pool",
         "entry at the HTF array", "skip: no HTF array at the entry")


def _one(i: int):
    r = _W["T"].iloc[i]
    return i, levels_for(_W["bars"][r.asset], r.fill, r.long)


def load(workers: int) -> pd.DataFrame:
    T = tl.load_trades(with_fill=True)
    if CACHE.exists():
        lv = pickle.loads(CACHE.read_bytes())
        if len(lv) == len(T):
            return T.assign(L=lv)
    _W["T"] = T
    _W["bars"] = {a: dukascopy.load(a, date(2019, 10, 1) if a.startswith("US") else date(2021, 10, 1), date(2024, 7, 1))
                  for a in T.asset.unique()}
    with mp.get_context("fork").Pool(min(workers, 10)) as pool:
        res = dict(pool.imap_unordered(_one, range(len(T)), chunksize=8))
    lv = [res[i] for i in range(len(T))]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(pickle.dumps(lv))
    return T.assign(L=lv)


def run(T: pd.DataFrame) -> pd.DataFrame:
    base = []
    for r in T.itertuples():
        x = tl.replay(r.hi, r.lo, r.cl, r.long, r.e, r.s, r.t)
        base.append((x[0] - r.cost / abs(r.e - r.s), x[1]) if x else (np.nan, False))
    B = pd.DataFrame(base, columns=["R", "win"], index=T.index)
    rows = [{"tweak": "as traded (day-only replay)", "applies": len(T), "trades": len(T), "skipped": 0, "missed": 0,
             "win": round(100 * B.win.mean(), 1), "mean_r": round(B.R.mean(), 3), "total_r": round(B.R.sum(), 1),
             "base_same": round(B.R.mean(), 3), "fixed": 0, "broken": 0, "cells_better": "–", "z_diff": None}]
    for name in NAMES:
        R, W, state = [], [], []
        for r, (bR, bW) in zip(T.itertuples(), base):
            tw = tweak(name, r.long, r.e, r.s, r.t, r.adr, r.L)
            if tw is None:
                R.append(0.0); W.append(False); state.append("skipped"); continue
            e2, s2, t2, deeper = tw
            if (e2, s2, t2) == (r.e, r.s, r.t):
                R.append(bR); W.append(bW); state.append("same"); continue
            if deeper:
                shift = (r.e - e2) / (r.e - s2)                       # entry moved toward the new stop, in new-R units
                x = tl.replay(r.hi, r.lo, r.cl, r.long, r.e, s2, t2, shift)
            else:
                x = tl.replay(r.hi, r.lo, r.cl, r.long, e2, s2, t2)
            if x is None:
                R.append(0.0); W.append(False); state.append("missed"); continue
            R.append(x[0] - r.cost / abs(e2 - s2)); W.append(x[1]); state.append("changed")
        res = pd.DataFrame({"R": R, "win": W, "state": state, "cell": T.cell.to_numpy()}, index=T.index)
        ch = res.state != "same"                                    # the trades the tweak touches
        took = res.state.isin(["same", "changed"])
        d = (res.R[ch] - B.R[ch]).dropna()
        cells = [(g.R.sum(), B.R[g.index].sum()) for _, g in res.groupby("cell") if len(g) >= 20]
        rows.append({"tweak": name, "applies": int(ch.sum()), "trades": int(took.sum()), "skipped": int((res.state == "skipped").sum()),
                     "missed": int((res.state == "missed").sum()), "win": round(100 * res.win[took].mean(), 1),
                     "mean_r": round(res.R[took].mean(), 3), "total_r": round(res.R.sum(), 1),
                     "base_same": round(B.R[ch].mean(), 3) if ch.any() else None,
                     "fixed": int((ch & res.win & ~B.win).sum()), "broken": int((ch & ~res.win & B.win).sum()),
                     "cells_better": f"{sum(a > b for a, b in cells)}/{len(cells)}",
                     "z_diff": round(d.mean() / d.std() * math.sqrt(len(d)), 2) if len(d) > 1 and d.std() > 0 else None})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out")
    a = ap.parse_args()
    T = load(a.workers)
    o = run(T)
    md = ["# Level-based tweaks from the 30-trade review — screened on every trade (a what-if, not a backtest)", "",
          f"{len(T)} trades (2022 model, MMxM, silver bullet; 7 datasets), day-only replay, net of the futures cost. "
          "applies = trades the tweak touches; base R = what those trades made as taken; z = paired, tweak − as taken, on those trades; "
          "total R counts a skipped or missed trade as 0.", "",
          "| tweak | applies | trades taken | skipped | missed | win % | mean R | total R | base R (touched) | fixed | broken | cells better | z |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {r.tweak} | {r.applies} | {r.trades} | {r.skipped} | {r.missed} | {r.win} | {r.mean_r:+.3f} | {r.total_r:+.1f} | "
           f"{'' if r.base_same is None else format(r.base_same, '+.3f')} | {r.fixed} | {r.broken} | {r.cells_better} | {'' if r.z_diff is None or r.z_diff != r.z_diff else r.z_diff} |"
           for r in o.itertuples()]
    text = "\n".join(md)
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text)
        o.to_csv(Path(a.out).with_suffix(".csv"), index=False)


if __name__ == "__main__":
    main()
