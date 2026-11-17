"""Pattern finder: which traits of a trade go with winning or losing — "do this more / do this less".

Reads any table of trades, takes the traits known when the trade was decided (time window, hour, weekday, bias, POI
type, liquidity kind, news, range place, entry mode, FVG size, …) and compares each trait value — and, with --pairs,
each pair of traits — against the rest of the trades: win rate (TP1 before the stop) with its Wilson 95% range, mean R,
the difference vs the rest, a Welch z, and robustness checks.

    uv run python research/scripts/pattern_find.py --sim reports/plans-sim.parquet --mode confirm_flip
    uv run python research/scripts/pattern_find.py --files "reports/trades/2022_model-US100-*-09c6020d.parquet" ...
    uv run python research/scripts/pattern_find.py --reviews research/trade-reviews/log.jsonl
    options: --pairs  --min-n 30  --features a,b,c  --out research/patterns/<name>.md

Labels (all are in-sample findings until a pre-registered check on unseen data confirms them):
  DO MORE / DO LESS    the difference survives the false-discovery correction (Benjamini–Hochberg, q 0.10), has the
                       same sign in both halves of the period and in most assets, and is still there with every
                       trade capped at 10 R (so it is not one outlier)
  LEAN MORE / LESS     z ≥ 2 and stable, but not through the correction — a lead, not a finding
Only traits known at the decision are used; outcome columns (r, vote, exit, MAE, shadow_*, cf_*, …) are never traits.
By default rows on or after 2024-07-01 are dropped (that data stays unseen until a pre-registered test).
"""
from __future__ import annotations

import argparse
import glob
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

UNSEEN = "2024-07-01"
CAP = 10.0
# never traits: outcomes, hindsight, identifiers and prices
LEAK = {"r", "vote", "exit", "exit_at", "filled_at", "mae_r", "runner_r", "ambiguous", "fill_price", "outcome", "trade",
        "r_tp1", "status", "stage", "trade_side", "r_own", "r_day_only", "verdict", "missed", "file", "engine_idea",
        "entry", "stop", "tp1", "final", "risk", "decided_at", "day", "entry_time", "run_id", "commit", "added_at",
        "extras", "period_start", "period_end", "gates", "failed_detail", "news_event", "wait", "cost_basis", "tp1_r"}
LEAK_PREFIX = ("shadow_", "cf_")


# ------------------------------------------------------------------------------------------------------------ stats

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def welch(a: pd.Series, b: pd.Series) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return 0.0 if se == 0 or math.isnan(se) else (a.mean() - b.mean()) / se


def p_two_sided(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2))


def bh(pvals: list[float], q: float = 0.10) -> list[bool]:
    """Benjamini–Hochberg: which tests pass at false-discovery rate ``q``."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    ok, cut = [False] * m, -1
    for rank, i in enumerate(order, 1):
        if pvals[i] <= q * rank / m:
            cut = rank
    for rank, i in enumerate(order, 1):
        ok[i] = rank <= cut
    return ok


# ------------------------------------------------------------------------------------------------------- the traits

def traits(df: pd.DataFrame, only: list[str] | None = None, max_levels: int = 12) -> pd.DataFrame:
    """Decision-time traits as strings: low-cardinality columns as they are, numeric ones cut into thirds."""
    out = {}
    cols = only or [c for c in df.columns if c not in LEAK and not c.startswith(LEAK_PREFIX) and c not in ("win", "R", "when")]
    for c in cols:
        s = df[c]
        if s.dtype == object and s.map(lambda v: isinstance(v, (list, dict, np.ndarray))).any():
            continue
        if pd.api.types.is_bool_dtype(s) or (s.dtype == object and s.dropna().map(type).eq(bool).all() and s.notna().any()):
            out[c] = s.map(lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else str(bool(v)))
        elif pd.api.types.is_numeric_dtype(s) and s.nunique() > max_levels:
            try:
                q = pd.qcut(s, 3, duplicates="drop")
            except ValueError:
                continue
            out[c] = q.map(lambda iv: None if pd.isna(iv) else f"{iv.left:.3g}–{iv.right:.3g}").astype(object)
        elif 2 <= s.nunique() <= max_levels:
            out[c] = s.map(lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)).astype(object)
    return pd.DataFrame(out, index=df.index)


# ------------------------------------------------------------------------------------------------------------- core

def prop_z(k1: int, n1: int, k2: int, n2: int) -> float:
    """Two-proportion z (pooled) for win rates."""
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else 0.0
    return 0.0 if se == 0 else (k1 / n1 - k2 / n2) / se


def compare(df: pd.DataFrame, T: pd.DataFrame, pairs: bool = False, min_n: int = 30, target: str = "r") -> pd.DataFrame:
    """Each trait value (and pair of values) vs the rest of the trades. ``target`` "r" judges the difference in mean R
    (Welch z); "win" judges the difference in win rate (two-proportion z) — robustness checks follow the target."""
    half = pd.Series(np.where(df["when"] < df["when"].median(), "early", "late"), index=df.index)
    asset = df["asset"] if "asset" in df else pd.Series("all", index=df.index)
    tests = [((c,), (v,), T[c] == v) for c in T for v in T[c].dropna().unique()]
    if pairs:
        cs = list(T)
        for i, a in enumerate(cs):
            for b in cs[i + 1:]:
                for va in T[a].dropna().unique():
                    for vb in T[b].dropna().unique():
                        tests.append(((a, b), (va, vb), (T[a] == va) & (T[b] == vb)))
    rows = []
    for cols, vals, mask in tests:
        mask = mask.fillna(False)
        g, rest = df[mask], df[~mask]
        if len(g) < min_n or len(rest) < min_n:
            continue
        wz = prop_z(int(g.win.sum()), len(g), int(rest.win.sum()), len(rest))
        z = welch(g.R, rest.R) if target == "r" else wz
        gc, rc = g.R.clip(upper=CAP), rest.R.clip(upper=CAP)
        val = (lambda x: x.R) if target == "r" else (lambda x: x.win.astype(float))
        d = val(g).mean() - val(rest).mean()
        signs_half = [np.sign(val(g)[half[g.index] == h].mean() - val(rest)[half[rest.index] == h].mean())
                      for h in ("early", "late") if (half[g.index] == h).any() and (half[rest.index] == h).any()]
        assets = [a for a in asset.unique() if (asset[g.index] == a).sum() >= 5 and (asset[rest.index] == a).any()]
        signs_asset = [np.sign(val(g)[asset[g.index] == a].mean() - val(rest)[asset[rest.index] == a].mean()) for a in assets]
        s = np.sign(d)
        lo, hi = wilson(int(g.win.sum()), len(g))
        rows.append({"trait": " & ".join(f"{c}={v}" for c, v in zip(cols, vals)), "k": len(cols), "n": len(g),
                     "win": g.win.mean(), "win_lo": lo, "win_hi": hi, "rest_win": rest.win.mean(),
                     "mean_r": g.R.mean(), "rest_r": rest.R.mean(), "diff_r": d, "z": z, "p": p_two_sided(z), "win_z": wz,
                     "capped_diff": (gc.mean() - rc.mean()) if target == "r" else d, "sum_r": g.R.sum(),
                     "halves": len(signs_half) == 2 and all(x == s for x in signs_half),
                     "assets": f"{sum(x == s for x in signs_asset)}/{len(signs_asset)}" if signs_asset else "–",
                     "assets_ok": not signs_asset or sum(x == s for x in signs_asset) >= max(1, math.ceil(len(signs_asset) * 2 / 3))})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["fdr"] = bh(out.p.tolist())
    robust = out.halves & out.assets_ok & (np.sign(out.capped_diff) == np.sign(out.diff_r))
    out["label"] = np.select(
        [out.fdr & robust & (out.diff_r > 0), out.fdr & robust & (out.diff_r < 0),
         (out.z >= 2) & robust, (out.z <= -2) & robust],
        ["DO MORE", "DO LESS", "LEAN MORE", "LEAN LESS"], default="")
    return out.sort_values("z", key=abs, ascending=False)


def report(out: pd.DataFrame, base: pd.DataFrame, title: str, note: str) -> str:
    L = [f"# Patterns — {title}", "", note, "",
         f"Base: {len(base)} trades · win {base.win.mean():.1%} · mean {base.R.mean():+.3f} R · "
         f"period {base['when'].min():%Y-%m-%d} → {base['when'].max():%Y-%m-%d} · tests run: {len(out)}", "",
         "In-sample findings: anything here becomes a rule only after a pre-registered check on unseen data "
         "(≥ 30 trades, z ≥ 2.4; CLAUDE.md). LEAN = a lead, not a finding.", ""]
    fmt = lambda r: (f"| {r.label} | {r.trait} | {r.n} | {r.win:.0%} [{r.win_lo:.0%}–{r.win_hi:.0%}] vs {r.rest_win:.0%} | "
                     f"{r.mean_r:+.3f} vs {r.rest_r:+.3f} | {r.diff_r:+.3f} ({r.capped_diff:+.3f} capped) | {r.z:+.1f} | "
                     f"{'yes' if r.halves else 'no'} | {r.assets} |")
    head = ["| label | trait | n | win % [95%] vs rest | mean R vs rest | Δ (R: capped 10 R) | z | both halves | assets |",
            "|---|---|---|---|---|---|---|---|---|"]
    for lab, name in (("MORE", "Do more"), ("LESS", "Do less")):
        sel = out[out.label.str.endswith(lab)]
        L += [f"## {name}", ""]
        L += (head + [fmt(r) for r in sel.itertuples()]) if len(sel) else ["(nothing passes the checks)"]
        L.append("")
    rest = out[(out.label == "") & (out.z.abs() >= 2)].head(15)
    if len(rest):
        L += ["## Strong but not stable (one half, one asset or one outlier carries it)", ""] + head + [fmt(r) for r in rest.itertuples()] + [""]
    return "\n".join(L)


# ----------------------------------------------------------------------------------------------------------- loading

def load_sim(path: str, mode: str) -> pd.DataFrame:
    d = pd.read_parquet(path)
    d = d[(d["mode"] == mode) & (d["trade"] == True)].copy()  # noqa: E712
    # win = TP1 traded before the stop (the vote), not "closed in profit" at the horizon
    d["R"], d["win"], d["when"] = d.runner_r.astype(float), d.outcome.str.contains("TP1"), pd.to_datetime(d.day)
    return d.drop(columns=["mode"])


def load_files(pattern: str) -> pd.DataFrame:
    fs = sorted(glob.glob(pattern))
    if not fs:
        raise SystemExit(f"no files match {pattern}")
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d = d[d["r"].notna()].copy() if "r" in d else d
    d["R"] = d["runner_r"].fillna(d["r"]).astype(float) if "runner_r" in d else d["r"].astype(float)
    d["win"] = d["vote"].map(lambda v: v is True or v == 1) if "vote" in d else d["R"] > 0
    d["when"] = pd.to_datetime(d["day"].astype(str))
    return d


def load_reviews(path: str) -> pd.DataFrame:
    rows = [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
    d = pd.DataFrame(rows)
    for k in {k for g in d.grades for k in g}:
        d[f"step_{k}"] = d.grades.map(lambda g: g.get(k))
    d["R"], d["win"] = d.r_own.astype(float), d.r_own.astype(float) > 0
    d["when"] = pd.to_datetime(d.entry_time.astype(str).str.slice(0, 10))
    return d.drop(columns=["grades"])


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--sim"); src.add_argument("--files"); src.add_argument("--reviews")
    ap.add_argument("--mode", default="confirm_flip", help="--sim: which entry mode's trades")
    ap.add_argument("--features", help="comma-separated trait columns (default: every decision-time column)")
    ap.add_argument("--pairs", action="store_true")
    ap.add_argument("--target", choices=["r", "win"], default="r", help="judge mean R (default) or win rate (TP1 before stop)")
    ap.add_argument("--min-n", type=int, default=30)
    ap.add_argument("--include-unseen", action="store_true", help="only for a pre-registered confirmation")
    ap.add_argument("--out")
    a = ap.parse_args()
    d = load_sim(a.sim, a.mode) if a.sim else load_files(a.files) if a.files else load_reviews(a.reviews)
    if not a.include_unseen:
        d = d[d["when"] < UNSEEN]
    d = d.reset_index(drop=True)
    T = traits(d, a.features.split(",") if a.features else None)
    out = compare(d, T, pairs=a.pairs, min_n=a.min_n, target=a.target)
    title = a.sim and f"{Path(a.sim).name} · {a.mode}" or a.files or a.reviews
    md = report(out, d, title, f"Judged on: {'win rate (TP1 before the stop)' if a.target == 'win' else 'mean R'} · Traits: {', '.join(T.columns)}")
    print(md)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(md)
        out.to_csv(Path(a.out).with_suffix(".csv"), index=False)


if __name__ == "__main__":
    main()
