"""The one pre-registered run of research/preregistered-orderflow-30min-2024H2.md. Do not re-run with other settings."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from micro_features import cluster_z, flow_imbalance  # noqa: E402

NY = "America/New_York"
FILES = {"2022_model": "backtest-US100", "mmxm": "backtest-mmxm-US100", "silver_bullet": "backtest-silver_bullet-US100"}
LO, HI = -0.014, 0.025
A, B = pd.Timestamp("2024-07-01", tz=NY), pd.Timestamp("2025-01-01", tz=NY)


def main():
    flow = pd.read_parquet("data/orderflow/NQ-flow1m-2024.parquet")
    rows = []
    for fam, f in FILES.items():
        d = pd.read_parquet(f"reports/{f}-2024-07-01-2026-11-12-futures.parquet")
        d = d[(d.status == "traded") & d.r.notna() & d.filled_at.notna()].copy()
        d["filled_at"] = pd.to_datetime(d.filled_at, utc=True).dt.tz_convert(NY)
        d = d[(d.filled_at >= A) & (d.filled_at < B)]
        for r in d.itertuples():
            rows.append({"family": fam, "filled_at": r.filled_at, "day": r.filled_at.strftime("%Y-%m-%d"), "r": float(r.r),
                         "win": r.vote is True or r.vote == 1, "imb30": flow_imbalance(flow, r.filled_at, 30, r.side)})
    t = pd.DataFrame(rows)
    n_all = len(t)
    t = t[t.imb30.notna()]
    t["grp"] = np.select([t.imb30 <= LO, t.imb30 >= HI], ["against", "with"], "middle")
    print(f"trades {n_all}, with flow {len(t)}")
    for g in ("against", "middle", "with"):
        x = t[t.grp == g]
        print(f"  {g:8s} n {len(x):4d} win {100 * x.win.mean():5.1f}%  mean R {x.r.mean():+.3f}")
    two = t[t.grp != "middle"]
    z = float(cluster_z(two.r, (two.grp == "against").astype(float), two.day)[0])
    a, w = two[two.grp == "against"], two[two.grp == "with"]
    print(f"against − with: {a.r.mean() - w.r.mean():+.3f} R, one-sided z (day-clustered) {z:+.2f}; "
          f"pass needs n ≥ 30 each and z ≥ 2.4 → {'PASS' if z >= 2.4 and min(len(a), len(w)) >= 30 else 'FAIL'}")
    for name, m in (("Q3", two.filled_at.dt.month <= 9), ("Q4", two.filled_at.dt.month >= 10)):
        x = two[m]
        print(f"  {name}: against {x[x.grp == 'against'].r.mean():+.3f} (n {(x.grp == 'against').sum()}) | with {x[x.grp == 'with'].r.mean():+.3f} (n {(x.grp == 'with').sum()})")
    for fam, x in two.groupby("family"):
        print(f"  {fam}: against {x[x.grp == 'against'].r.mean():+.3f} (n {(x.grp == 'against').sum()}) | with {x[x.grp == 'with'].r.mean():+.3f} (n {(x.grp == 'with').sum()})")


if __name__ == "__main__":
    main()
