"""Pre-registered order-flow tests H1–H3 on CME NQ (research/preregistered-orderflow-NQ-2024-2025.md + amendment 1).

    uv run python -m ict_engine.eval.orderflow_tests flow          # trades → 1m flow bars + stop-out absorption
    uv run python -m ict_engine.eval.orderflow_tests test          # H1–H3 → reports/orderflow-tests.md

Inputs: model runs on NQCME bars in ``reports/nqcme/<model>.parquet`` (research/scripts/nq_cme_runs.py) and the
2024 trades in ``data/orderflow``. Measures exactly as pre-registered:
- trigger imbalance I: 5 one-minute bars ending at ``decided_at`` inclusive (``decided_at`` is the start of the last
  1m bar already closed when the setup was decided, so this window has no look-ahead);
- absorption at a stop-out: t0 = first trade at/through the stop at or after the exit bar's start; over
  [t0, t0 + 5 min): V = volume within ±4 ticks of the stop ÷ the median 5-minute volume for that half-hour of the
  day over the previous 20 trading days; F = furthest trade beyond the stop, in R;
- standard errors clustered by NY trading day.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ict_engine.data import orderflow as of

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "reports" / "nqcme"
FLOW = of.OUT / "NQ-flow1m-2024.parquet"
STOPS = RUNS / "stopouts.parquet"
TICK = 0.25
POOLED = ("2022_model", "cameron", "mmxm", "silver_bullet", "pd_return")
Z_PASS = 2.4


# --- pure measures (unit-tested) ----------------------------------------------------------------------------

def cluster_diff(y, x, groups) -> tuple[float, float, float]:
    """OLS y = a + b·x with x ∈ {0, 1}; returns (b, cluster-robust se of b, z). Clusters = ``groups``."""
    y, x, g = np.asarray(y, float), np.asarray(x, float), np.asarray(groups)
    X = np.column_stack([np.ones_like(x), x])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    e = y - X @ beta
    meat = np.zeros((2, 2))
    uniq = pd.unique(g)
    for k in uniq:
        m = g == k
        s = X[m].T @ e[m]
        meat += np.outer(s, s)
    G, n = len(uniq), len(y)
    V = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - 2))
    se = float(np.sqrt(V[1, 1]))
    return float(beta[1]), se, float(beta[1] / se) if se > 0 else float("nan")


def absorption(trades: pd.DataFrame, exit_bar: pd.Timestamp, side: str, stop: float, risk: float,
               ticks: int = 4, tick: float = TICK, minutes: int = 5) -> dict:
    """Stop-out of a ``side`` trade: when the stop actually traded (t0), volume near it and how far price went
    beyond it in the next ``minutes``. Empty dict when no trade reached the stop (outside the bought window)."""
    long = side == "long"
    w = trades[(trades.index >= exit_bar) & (trades.index < exit_bar + pd.Timedelta(minutes=1 + minutes))]
    hit = w[(w.price <= stop) if long else (w.price >= stop)]
    if hit.empty or risk <= 0:
        return {}
    t0 = hit.index[0]
    after = trades[(trades.index >= t0) & (trades.index < t0 + pd.Timedelta(minutes=minutes))]
    near = after[(after.price - stop).abs() <= ticks * tick]
    beyond = (stop - after.price.min()) if long else (after.price.max() - stop)
    return {"t0": t0, "vol_near": float(near["size"].sum()), "F": float(max(beyond, 0.0) / risk)}


def baseline_5m(bars: pd.DataFrame, days: int = 20) -> pd.Series:
    """Median 5-minute volume per (day, half-hour) from the previous ``days`` trading days only (no look-ahead).
    ``bars`` = 1m bars with ``volume`` (all hours). Index: (trading date, half-hour as hours, e.g. 9.5)."""
    v = bars.volume.resample("5min").sum()
    v = v[v > 0]
    d = pd.DataFrame({"v": v.values, "date": v.index.date, "hh": v.index.hour + (v.index.minute >= 30) * 0.5})
    blocks = d.groupby(["hh", "date"]).v.apply(list)
    out = {}
    for hh, g in blocks.groupby(level="hh"):
        g = g.droplevel("hh").sort_index()                  # dates on which this half-hour traded
        dates, lists = list(g.index), list(g.values)
        for i in range(days, len(dates)):
            out[(dates[i], hh)] = float(np.median([x for l in lists[i - days:i] for x in l]))
    return pd.Series(out, dtype=float)


def first_after(bars: pd.DataFrame, after: pd.Timestamp, end: pd.Timestamp, side: str, tp1: float,
                stop: float) -> str:
    """After a stop-out: which trades first before ``end``, TP1 or the mirror level (stop ∓ |TP1 − stop|)."""
    a = bars[(bars.index > after) & (bars.index < end)]
    long = side == "long"
    d = abs(tp1 - stop)
    mirror = stop - d if long else stop + d
    up = ((a.high >= tp1) if long else (a.low <= tp1)).to_numpy()
    dn = ((a.low <= mirror) if long else (a.high >= mirror)).to_numpy()
    iu = int(up.argmax()) if up.any() else None
    idn = int(dn.argmax()) if dn.any() else None
    if iu is not None and (idn is None or iu < idn):
        return "tp1"
    if idn is not None:
        return "mirror" if iu is None or idn < iu else "both"   # same bar: unknown order
    return "neither"


# --- pipeline ------------------------------------------------------------------------------------------------

def runs() -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_parquet(p) for p in sorted(RUNS.glob("*.parquet")) if p.stem != "stopouts"}


def build_flow() -> None:
    """Month by month: 1m flow bars for the year, plus absorption measures for every stop-out in every run."""
    rs = runs()
    stops = pd.concat([d[(d.status == "traded") & (d.exit == "stop")].assign(run=k) for k, d in rs.items()])
    flow, rows = [], []
    for m in range(1, 13):
        p = of.path_for(of.SYMBOL, of.SCHEMA, f"2024-{m:02d}")
        if not p.exists():
            raise SystemExit(f"{p} missing — fetch first")
        t = pd.read_parquet(p, columns=["price", "size", "side"])
        flow.append(of.bars_1m(t)[["volume", "buy", "sell", "delta"]])
        s = stops[pd.to_datetime(stops.exit_at).dt.month == m]
        for i, r in s.iterrows():
            a = absorption(t, pd.Timestamp(r.exit_at), r.side, r.stop, abs(r.entry - r.stop))
            rows.append({"run": r.run, "row": i, **a})
        print(p.name, len(t), "stop-outs", len(s), flush=True)
    pd.concat(flow).to_parquet(FLOW)
    pd.DataFrame(rows).to_parquet(STOPS)


def _with_I(d: pd.DataFrame, flow: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["I"] = [of.imbalance(flow, pd.Timestamp(t), 5, s) for t, s in zip(d.decided_at, d.side)]
    d["day"] = pd.to_datetime(d.day).dt.date if "day" in d else pd.to_datetime(d.decided_at).dt.date
    d["half"] = np.where(pd.to_datetime(d.decided_at).dt.month <= 6, "2024-H1", "2024-H2")
    return d


def _fmt(name, b, se, z, n, extra=""):
    verdict = "PASS" if z >= Z_PASS else "fail"
    return f"| {name} | {n} | {b:+.3f} | {se:.3f} | {z:+.2f} | {verdict} | {extra} |"


def run_tests() -> str:
    rs = runs()
    flow = pd.read_parquet(FLOW)
    out = ["# Order-flow tests H1–H3 (CME NQ, 2024) — pre-registered", "",
           "Pass = one-sided z ≥ 2.4, SE clustered by day. Effects: H1 = Δ share missed (top − bottom tercile of I); "
           "H2 = Δ mean R (I > 0 − I < 0); H3 = Δ P(TP1 first) (absorbed − not).", "",
           "| test | n | effect | se | z | verdict | notes |", "|---|---|---|---|---|---|---|"]
    detail = []

    # H1 — 2022 model (limit): missed share, top vs bottom tercile of I
    d = _with_I(rs["2022_model"], flow)
    d = d[d.status.isin(["traded", "missed", "not_filled"]) & d.I.notna()]
    lo, hi = d.I.quantile([1 / 3, 2 / 3])
    d["terc"] = np.where(d.I >= hi, "top", np.where(d.I <= lo, "bottom", "mid"))
    tb = d[d.terc != "mid"]
    h1 = cluster_diff(tb.status.eq("missed"), tb.terc.eq("top"), tb.day)
    shares = tb.groupby("terc").status.apply(lambda s: s.eq("missed").mean())
    out.append(_fmt("H1 missed (2022 model)", *h1, len(tb),
                    f"missed: top {shares.get('top', np.nan):.0%}, bottom {shares.get('bottom', np.nan):.0%}; "
                    f"cuts I {lo:+.2f}/{hi:+.2f}"))
    for h, g in tb.groupby("half"):
        detail.append(_fmt(f"H1 {h}", *cluster_diff(g.status.eq("missed"), g.terc.eq("top"), g.day), len(g)))
    if h1[2] >= Z_PASS:                                        # secondary only if H1 passes
        mk = _with_I(rs["2022_model-market"], flow)
        lim = d[d.terc == "top"].assign(R=lambda x: x.r.fillna(0.0), m=0)
        mkt = mk[mk.status.isin(["traded", "missed", "not_filled"]) & (mk.I >= hi)].assign(R=lambda x: x.r.fillna(0.0), m=1)
        both = pd.concat([lim, mkt])
        out.append(_fmt("H1b market − limit R, top tercile", *cluster_diff(both.R, both.m, both.day), len(both)))

    # H2 — all five pooled, traded only: mean R, I > 0 vs I < 0
    t = pd.concat([_with_I(rs[k], flow).assign(model=k) for k in POOLED])
    t = t[(t.status == "traded") & t.I.notna() & (t.I != 0)]
    h2 = cluster_diff(t.r, t.I > 0, t.day)
    m = t.groupby(t.I > 0).r.mean()
    out.append(_fmt("H2 R with vs against flow (pooled)", *h2, len(t),
                    f"mean R: I>0 {m.get(True, np.nan):+.3f}, I<0 {m.get(False, np.nan):+.3f}"))
    for h, g in t.groupby("half"):
        detail.append(_fmt(f"H2 {h}", *cluster_diff(g.r, g.I > 0, g.day), len(g)))
    for k, g in t.groupby("model"):
        detail.append(_fmt(f"H2 {k} (descriptive)", *cluster_diff(g.r, g.I > 0, g.day), len(g)))

    # H3 — stop-outs, all five pooled: P(TP1 before mirror) absorbed vs not
    st = pd.read_parquet(STOPS).dropna(subset=["t0"])
    st = st[st.run.isin(POOLED)]
    base = baseline_5m(load_bars())
    rows = []
    for _, a in st.iterrows():
        r = rs[a.run].loc[a.row]
        t0 = pd.Timestamp(a.t0)
        key = (t0.date(), t0.hour + (0.5 if t0.minute >= 30 else 0.0))
        if key not in base.index:
            continue
        end = pd.Timestamp(f"{pd.Timestamp(r.day):%Y-%m-%d} 16:00", tz=of.NY)
        rows.append({"day": t0.date(), "half": "2024-H1" if t0.month <= 6 else "2024-H2",
                     "V": a.vol_near / base[key], "F": a.F,
                     "first": first_after(BARS_CACHE, pd.Timestamp(r.exit_at), end, r.side, r.tp1, r.stop)})
    x = pd.DataFrame(rows)
    v_hi = x.V.quantile(2 / 3)
    x["absorbed"] = (x.V >= v_hi) & (x.F < 0.5)
    h3 = cluster_diff(x["first"].eq("tp1"), x.absorbed, x.day)
    p = x.groupby("absorbed")["first"].apply(lambda s: s.eq("tp1").mean())
    out.append(_fmt("H3 TP1-first after absorbed stop-outs", *h3, len(x),
                    f"P(TP1 first): absorbed {p.get(True, np.nan):.0%} (n {int(x.absorbed.sum())}), "
                    f"other {p.get(False, np.nan):.0%}; V cut {v_hi:.2f}"))
    for h, g in x.groupby("half"):
        detail.append(_fmt(f"H3 {h}", *cluster_diff(g["first"].eq("tp1"), g.absorbed, g.day), len(g)))

    out += ["", "## Halves and per-model detail (reported, not tested)", "",
            "| test | n | effect | se | z | (z ≥ 2.4?) | |", "|---|---|---|---|---|---|---|", *detail]
    return "\n".join(out) + "\n"


BARS_CACHE: pd.DataFrame | None = None


def load_bars() -> pd.DataFrame:
    global BARS_CACHE
    if BARS_CACHE is None:
        from datetime import date
        BARS_CACHE = of.load(date(2023, 10, 1), date(2025, 1, 1), schema=of.BARS)
    return BARS_CACHE


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.eval.orderflow_tests")
    ap.add_argument("cmd", choices=("flow", "test"))
    a = ap.parse_args(argv)
    if a.cmd == "flow":
        build_flow()
    else:
        text = run_tests()
        (ROOT / "reports" / "orderflow-tests.md").write_text(text)
        print(text)


if __name__ == "__main__":
    main()
