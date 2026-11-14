"""Gap sweep — where each model loses its R, and which order-flow measure could speak to each gap.

    uv run python -m ict_engine.eval.gaps [--start 2022-01-03 --end 2024-06-28] [--cost cfd|futures]
    → prints and writes reports/gaps-<basis>.md (+ .parquet with one row per setup that reached the order stage)

Every setup that passed its gates and placed an order (traded, missed, not filled) gets one label from its 1m
path (all prices from the trade's own plan; no look-ahead is needed because this is after-the-fact review):

    win             TP1 before the stop
    missed          TP1 traded before the limit filled: the move left without us (entry too deep)
    not_filled      neither entry nor TP1 traded before the window closed
    near_miss       filled, came ≥ ``near`` of the way to TP1, then stopped (target / exit gap)
    stop_then_tp1   stopped, and TP1 traded later the same session (stop placement gap: the stop was in the way)
    fast_loss       stopped without ever reaching +0.5R (entry timing / direction gap)
    slow_loss       stopped after reaching +0.5R but < ``near`` of TP1
    time_exit       closed at the session end without stop or TP1

Each gap maps to a hypothesis an order-flow feed (CME TBBO: trades with aggressor side + top of book) could test;
see ``ORDERFLOW`` and references/orderflow.md §10–11. Selection period only (2022–24) unless told otherwise.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SESSION_END = "16:00"
LABELS = ("win", "missed", "not_filled", "near_miss", "stop_then_tp1", "fast_loss", "slow_loss", "time_exit")

# What order flow could say about each gap (hypotheses to pre-register once data exists, not results).
ORDERFLOW = {
    "missed": "Entry location. When signed volume (delta) at the trigger is strongly one-sided, enter at market / "
              "shallower instead of waiting for the limit (Harris ch.4: aggressive vs passive orders; OFI, Cont et al.).",
    "fast_loss": "Entry timing / direction. Require the trigger's order-flow imbalance (OFI, cumulative delta over the "
                 "reaction) to agree with the trade; a 1m FVG printed against the aggressor flow is a likely trap.",
    "stop_then_tp1": "Stop placement. Check whether stops sat where liquidity was taken: a burst of aggressive volume "
                     "through our stop with no follow-through (absorption; Bouchaud transient impact) → place stops "
                     "beyond that level or wait for the sweep to finish.",
    "near_miss": "Exit. Delta exhaustion / opposing absorption near the target → take TP1 earlier when flow fades "
                 "(López de Prado: exits change the shape, not the mean, so expect a small effect).",
    "slow_loss": "Trade management. Flow reversal after +0.5R (delta flips, spread widens) → move the stop or exit.",
    "time_exit": "Session flow. Low participation (volume / trade count) days → skip; a filter, not a signal.",
    "not_filled": "None directly; it costs nothing but opportunity.",
}


# --- pure pieces (unit-tested) ---------------------------------------------------------------------------

def path_stats(bars: pd.DataFrame, side: str, entry: float, stop: float, tp1: float,
               filled_at: pd.Timestamp, exit_at: pd.Timestamp, session_end: pd.Timestamp) -> dict:
    """MFE (in R and as a share of the way to TP1) between fill and exit, and whether TP1 traded after the exit
    but before ``session_end``."""
    long = side == "long"
    risk = abs(entry - stop)
    held = bars[(bars.index >= filled_at) & (bars.index <= exit_at)]
    after = bars[(bars.index > exit_at) & (bars.index < session_end)]
    if held.empty or risk <= 0:
        return {"mfe_r": np.nan, "mfe_frac": np.nan, "tp1_after": False, "mins_held": np.nan}
    best = held.high.max() - entry if long else entry - held.low.min()
    tp1_dist = abs(tp1 - entry)
    hit_after = bool(((after.high >= tp1) if long else (after.low <= tp1)).any()) if len(after) else False
    return {"mfe_r": float(best / risk), "mfe_frac": float(best / tp1_dist) if tp1_dist > 0 else np.nan,
            "tp1_after": hit_after, "mins_held": (exit_at - filled_at).total_seconds() / 60}


def label(status: str, exit_reason, vote, st: dict, near: float = 0.8) -> str:
    """One gap label per setup (see the module docstring)."""
    if status == "missed":
        return "missed"
    if status == "not_filled":
        return "not_filled"
    if bool(vote):
        return "win"
    if exit_reason == "time_exit":
        return "time_exit"
    if st.get("tp1_after"):
        return "stop_then_tp1"
    f, r = st.get("mfe_frac"), st.get("mfe_r")
    if f is not None and not pd.isna(f) and f >= near:
        return "near_miss"
    if r is not None and not pd.isna(r) and r < 0.5:
        return "fast_loss"
    return "slow_loss"


# --- sweep --------------------------------------------------------------------------------------------------

def _rows(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.status.isin(["traded", "missed", "not_filled"]) & df.entry.notna()].copy()


def annotate(df: pd.DataFrame, bars_by_asset: dict, near: float = 0.8) -> pd.DataFrame:
    """Add path stats + a ``gap`` label to every setup that reached the order stage."""
    t = _rows(df)
    out = []
    for asset, g in t.groupby("asset"):
        bars = bars_by_asset[asset]
        for i, r in g.iterrows():
            st = {}
            if r.status == "traded" and pd.notna(r.filled_at) and pd.notna(r.exit_at):
                end = pd.Timestamp(f"{pd.Timestamp(r.day):%Y-%m-%d} {SESSION_END}", tz="America/New_York")
                st = path_stats(bars, r.side, r.entry, r.stop, r.tp1, pd.Timestamp(r.filled_at),
                                pd.Timestamp(r.exit_at), end)
            out.append({"idx": i, **st, "gap": label(r.status, r.exit, r.vote, st, near)})
    a = pd.DataFrame(out).set_index("idx")
    return t.join(a)


def summary(t: pd.DataFrame) -> pd.DataFrame:
    """Per family: share of order-stage setups per gap label, and the R each loss label costs."""
    rows = []
    for fam, g in t.groupby("family"):
        traded = g[g.status == "traded"]
        rec = {"family": fam, "orders": len(g), "traded": len(traded),
               "exp_r": float(traded.r.mean()) if len(traded) else np.nan}
        for lab in LABELS:
            x = g[g.gap == lab]
            rec[f"{lab}_n"] = len(x)
            rec[f"{lab}_r"] = float(x.r.sum()) if lab not in ("missed", "not_filled") and len(x) else 0.0
        rows.append(rec)
    return pd.DataFrame(rows)


def render(s: pd.DataFrame, basis: str, start, end) -> str:
    lines = [f"# Gap sweep — {basis} costs, {start} → {end}", "",
             "Share of setups that placed an order, by what happened. `missed` = TP1 traded before our limit filled. "
             "R columns = total R the label cost (traded only).", "",
             "| model | orders | traded | exp R | " + " | ".join(LABELS) + " |",
             "|---|---|---|---|" + "---|" * len(LABELS)]
    for _, r in s.iterrows():
        cells = [f"{r[f'{lab}_n'] / r.orders:.0%}" + (f" ({r[f'{lab}_r']:+.0f}R)" if r[f'{lab}_r'] else "")
                 for lab in LABELS]
        lines.append(f"| {r.family} | {r.orders} | {r.traded} | {r.exp_r:+.3f} | " + " | ".join(cells) + " |")
    lines += ["", "## What order flow could test for each gap (hypotheses, not results)", ""]
    lines += [f"- **{k}**: {v}" for k, v in ORDERFLOW.items()]
    return "\n".join(lines) + "\n"


def main(argv=None):
    from ict_engine.eval import store
    from ict_engine.eval.backtest import load_range
    ap = argparse.ArgumentParser(prog="ict_engine.eval.gaps")
    ap.add_argument("--start", default="2022-01-03")
    ap.add_argument("--end", default="2024-06-28")
    ap.add_argument("--cost", choices=("cfd", "futures"), default="cfd")
    ap.add_argument("--near", type=float, default=0.8)
    a = ap.parse_args(argv)
    df = store.load()
    df = df[df["cost_basis"].fillna("cfd") == a.cost]
    df = store.latest(df)
    df = df[(pd.to_datetime(df.day) >= a.start) & (pd.to_datetime(df.day) <= a.end)]
    bars = {x: load_range(x, pd.Timestamp(a.start).date(), pd.Timestamp(a.end).date()) for x in df.asset.unique()}
    t = annotate(df, bars, a.near)
    s = summary(t)
    text = render(s, a.cost, a.start, a.end)
    out = ROOT / "reports" / f"gaps-{a.cost}"
    save = t.copy()
    for c in save.columns:
        if c.endswith("_at"):
            save[c] = pd.to_datetime(save[c], utc=True).dt.tz_convert("America/New_York")
        elif save[c].dtype == object and pd.to_numeric(save[c], errors="coerce").notna().sum() == save[c].notna().sum():
            save[c] = pd.to_numeric(save[c], errors="coerce")
        elif save[c].dtype == object:
            save[c] = save[c].map(lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else str(v))
    save.to_parquet(out.with_suffix(".parquet"))
    out.with_suffix(".md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
