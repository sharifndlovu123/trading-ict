"""Post-analysis — what a model did well, what it got wrong, and where it works.

    uv run python -m ict_engine.eval.review reports/backtest-US100-*.parquet [more.parquet ...]
    → prints the review and writes reports/review-<stem>.md

Reads backtest tables (``ict_engine.eval.backtest``). Three parts:

1. **Diagnosis** (per losing trade): which single factor most likely caused the
   loss, judged with hindsight + one-factor counterfactuals —
       bias_wrong      the day ran the opposite side (PDH/PDL) first
       wrong_side      the mirrored trade at the same entry would have won
       stop_too_tight  a 1.5× wider stop would have reached TP1
       target_too_far  TP1 at 1R would have been hit before the stop
       ambiguous       stop and TP1 inside one 1m bar (counted as a loss)
       time_exit       closed at 16:00 without stop or TP1
       unexplained     none of the above — the setup simply failed
   A loss can have several causes; all are counted.
2. **Gate value**: for every gate, how the setups it blocked would have done
   (shadow results) vs the trades that passed. A gate whose blocked setups do
   *better* than the traded ones is filtering out winners.
3. **Buckets and tips**: expectancy (R) and win rate (Wilson 95%) per bucket
   (window, weekday, hour, side, quarter, bias agreement, liquidity type, TP1
   kind…), and a tip only when a bucket differs from the rest by |z| ≥ 2 with
   at least ``min_n`` trades on both sides **and** the same sign in both halves
   of the date range (an early/late split — a pattern that flips is noise).

Hindsight columns are for judging decisions only; nothing here feeds back into
a gate automatically. Tips are hypotheses to test as new variants.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from ict_engine.eval.bias import wilson

ROOT = Path(__file__).resolve().parents[2]
CAUSES = ("bias_wrong", "wrong_side", "stop_too_tight", "target_too_far", "ambiguous", "time_exit", "unexplained")
DIMENSIONS = ("window", "weekday", "hour", "side", "quarter", "bias_agrees", "liquidity_kind", "liquidity",
              "tp1_kind", "poi_kind", "asset")


# --- preparation --------------------------------------------------------------

def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived bucket columns used by every part."""
    df = df.copy()
    want = df.side.map({"long": "bull", "short": "bear"})
    df["bias_agrees"] = (df.bias == want).map({True: "with bias", False: "against/neutral"})
    df["tp1_kind"] = df.tp1_name.fillna("none").str.replace(r"^\d+m ", "", regex=True)
    df["poi_kind"] = df.poi.fillna("none").str.extract(r"^(swept \w+|\w+ FVG)", expand=False).fillna("none")
    df["half"] = (df.day > df.day.min() + (df.day.max() - df.day.min()) / 2).map({False: "early", True: "late"})
    return df


def trades(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.status == "traded"]


# --- 1. diagnosis -------------------------------------------------------------

def _true(v) -> bool:
    """True only for a real True (column values may be numpy bools, None or NaN)."""
    return v is not None and not (isinstance(v, float) and math.isnan(v)) and bool(v)


def causes(row) -> list[str]:
    """Likely causes of one losing trade (empty for winners)."""
    if _true(row.vote) or row.r is None or (isinstance(row.r, float) and math.isnan(row.r)):
        return []
    out = []
    if row.exit == "time_exit":
        out.append("time_exit")
    if row.side == "long" and row.outcome == "bear_hit" or row.side == "short" and row.outcome == "bull_hit":
        out.append("bias_wrong")
    if _true(row.get("cf_flip_vote")):
        out.append("wrong_side")
    if _true(row.get("cf_wide_stop_vote")):
        out.append("stop_too_tight")
    if _true(row.get("cf_tp1_1r_vote")):
        out.append("target_too_far")
    if _true(row.ambiguous):
        out.append("ambiguous")
    return out or ["unexplained"]


def diagnose(df: pd.DataFrame, by: str | None = "window") -> pd.DataFrame:
    """Share of losing trades with each cause, overall or per ``by`` bucket."""
    t = trades(df)
    losers = t[~t.vote.map(_true)]
    if losers.empty:
        return pd.DataFrame()
    tags = losers.apply(causes, axis=1)
    rows = []
    groups = [("all", losers.index)] if by is None else list(losers.groupby(by).groups.items())
    for key, idx in groups:
        n = len(idx)
        rec = {by or "bucket": key, "losses": n}
        for c in CAUSES:
            rec[c] = sum(c in tags[i] for i in idx) / n
        rows.append(rec)
    return pd.DataFrame(rows)


# --- 2. gate value ------------------------------------------------------------

def gate_value(df: pd.DataFrame) -> pd.DataFrame:
    """For each gate: blocked setups' shadow results vs the traded setups' real results."""
    t = trades(df)
    rows = [_stats("traded (passed all)", t.r, t.vote)]
    blocked = df[df.failed_gate.notna() & df.shadow_r.notna()]
    for gate, g in blocked.groupby("failed_gate"):
        rows.append(_stats(f"blocked@{gate} (shadow)", g.shadow_r, g.shadow_vote))
    out = pd.DataFrame(rows)
    if len(t):
        out["vs_traded_r"] = out.exp_r - out.exp_r.iloc[0]
    return out


# --- 3. buckets and tips ------------------------------------------------------

def _stats(name, r: pd.Series, vote: pd.Series) -> dict:
    r, vote = r.dropna().astype(float), vote.dropna().astype(bool)
    n, k = len(r), int(vote.sum())
    lo, hi = wilson(k, len(vote)) if len(vote) else (0.0, 0.0)
    sd = float(r.std(ddof=1)) if n > 1 else float("nan")
    return {"bucket": name, "n": n, "votes": k, "win": k / len(vote) if len(vote) else float("nan"),
            "win_lo": lo, "win_hi": hi, "exp_r": float(r.mean()) if n else float("nan"),
            "exp_se": sd / math.sqrt(n) if n > 1 else float("nan")}


def buckets(df: pd.DataFrame, by: str) -> pd.DataFrame:
    t = trades(df)
    rows = []
    for key, g in t.groupby(by):
        s = _stats(str(key), g.r, g.vote)
        halves = g.groupby("half").r.mean()
        s["early_r"], s["late_r"] = halves.get("early", float("nan")), halves.get("late", float("nan"))
        rows.append(s)
    return pd.DataFrame(rows).sort_values("exp_r", ascending=False) if rows else pd.DataFrame()


def tips(df: pd.DataFrame, dims=DIMENSIONS, min_n: int = 20, z_min: float = 2.0) -> list[dict]:
    """Buckets whose expectancy differs from the rest of the model's trades — evidence, not hunches."""
    t = trades(df)
    out = []
    for model, m in t.groupby("model"):
        for dim in dims:
            if dim not in m:
                continue
            for key, g in m.groupby(dim):
                rest = m[m[dim] != key]
                if len(g) < min_n or len(rest) < min_n:
                    continue
                se = math.sqrt(g.r.var(ddof=1) / len(g) + rest.r.var(ddof=1) / len(rest))
                if not se:
                    continue
                diff = g.r.mean() - rest.r.mean()
                z = diff / se
                # stability: bucket minus rest has the same sign in both halves of the date range
                signs = []
                for h in ("early", "late"):
                    gh, rh = g[g.half == h], rest[rest.half == h]
                    if len(gh) and len(rh):
                        signs.append(math.copysign(1, gh.r.mean() - rh.r.mean()))
                stable = len(signs) == 2 and signs[0] == signs[1]
                if abs(z) >= z_min and stable:
                    s = _stats(key, g.r, g.vote)
                    out.append({"model": model, "dim": dim, "bucket": key, "n": len(g), "exp_r": g.r.mean(),
                                "rest_r": rest.r.mean(), "z": z, "win": s["win"], "win_lo": s["win_lo"],
                                "win_hi": s["win_hi"],
                                "text": f"{model}: {dim}={key} expectancy {g.r.mean():+.2f}R vs {rest.r.mean():+.2f}R "
                                        f"for the rest (n={len(g)}, win {s['win']:.0%} [{s['win_lo']:.0%}–{s['win_hi']:.0%}], "
                                        f"z={z:+.1f}; holds in both halves)"})
    return sorted(out, key=lambda x: -abs(x["z"]))


# --- report -------------------------------------------------------------------

PCT = ("win", "win_lo", "win_hi")
R_COLS = ("exp_r", "exp_se", "early_r", "late_r", "vs_traded_r")
COUNTS = ("n", "votes", "losses", "setups")


def _fmt(df: pd.DataFrame) -> str:
    if df.empty:
        return "_(none)_"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if c in PCT or c in CAUSES:
                cells.append("" if pd.isna(v) else f"{v:.0%}")
            elif c in R_COLS:
                cells.append("" if pd.isna(v) else f"{v:+.3f}")
            elif c in COUNTS:
                cells.append(str(int(v)))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def report(df: pd.DataFrame, title: str = "") -> str:
    df = prepare(df)
    t = trades(df)
    overall = pd.DataFrame([_stats("all trades", t.r, t.vote)])
    status = df.status.value_counts().rename_axis("status").reset_index(name="setups")
    parts = [f"# Review {title}".rstrip(),
             f"{df.day.min():%Y-%m-%d} → {df.day.max():%Y-%m-%d} · models: {', '.join(sorted(df.model.unique()))} · "
             f"variants: {', '.join(sorted(df.variant.unique()))}",
             "## Overall", _fmt(overall), _fmt(status),
             "## Tips (|z| ≥ 2, n ≥ 20 both sides, same sign early and late)",
             "\n".join(f"- {x['text']}" for x in tips(df)) or "_No bucket passes the evidence bar yet._",
             "## What went wrong — causes of losing trades (share of losses; several per loss allowed)",
             _fmt(diagnose(df, None)), _fmt(diagnose(df, "window")),
             "## Gate value — what each gate blocked (shadow) vs what it let through",
             _fmt(gate_value(df))]
    for dim in ("window", "weekday", "hour", "side", "bias_agrees", "tp1_kind", "liquidity_kind"):
        parts += [f"## By {dim}", _fmt(buckets(df, dim))]
    return "\n\n".join(parts) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.eval.review")
    ap.add_argument("tables", nargs="+", type=Path)
    a = ap.parse_args(argv)
    df = pd.concat([pd.read_parquet(p) for p in a.tables], ignore_index=True)
    stem = a.tables[0].stem.replace("backtest-", "") + (f"+{len(a.tables) - 1}" if len(a.tables) > 1 else "")
    text = report(df, stem)
    out = ROOT / "reports" / f"review-{stem}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(text)
    print(text)
    print(out)


if __name__ == "__main__":
    main()
