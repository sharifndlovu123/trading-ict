"""Score research/preregistered-reentry-v2-2026-11-16.md from the sweep outputs (reports/reentry2-<model>.parquet).

    uv run python research/scripts/reentry2_eval.py

H1: added re-entries (reentry = True) of each re-entry variant, IS / OOS, per model and pooled → candidate or fail.
H2: "small grab: every counter-trend trade" vs baseline, paired per trade (same asset, decision time, side):
    Δ = runner R with the small grab − runner R with the default runner; pass = OOS mean Δ > 0, z ≥ 2.4, n ≥ 30.
"""
import math

import pandas as pd

CUT = pd.Timestamp("2023-09-29")
MODELS = ("2022_model", "mmxm")
PLAIN = "re-entry: after a stop, same side"
V2 = "re-entry v2: no chase + counter-trend small grab"
SINGLES = ("re-entry v2: no chase", "re-entry v2: counter-trend small grab")
GRAB = "small grab: every counter-trend trade"
KEY = ["asset", "decided_at", "side"]


def stats(x: pd.Series) -> str:
    n = len(x)
    if n == 0:
        return "n 0"
    m = x.mean()
    se = x.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    return f"n {n:3d}  mean {m:+.2f} R  se {se:.2f}  z {m / se if se and se == se else float('nan'):+.2f}"


def traded(df, name):
    return df[(df.variant_name == name) & (df.status == "traded") & df.runner_r.notna()]


def added(df, name):
    t = traded(df, name)
    return t[t.reentry]


def main():
    frames = {m: pd.read_parquet(f"reports/reentry2-{m}.parquet") for m in MODELS}
    print("H1 — added re-entries (runner R)")
    pooled = {}
    for name in (PLAIN, V2) + SINGLES:
        parts = []
        for m, df in frames.items():
            a = added(df, name).assign(model=m)
            parts.append(a)
            print(f"  {m:10s} {name:50s} IS {stats(a[a.day < CUT].runner_r)}   OOS {stats(a[a.day >= CUT].runner_r)}")
        p = pd.concat(parts)
        pooled[name] = p
        print(f"  {'pooled':10s} {name:50s} IS {stats(p[p.day < CUT].runner_r)}   OOS {stats(p[p.day >= CUT].runner_r)}")
    v, b = pooled[V2], pooled[PLAIN]
    vis, voos, boos = v[v.day < CUT].runner_r.mean(), v[v.day >= CUT].runner_r.mean(), b[b.day >= CUT].runner_r.mean()
    cand = vis > 0 and voos > 0 and voos >= boos
    print(f"  → v2 pooled IS {vis:+.2f}, OOS {voos:+.2f} vs plain OOS {boos:+.2f}: {'CANDIDATE' if cand else 'FAIL'}"
          f" (cannot pass: n < 30 by construction)")
    tp = v[v.tp1_only]
    print(f"  v2 re-entries closed at TP1 (against the weekly): {len(tp)} of {len(v)}; chasing refused: "
          f"{sum(((df.variant_name == V2) & df.gates.str.contains('reentry:0', na=False)).sum() for df in frames.values())}")

    print("\nH2 — every counter-trend trade takes the small grab (paired vs baseline, runner R)")
    for m, df in frames.items():
        base = traded(df, "baseline")[KEY + ["runner_r", "weekly_trend", "day"]]
        var = traded(df, GRAB)[KEY + ["runner_r", "tp1_only"]]
        j = base.merge(var, on=KEY, suffixes=("_base", "_grab"))
        unmatched = len(base) + len(var) - 2 * len(j)
        d = j.runner_r_grab - j.runner_r_base
        with_w = j[~j.tp1_only]
        print(f"  {m}: matched {len(j)} trades (unmatched {unmatched}); with-weekly trades changed: "
              f"{int((with_w.runner_r_grab - with_w.runner_r_base).abs().gt(1e-9).sum())}")
        c = j[j.tp1_only]
        dc = c.runner_r_grab - c.runner_r_base
        for lab, mask in (("IS ", c.day < CUT), ("OOS", c.day >= CUT)):
            print(f"    counter-trend {lab}: Δ {stats(dc[mask])}   (base {c.runner_r_base[mask].mean():+.2f} → grab {c.runner_r_grab[mask].mean():+.2f})")
        o = dc[c.day >= CUT]
        se = o.std(ddof=1) / math.sqrt(len(o)) if len(o) > 1 else float("nan")
        ok = len(o) >= 30 and o.mean() > 0 and se > 0 and o.mean() / se >= 2.4
        print(f"    → {'PASS' if ok else 'FAIL'}")
        for lab, mask in (("IS ", j.day < CUT), ("OOS", j.day >= CUT)):
            jj = j[mask]
            print(f"    baseline {lab}: with weekly {stats(jj[~jj.tp1_only].runner_r_base)}  |  against {stats(jj[jj.tp1_only].runner_r_base)}"
                  f"  |  neutral weekly {int((jj.weekly_trend == 'neutral').sum())}")
        print(f"    whole book OOS: baseline {stats(j[j.day >= CUT].runner_r_base)}  grab {stats(j[j.day >= CUT].runner_r_grab)}")


if __name__ == "__main__":
    main()
