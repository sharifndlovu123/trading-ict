"""Counterfactual for the 'missed' gap: enter at MARKET at the bar after the decision (same stop, same TP1),
for every setup that placed an order. R after the model's own cost (cost_r recomputed on the new risk)."""
import sys, math
import pandas as pd
from ict_engine.eval.backtest import load_range
from ict_engine.data import instruments
import os
os.environ["ICT_COST_BASIS"] = sys.argv[1]
p = pd.read_parquet(f"reports/gaps-{sys.argv[1]}.parquet")
p["r"] = pd.to_numeric(p.r)
p = p.sort_values("decided_at").groupby(["family", "asset", "day", "window"], dropna=False).head(1)   # one per window
rows = []
for a, g in p.groupby("asset"):
    b = load_range(a, pd.Timestamp("2022-01-03").date(), pd.Timestamp("2024-06-28").date())
    for _, r in g.iterrows():
        end = pd.Timestamp(f"{pd.Timestamp(r.day):%Y-%m-%d} 16:00", tz="America/New_York")
        aft = b[(b.index > r.decided_at) & (b.index < end)]
        if aft.empty:
            continue
        long = r.side == "long"
        e = float(aft.open.iloc[0])
        risk = (e - r.stop) if long else (r.stop - e)
        if risk <= 0 or ((r.tp1 <= e) if long else (r.tp1 >= e)):
            rows.append((r.family, r.gap, r.day, a, None)); continue          # already through stop or TP1: no trade
        cost = instruments.cost_at(a, e, r.decided_at) / risk
        res = None
        for _, x in aft.iterrows():
            hs = x.low <= r.stop if long else x.high >= r.stop
            ht = x.high >= r.tp1 if long else x.low <= r.tp1
            if hs:
                res = -1.0; break
            if ht:
                res = abs(r.tp1 - e) / risk; break
        if res is None:
            res = ((aft.close.iloc[-1] - e) if long else (e - aft.close.iloc[-1])) / risk
        rows.append((r.family, r.gap, r.day, a, res - cost))
x = pd.DataFrame(rows, columns=["family", "gap", "day", "asset", "r_mkt"]).dropna(subset=["r_mkt"])
from ict_engine.eval.store import clustered_se
def st(g):
    m = g.r_mkt.mean(); se = clustered_se(g.r_mkt.reset_index(drop=True), g.day.reset_index(drop=True))
    return f"{m:+.3f} (n {len(g)}, z_cl {m/se:+.1f})"
print(sys.argv[1], "(first order per model/asset/day/window)")
mid = pd.Timestamp("2023-04-01")
for fam, g in x.groupby("family"):
    d = pd.to_datetime(g.day)
    print(f"{fam:14s} market: all {st(g)} | 2022-01→2023-03 {st(g[d < mid])} | 2023-04→2024-06 {st(g[d >= mid])}")
