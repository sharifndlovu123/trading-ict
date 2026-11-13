"""Trade store: every backtest run in one clean, typed, labelled table.

    uv run python -m ict_engine.eval.store add reports/backtest*-2024-07-01-2026-11-12.parquet
    uv run python -m ict_engine.eval.store runs
    uv run python -m ict_engine.eval.store board --by family window --min-n 30 [--asset US100] [--start 2022-01-01] [--commit abc1234]

Layout: ``reports/trades/<run_id>.parquet``, one file per run. A run is one
(model, asset, period, settings label, code commit) backtest. Every row is one setup,
traded or not (the ``ict_engine.eval.backtest`` table), plus run labels:

    run_id, commit, extras, period_start, period_end, added_at, family

Rules: required columns must be present. One run holds one model family and one asset.
Adding the same run again is refused unless ``replace=True``. Mixed None/bool columns
are stored as nullable booleans. This is the database the leaderboard and the
"trade these times × models" selection read from.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import subprocess
from pathlib import Path

import pandas as pd

from ict_engine.eval.bias import wilson

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "reports" / "trades"
REQUIRED = ("model", "variant", "asset", "style", "day", "side", "decided_at", "weekday", "hour",
            "window", "status", "r", "vote")
BOOL_COLS = ("vote", "ambiguous", "shadow_vote", "shadow_ambiguous",
             "cf_wide_stop_vote", "cf_tp1_1r_vote", "cf_flip_vote")
FLOAT_COLS = ("arm",)
FAMILY = {"mmbm": "mmxm", "mmsm": "mmxm"}


def git_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "ict_engine"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        return sha + ("+dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def normalise(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in BOOL_COLS:
        if c in df:
            df[c] = df[c].map(lambda v: pd.NA if v is None or (isinstance(v, float) and math.isnan(v)) else bool(v)
                              ).astype("boolean")
    for c in FLOAT_COLS:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    df["day"] = pd.to_datetime(df.day)
    df["family"] = df.model.replace(FAMILY)
    if "cost_basis" not in df:
        df["cost_basis"] = "cfd"                       # runs before 2026-11-13 were all CFD-costed
    return df


def _check(df: pd.DataFrame):
    missing = [c for c in REQUIRED if c not in df]
    if missing:
        raise ValueError(f"run is missing required columns: {missing}")
    if df.asset.nunique() > 1:
        raise ValueError(f"a run holds one asset, got {sorted(df.asset.unique())}")
    fams = set(df.model.replace(FAMILY))
    if len(fams) > 1:
        raise ValueError(f"a run holds one model family, got {sorted(fams)}")


def run_id(df: pd.DataFrame, start, end, commit: str, extras: bool) -> str:
    fam = df.model.replace(FAMILY).iloc[0]
    variants = "|".join(sorted(df.variant.unique()))
    basis = df.cost_basis.iloc[0] if "cost_basis" in df else "cfd"
    key = f"{fam}|{df.asset.iloc[0]}|{start}|{end}|{variants}|{commit}|{extras}" + ("" if basis == "cfd" else f"|{basis}")
    return f"{fam}-{df.asset.iloc[0]}-{start}-{end}-{hashlib.sha1(key.encode()).hexdigest()[:8]}"


def add_run(df: pd.DataFrame, start, end, commit: str | None = None, extras: bool = True,
            root: Path = STORE, replace: bool = False) -> str:
    if df.empty:
        raise ValueError("empty run")
    _check(df)
    commit = commit or git_commit()
    rid = run_id(df, start, end, commit, extras)
    path = Path(root) / f"{rid}.parquet"
    if path.exists() and not replace:
        raise FileExistsError(f"run {rid} already in the store (replace=True to overwrite)")
    out = normalise(df).assign(run_id=rid, commit=commit, extras=extras,
                               period_start=pd.Timestamp(start), period_end=pd.Timestamp(end),
                               added_at=pd.Timestamp.now(tz="UTC"))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path)
    return rid


def load(root: Path = STORE, traded_only: bool = False, **filters) -> pd.DataFrame:
    """All runs (or ``filters`` like asset="XAUUSD", family="mmxm", commit=...)."""
    files = sorted(Path(root).glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    for k, v in filters.items():
        df = df[df[k].isin(v if isinstance(v, (list, tuple, set)) else [v])]
    return df[df.status == "traded"] if traded_only else df


def runs(root: Path = STORE) -> pd.DataFrame:
    df = load(root)
    if df.empty:
        return df
    t = df[df.status == "traded"]
    info = df.groupby("run_id").agg(family=("family", "first"), asset=("asset", "first"),
                                    start=("period_start", "first"), end=("period_end", "first"),
                                    commit=("commit", "first"), extras=("extras", "first"), setups=("status", "size"))
    return info.join(t.groupby("run_id").r.agg(trades="size", exp_r="mean")).reset_index()


def clustered_se(r: pd.Series, day: pd.Series) -> float:
    """Standard error of the mean R, clustered by trading day.

    Trades on the same day share one tape (same bias call, same news, same trend), so they are not
    independent and the naive se = s/√n overstates confidence (orderflow.md §3: autocorrelation-robust
    statistics). With residual sums S_g per day and G days: var = G/(G−1) · Σ S_g² / n².
    Equals the naive se when every day has one trade."""
    r = pd.Series(r).reset_index(drop=True).astype(float)
    g = pd.Series(pd.to_datetime(day)).dt.normalize().reset_index(drop=True)
    n, groups = len(r), g.nunique()
    if n < 2 or groups < 2:
        return float("nan")
    s = (r - r.mean()).groupby(g).sum()
    return math.sqrt(groups / (groups - 1) * float((s ** 2).sum()) / n ** 2)


def leaderboard(df: pd.DataFrame, by: list[str], min_n: int = 30) -> pd.DataFrame:
    """Expectancy ± se, win rate with Wilson range and n per bucket of traded setups, best first.
    ``se_cl``/``z_cl``: se and z clustered by trading day (use these for decisions; ``se`` assumes independent
    trades). The ``early_r``/``late_r`` halves (by date, per bucket) show whether a bucket is stable."""
    t = df[df.status == "traded"]
    rows = []
    for key, g in t.groupby(by):
        n = len(g)
        if n < min_n:
            continue
        k = int(g.vote.fillna(False).astype(bool).sum())
        lo, hi = wilson(k, n)
        mid = g.day.min() + (g.day.max() - g.day.min()) / 2
        rows.append({**dict(zip(by, key if isinstance(key, tuple) else (key,))), "n": n, "win": k / n,
                     "win_lo": lo, "win_hi": hi, "exp_r": g.r.mean(),
                     "se": g.r.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan"),
                     "se_cl": (se_cl := clustered_se(g.r, g.day)),
                     "z_cl": g.r.mean() / se_cl if se_cl and se_cl == se_cl and se_cl > 0 else float("nan"),
                     "early_r": g[g.day <= mid].r.mean(), "late_r": g[g.day > mid].r.mean()})
    out = pd.DataFrame(rows)
    return out.sort_values("exp_r", ascending=False).reset_index(drop=True) if len(out) else out


def _period_from_name(path: Path) -> tuple[str, str]:
    parts = path.stem.split("-")
    dates = ["-".join(parts[i:i + 3]) for i in range(len(parts) - 2) if parts[i].isdigit() and len(parts[i]) == 4]
    if len(dates) < 2:
        raise ValueError(f"can't read start/end dates from {path.name}; pass --start/--end")
    return dates[0], dates[1]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.eval.store")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("tables", nargs="+", type=Path)
    a.add_argument("--start")
    a.add_argument("--end")
    a.add_argument("--commit")
    a.add_argument("--no-extras", action="store_true")
    a.add_argument("--replace", action="store_true")
    sub.add_parser("runs")
    b = sub.add_parser("board")
    b.add_argument("--by", nargs="+", default=["family", "window"])
    b.add_argument("--min-n", type=int, default=30)
    b.add_argument("--asset")
    b.add_argument("--family")
    b.add_argument("--commit", help="only runs made at this commit (don't mix rule versions)")
    b.add_argument("--cost", choices=("cfd", "futures"), help="only runs on this cost basis")
    b.add_argument("--start")
    b.add_argument("--end")
    args = ap.parse_args(argv)
    pd.set_option("display.width", 200)
    if args.cmd == "add":
        for p in args.tables:
            start, end = (args.start, args.end) if args.start else _period_from_name(p)
            df = pd.read_parquet(p)
            for asset, g in df.groupby("asset"):
                try:
                    print(add_run(g, start, end, args.commit, not args.no_extras, replace=args.replace))
                except FileExistsError as e:
                    print(f"skip: {e}")
    elif args.cmd == "runs":
        print(runs().to_string(index=False))
    else:
        filt = {k: v for k, v in (("asset", args.asset), ("family", args.family), ("commit", args.commit),
                                  ("cost_basis", args.cost)) if v}
        df = load(**filt)
        if args.start:
            df = df[df.day >= pd.Timestamp(args.start)]
        if args.end:
            df = df[df.day <= pd.Timestamp(args.end)]
        print(leaderboard(df, args.by, args.min_n).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
