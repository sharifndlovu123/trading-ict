"""Tweak lab: replay every backtest trade under alternative pricing and count how many trades each tweak fixes.

Sharif 2026-11-16: "when we review trades you should tweak what can be tweaked, find patterns through possible tweaks,
where if this is tweaked a certain way it works for many more trades … tweaks need to go through the audit process and
if it's backtested and shows improvements it's worth the addition."

    uv run python research/scripts/tweak_lab.py [--out research/tweaks/<date>.md]

Each trade (focus models on every in-sample dataset) is replayed on 1m bars from its fill to 16:55 NY of its trading
day (day-only), once as it was and once per tweak. A tweak changes only pricing — the stop, the target or the entry
price — never which setups are taken, so this is a what-if screen, not a backtest: a tweak that looks good here still
goes through the change gate (an option behind a flag, a real backtest, then a pre-registered run).

Reported per tweak: trades, win % (TP before the stop), mean R net of the futures cost (R on the tweak's own risk),
z, trades fixed (loss → win) and broken (win → loss), and on how many dataset × model cells total R improves.
Same bar stop + target → stop first. Unseen data (2024-07+) is never loaded.
"""
from __future__ import annotations

import argparse
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.concepts.liquidity_map import _daily  # noqa: E402
from ict_engine.data import dukascopy, instruments  # noqa: E402

NY = "America/New_York"
MODELS = {"2022_model": "backtest-{a}", "mmxm": "backtest-mmxm-{a}", "silver_bullet": "backtest-silver_bullet-{a}"}
SETS = [("2022-24", a, "2022-01-03-2024-06-28") for a in ("US100", "US500", "US30", "XAUUSD")] + \
       [("2020", a, "2020-01-02-2020-12-31") for a in ("US100", "US500", "US30")]
PARKED = {("mmxm", "XAUUSD")}

# name → (entry shift toward the stop in R, stop rule, target rule)
#   stop:   ("x", k) distance × k | ("adr", f) at least f × ADR | None
#   target: ("r", k) k × the tweak's own risk | ("px",) the original TP1 price
TWEAKS = {
    "as traded (day-only replay)": (0, None, ("px",)),
    "TP1 at 1 R": (0, None, ("r", 1.0)),
    "TP1 at 1.5 R": (0, None, ("r", 1.5)),
    "TP1 at 2 R": (0, None, ("r", 2.0)),
    "stop × 1.5, TP1 price kept": (0, ("x", 1.5), ("px",)),
    "stop × 2, TP1 price kept": (0, ("x", 2.0), ("px",)),
    "stop × 3, TP1 price kept": (0, ("x", 3.0), ("px",)),
    "stop × 2, TP1 at 1 R": (0, ("x", 2.0), ("r", 1.0)),
    "stop ≥ 0.05 ADR, TP1 price kept": (0, ("adr", 0.05), ("px",)),
    "stop ≥ 0.10 ADR, TP1 price kept": (0, ("adr", 0.10), ("px",)),
    "stop ≥ 0.10 ADR, TP1 at 1 R": (0, ("adr", 0.10), ("r", 1.0)),
    "stop ≥ 0.15 ADR, TP1 at 1 R": (0, ("adr", 0.15), ("r", 1.0)),
    "entry 0.25 R deeper (same stop, same TP1)": (0.25, None, ("px",)),
    "entry 0.5 R deeper (same stop, same TP1)": (0.5, None, ("px",)),
    "entry 0.5 R deeper, stop × 1.5": (0.5, ("x", 1.5), ("px",)),
}


def replay(hi: np.ndarray, lo: np.ndarray, cl: np.ndarray, long: bool, e: float, s: float, t: float,
           shift: float = 0.0) -> tuple[float, bool, bool] | None:
    """(R on this stop, win, stopped) for one trade on its bars from the fill; None when a deeper entry never fills.
    ``shift`` > 0 moves the entry that many R toward the stop: a limit that must trade before the target does."""
    sg = 1 if long else -1
    start = 0
    if shift:
        e2 = e - shift * (e - s)                       # toward the stop
        reach = np.nonzero((lo <= e2) if long else (hi >= e2))[0]
        tp_first = np.nonzero((hi >= t) if long else (lo <= t))[0]
        if not len(reach) or (len(tp_first) and tp_first[0] < reach[0]):
            return None                                # the trade left without the deeper fill
        start, e = int(reach[0]), e2
    risk = (e - s) * sg
    if risk <= 0 or (t - e) * sg <= 0:
        return None
    h, l = hi[start:], lo[start:]
    st = np.nonzero((l <= s) if long else (h >= s))[0]
    tp = np.nonzero((h >= t) if long else (l <= t))[0]
    i_s, i_t = (st[0] if len(st) else 10 ** 9), (tp[0] if len(tp) else 10 ** 9)
    if i_s <= i_t and i_s < 10 ** 9:
        return -1.0, False, True
    if i_t < i_s:
        return (t - e) * sg / risk, True, False
    return (float(cl[-1]) - e) * sg / risk, False, False


def apply(tw, long: bool, e: float, s: float, t: float, adr: float) -> tuple[float, float, float]:
    """The tweak's (stop, target, entry shift) for one trade."""
    shift, stop_rule, tgt = tw
    sg = 1 if long else -1
    dist = (e - s) * sg
    if stop_rule:
        dist = dist * stop_rule[1] if stop_rule[0] == "x" else max(dist, stop_rule[1] * adr)
    s2 = e - sg * dist
    e2 = e - shift * (e - s2) if shift else e
    t2 = t if tgt[0] == "px" else e2 + sg * tgt[1] * (e2 - s2) * sg
    return s2, t2, shift


def load_trades(with_fill: bool = False) -> pd.DataFrame:
    out = []
    for a in sorted({s[1] for s in SETS}):
        b = dukascopy.load(a, date(2019, 10, 1) if a.startswith("US") else date(2021, 10, 1), date(2024, 7, 1))
        idx = b.index.tz_convert("UTC").tz_localize(None).to_numpy()
        hi, lo, cl = b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
        dd = _daily(b)
        adr = (dd.high - dd.low).rolling(20).mean().shift(1)
        adr.index = pd.DatetimeIndex(dd.index).tz_localize(None).normalize()
        cost = instruments.futures_cost(a)
        for per, asset, span in SETS:
            if asset != a:
                continue
            for m, pat in MODELS.items():
                f = Path(f"reports/{pat.format(a=a)}-{span}-futures.parquet")
                if (m, a) in PARKED or not f.exists():
                    continue
                d = pd.read_parquet(f)
                d = d[(d.status == "traded") & d.r.notna() & d.filled_at.notna()]
                fills = pd.to_datetime(d.filled_at, utc=True).dt.tz_convert(NY)
                for r, fill in zip(d.itertuples(), fills):
                    flat = (fill + pd.Timedelta(hours=6)).normalize() + pd.Timedelta(hours=16, minutes=55)
                    i0 = np.searchsorted(idx, np.datetime64(fill.tz_convert("UTC").tz_localize(None)))
                    i1 = np.searchsorted(idx, np.datetime64(flat.tz_convert("UTC").tz_localize(None)))
                    if i1 - i0 < 2:
                        continue
                    A = adr.get(fill.tz_localize(None).normalize())
                    if A is None or not A == A:
                        A = adr[adr.index <= fill.tz_localize(None)].iloc[-1]
                    out.append({"cell": f"{per} {a} {m}", "family": m, "asset": a, "fill": fill, "long": r.side == "long", "e": float(r.entry),
                                "s": float(r.stop), "t": float(r.tp1), "adr": float(A), "cost": cost,
                                "hi": hi[i0:i1], "lo": lo[i0:i1], "cl": cl[i0:i1]})
    return pd.DataFrame(out)


def run(T: pd.DataFrame, tweaks=TWEAKS) -> pd.DataFrame:
    rows, base = [], None
    for name, tw in tweaks.items():
        R, W, ok = [], [], []
        for r in T.itertuples():
            s2, t2, shift = apply(tw, r.long, r.e, r.s, r.t, r.adr)
            x = replay(r.hi, r.lo, r.cl, r.long, r.e, s2, t2, shift)
            if x is None:
                R.append(np.nan); W.append(False); ok.append(False)
                continue
            e2 = r.e - shift * (r.e - s2)
            R.append(x[0] - r.cost / abs(e2 - s2)); W.append(x[1]); ok.append(True)
        res = pd.DataFrame({"cell": T.cell, "R": R, "win": W, "ok": ok})
        if base is None:
            base = res
        t = res[res.ok]
        n = len(t)
        both = res.ok & base.ok
        # per cell: total R over every trade (a missed trade = 0), so a tweak that skips trades is compared fairly
        cells = [(g.R.fillna(0).sum(), base.loc[g.index].R.fillna(0).sum()) for _, g in res.groupby("cell") if len(g) >= 20]
        rows.append({"tweak": name, "trades": n, "missed": int((~res.ok).sum()),
                     "win": round(100 * t.win.mean(), 1), "mean_r": round(t.R.mean(), 3),
                     "z": round(t.R.mean() / t.R.std() * math.sqrt(n), 2), "total_r": round(t.R.sum(), 1),
                     "fixed": int((both & res.win & ~base.win).sum()), "broken": int((both & ~res.win & base.win).sum()),
                     "cells_better": f"{sum(a > b for a, b in cells)}/{len(cells)}"})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    T = load_trades()
    o = run(T)
    md = ["# Tweak lab — what-if pricing on every trade (a screen, not a backtest)", "",
          f"{len(T)} trades, focus models (2022 model, MMxM, silver bullet) on {T.cell.nunique()} dataset × model cells, "
          "day-only replay, net of the futures cost. fixed = loss → win, broken = win → loss vs the trade as taken.", "",
          "| tweak | trades | missed | win % | mean R | z | total R | fixed | broken | cells better |", "|---|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {r.tweak} | {r.trades} | {r.missed} | {r.win} | {r.mean_r:+.3f} | {r.z:+.2f} | {r.total_r:+.1f} | {r.fixed} | {r.broken} | {r.cells_better} |"
           for r in o.itertuples()]
    text = "\n".join(md)
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text)
        o.to_csv(Path(a.out).with_suffix(".csv"), index=False)


if __name__ == "__main__":
    main()
