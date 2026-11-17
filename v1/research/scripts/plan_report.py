"""Results page for the engine-plan simulation (reports/plans-sim.parquet → out/plan-results.html). In-sample, descriptive.
The review set's own days (out/trades) are left out of the per-day list so the page does not spoil the review.

    uv run python research/scripts/plan_report.py
"""
import json
from pathlib import Path

import pandas as pd

MODES = {"touch": "Touch fill", "confirm": "Confirm", "confirm_flip": "Confirm + flip",
         "confirm_flip_reaction": "Confirm + flip, old stop"}


def stats(g: pd.DataFrame) -> dict:
    t = g[g.trade == True]  # noqa: E712
    n, r = len(t), t.runner_r
    sd = float(r.std()) if n > 1 else 0.0
    tp1 = t.outcome.str.contains("TP1")                      # the vote: TP1 before the stop
    return {"plans": int(len(g)), "trades": n, "win": round(100 * float(tp1.mean()), 1) if n else None,
            "profit": round(100 * float((r > 0).mean()), 1) if n else None,
            "sum": round(float(r.sum()), 1), "mean": round(float(r.mean()), 3) if n else None,
            "z": round(float(r.mean()) / sd * n ** 0.5, 2) if n > 1 and sd > 0 else None,
            "full_stops": int((r <= -0.99).sum()), "avg_win": round(float(r[r > 0].mean()), 2) if (r > 0).any() else None,
            "wo3": round(float(r.sum() - r.nlargest(3).sum()), 1), "cap10": round(float(r.clip(upper=10).sum()), 1),
            "median": round(float(r.median()), 2) if n else None}


def main():
    df = pd.read_parquet("reports/plans-sim.parquet")
    tr = df[df["mode"] != "wait"].copy()
    tr["fast"] = tr["fast"].map({True: "fast move", False: "slow move"})
    tr["src"] = tr["src"].map({"gap": "gap (FVG / IFVG)", "ob": "order block"})
    tr["rtf"] = tr["rtf"].map({"1d": "daily range", "4h": "4H range", "1h": "1H range"})
    head = {m: stats(tr[tr["mode"] == m]) for m in MODES}
    curves = {}
    for m in MODES:
        t = tr[(tr["mode"] == m) & (tr.trade == True)].sort_values("day")  # noqa: E712
        c = t.groupby("day").runner_r.sum().cumsum()
        curves[m] = [[d, round(float(v), 2)] for d, v in c.items()]
    cuts = {}
    for key, name in (("asset", "Asset"), ("src", "Zone type"), ("fast", "Move speed"), ("rtf", "Range timeframe")):
        cuts[name] = {str(k): {m: stats(g[g["mode"] == m]) for m in MODES} for k, g in tr.groupby(key)}
    cf = tr[tr["mode"] == "confirm_flip"]
    stage = {s: stats(g) for s, g in cf.groupby("stage") if g.trade.any()}
    out_kinds = (cf.outcome.str.replace(r" (Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d\d:\d\d.*$", "", regex=True)
                 .str.replace(r"closed ≈ .*$", "", regex=True).str.replace(r"\s+$", "", regex=True)
                 .value_counts().head(12))
    waits = int((df["mode"] == "wait").sum())
    data = {"head": head, "curves": curves, "cuts": cuts, "stage": stage, "outcomes": out_kinds.to_dict(),
            "reads": int(len(df[df["mode"].isin(["wait", "touch"])])), "waits": waits,
            "period": [str(df.day.min()), str(df.day.max())]}
    html = Path("viewer/plan_results.html").read_text().replace("/*DATA*/null", json.dumps(data))
    Path("out").mkdir(exist_ok=True)
    Path("out/plan-results.html").write_text(html)
    print("→ out/plan-results.html")


if __name__ == "__main__":
    main()
