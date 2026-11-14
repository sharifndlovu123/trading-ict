"""Counterfactual: bias gate prev_day_dol vs htf20, on setups that pass every other gate (2022–24 only)."""
import sys, math
from datetime import date, time
import pandas as pd
from ict_engine.eval import store
from ict_engine.eval.backtest import load_range
from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import bias_htf20

commit, basis = sys.argv[1], sys.argv[2]
df = store.load(commit=commit)
df = df[(df.cost_basis.fillna("cfd") == basis) & (pd.to_datetime(df.day) <= "2024-06-28")]
def others_pass(g):
    parts = dict(x.split(":") for x in g.split())
    return all(v == "1" for k, v in parts.items() if k != "bias") and "bias" in parts
pool = df[df.gates.map(others_pass)].copy()
pool = pool[pool.shadow_r.notna()] if len(pool) else pool
h = {}
for a in pool.asset.unique():
    d = resample(load_range(a, date(2021, 11, 1), date(2024, 6, 28)), "1d")
    for day in pool[pool.asset == a].day.unique():
        cut = pd.Timestamp(day).tz_localize("America/New_York")
        h[(a, day)] = bias_htf20(d[d.close_ts < cut])[0]
pool["htf20"] = [h[(a, d)] for a, d in zip(pool.asset, pool.day)]
want = pool.side.map({"long": "bull", "short": "bear"})
pool["pdd"] = pool.bias == want          # bias column = the run's rule (prev_day_dol)
pool["h20"] = pool.htf20 == want
def st(t):
    n = len(t); m = t.shadow_r.mean(); se = t.shadow_r.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    # cluster by day
    g = t.groupby(["asset", "day"]).shadow_r.sum(); se_cl = math.sqrt(((g - t.groupby(["asset","day"]).size() * m) ** 2).sum()) / n
    return f"n {n:5d}  exp {m:+.3f}  se_cl {se_cl:.3f}  z {m/se_cl:+.1f}"
print(f"== {commit} {basis}; bias rule in run: {pool.bias_rule.unique()}")
for fam, t in [("ALL", pool)] + list(pool.groupby("family")):
    print(fam)
    print("  prev_day_dol aligned :", st(t[t.pdd]))
    print("  htf20 aligned        :", st(t[t.h20]))
    print("  both                 :", st(t[t.pdd & t.h20]))
    print("  htf20 only (pdd no)  :", st(t[~t.pdd & t.h20]))
    print("  neither              :", st(t[~t.pdd & ~t.h20]))
