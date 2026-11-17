"""Score research/preregistered-weekly-structure-2026-11-16.md (+ amendments 1–2) from reports/weekly-<model>.parquet.

    uv run python research/scripts/weekly_eval.py

Paired per trade vs baseline (same asset, decision time, side): Δ = runner R with the small grab − runner R with the
default runner, over trades against the weekly structure. Pass (per model) = OOS mean Δ > 0, z ≥ 2.4, n ≥ 30.
Trades with the structure or in neutral weeks must be unchanged. Descriptive: baseline with / against / neutral.
"""
import math

import pandas as pd

CUT = pd.Timestamp("2023-09-29")
VAR = "small grab: against the weekly structure"
KEY = ["asset", "decided_at", "side"]


def stats(x: pd.Series) -> str:
    n = len(x)
    if n < 2:
        return f"n {n}"
    m, se = x.mean(), x.std(ddof=1) / math.sqrt(n)
    return f"n {n:3d}  mean {m:+.2f} R  se {se:.2f}  z {m / se if se else float('nan'):+.2f}"


def traded(df, name):
    return df[(df.variant_name == name) & (df.status == "traded") & df.runner_r.notna()]


def main():
    for m in ("2022_model", "mmxm"):
        df = pd.read_parquet(f"reports/weekly-{m}.parquet")
        base = traded(df, "baseline")[KEY + ["runner_r", "weekly_trend", "day"]]
        var = traded(df, VAR)[KEY + ["runner_r", "tp1_only", "weekly_trend"]]
        j = base.merge(var, on=KEY, suffixes=("_base", "_grab"))
        print(f"\n{m}: matched {len(j)} (baseline {len(base)}, variant {len(var)}); weekly trend column = weekly_structure "
              f"in the variant run (htf40 in the baseline run; they agree on {(j.weekly_trend_base == j.weekly_trend_grab).mean():.0%})")
        same = j[~j.tp1_only]
        print(f"  with-structure / neutral trades changed: {int((same.runner_r_grab - same.runner_r_base).abs().gt(1e-9).sum())} of {len(same)}")
        c = j[j.tp1_only]
        d = c.runner_r_grab - c.runner_r_base
        for lab, mask in (("IS ", c.day < CUT), ("OOS", c.day >= CUT)):
            print(f"  against-structure {lab}: Δ {stats(d[mask])}   (runner {c.runner_r_base[mask].mean():+.2f} → small grab {c.runner_r_grab[mask].mean():+.2f})")
        o = d[c.day >= CUT]
        se = o.std(ddof=1) / math.sqrt(len(o)) if len(o) > 1 else float("nan")
        ok = len(o) >= 30 and o.mean() > 0 and se > 0 and o.mean() / se >= 2.4
        print(f"  → {'PASS' if ok else 'FAIL'}")
        for lab, mask in (("IS ", j.day < CUT), ("OOS", j.day >= CUT)):
            jj = j[mask]
            side = jj.side.map({"long": "bull", "short": "bear"})
            w = jj.weekly_trend_grab                       # the weekly structure (baseline column = htf40)
            print(f"  baseline {lab}: with {stats(jj[side == w].runner_r_base)} | against {stats(jj[jj.tp1_only].runner_r_base)}"
                  f" | neutral {stats(jj[w == 'neutral'].runner_r_base)}")
        print(f"  whole book OOS: baseline {stats(j[j.day >= CUT].runner_r_base)}   small grab {stats(j[j.day >= CUT].runner_r_grab)}")
        wk = df[df.variant_name == VAR].drop_duplicates(["asset", "day"]).groupby(["asset", "weekly_trend"]).size()
        print("  days by weekly trend:", wk.to_dict())


if __name__ == "__main__":
    main()
