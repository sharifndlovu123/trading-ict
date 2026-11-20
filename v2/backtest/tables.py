"""What the calls say, as tables, and one call as marks for the chart. The first pattern finder: it counts what
repeats and shows how many times each was seen. It proposes no rule. Design: the same document as ``run.py``.

Keeping the numbers honest (from the design):
  * every table is split by which was nearer, the target or the thing that undoes the call, because the nearer level
    usually goes first whatever a tool says;
  * a share is always of the calls that resolved one way or the other (true or undone), with the count beside it;
  * unresolved, open and same-candle calls are counted and shown, never folded into a share.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent / "out"
DONE = ("true", "undone")


def load(folder: Path = OUT) -> pd.DataFrame:
    files = sorted(folder.glob("calls-*.parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True) if files else pd.DataFrame()


def count(df: pd.DataFrame, by: list[str]) -> list[dict]:
    """One row per group: how many calls, how each ended, and the share that came true among those that resolved."""
    if df.empty:
        return []
    rows = []
    for key, g in df.groupby(by, dropna=False, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        done = g[g["outcome"].isin(DONE)]
        won = int((done["outcome"] == "true").sum())
        rows.append({**{b: (None if pd.isna(k) else k.item() if hasattr(k, "item") else k) for b, k in zip(by, key)}, "calls": len(g), "true": won,
                     "undone": len(done) - won, "other": len(g) - len(done),
                     "true_share": round(won / len(done), 3) if len(done) else None,
                     "median_hours": None if done["hours"].dropna().empty else round(float(done["hours"].median()), 1)})
    return rows


def nearer_side(df: pd.DataFrame) -> list[dict]:
    """For liquidity calls where liquidity rested on both sides: how often the NEARER side went first, when the nearer
    side was the bias's side and when it was the other side. The difference between the two is what the bias adds."""
    rows = []
    liq = df[(df["kind"] == "liquidity") & df["outcome"].isin(DONE) & df["sellside"].notna() & df["buyside"].notna()] if not df.empty else df
    if liq.empty:
        return rows
    for tf, g in liq.groupby("tf"):
        with_bias, against = g[g["nearer"] == "target"], g[g["nearer"] == "undo"]
        rows.append({"tf": tf,
                     "nearer_was_bias_side": len(with_bias), "nearer_went_first_share": round(float((with_bias["outcome"] == "true").mean()), 3) if len(with_bias) else None,
                     "nearer_was_other_side": len(against), "nearer_went_first_share_other": round(float((against["outcome"] == "undone").mean()), 3) if len(against) else None})
    return rows


def picture(df: pd.DataFrame, order: list[str]) -> list[dict]:
    """One row per timeframe, highest first: for each kind of call, how often it came true when the target was the
    nearer level and when it was the farther one; and what the bias adds to a liquidity call. This is the table he
    asked to be noticed: "the higher timeframes have higher percentages than below… it's very important." """
    if df.empty:
        return []
    adds, rows = {r["tf"]: r for r in nearer_side(df)}, []
    for tf in [t for t in order if t in set(df["tf"])]:
        g = df[df["tf"] == tf]
        row = {"tf": tf, "calls": len(g)}
        for kind in ("liquidity", "bias", "imbalance"):
            for nearer in ("target", "undo"):
                d = g[(g["kind"] == kind) & (g["nearer"] == nearer) & g["outcome"].isin(DONE)]
                row[f"{kind}_{nearer}"] = round(float((d["outcome"] == "true").mean()), 3) if len(d) else None
                row[f"{kind}_{nearer}_n"] = len(d)
        a = adds.get(tf, {})
        with_bias, other = a.get("nearer_went_first_share"), a.get("nearer_went_first_share_other")
        row.update(bias_side=with_bias, bias_side_n=a.get("nearer_was_bias_side", 0), other_side=other, other_side_n=a.get("nearer_was_other_side", 0),
                   bias_adds=None if with_bias is None or other is None else round(with_bias - other, 3))
        rows.append(row)
    return rows


def tables(df: pd.DataFrame, order: list[str] | None = None) -> dict:
    if df.empty:
        return {"calls": 0}
    return {"calls": len(df), "instruments": sorted(df["asset"].unique()), "years": sorted(int(y) for y in df["year"].unique()),
            "outcomes": {k: int(v) for k, v in df["outcome"].value_counts().items()},
            "picture": picture(df, order or sorted(df["tf"].unique())),
            "bias_adds_by_year": [{"year": int(y), **{r["tf"]: r["bias_adds"] for r in picture(g, order or sorted(df["tf"].unique()))},
                                   **{r["tf"] + "_n": r["bias_side_n"] + r["other_side_n"] for r in picture(g, order or sorted(df["tf"].unique()))}}
                                  for y, g in df.groupby("year")],
            "by_kind": count(df, ["kind", "tf", "nearer"]),
            "what_the_bias_adds": nearer_side(df),
            "with_the_timeframe_above": count(df[df["with_above"].notna()], ["kind", "tf", "with_above", "nearer"]),
            "made_in": count(df, ["kind", "made_in", "nearer"]),
            "resolved_hour": count(df[df["tf"].isin(["1h", "4h"]) & df["resolved_hour"].notna()], ["resolved_hour"]),
            "by_year": count(df, ["kind", "year", "nearer"]),
            "by_instrument": count(df, ["kind", "asset", "nearer"])}


def pick(df: pd.DataFrame, limit: int = 60, **want) -> list[dict]:
    """Calls to look at, newest first, narrowed by any of: asset, tf, kind, outcome, nearer."""
    for k, v in want.items():
        if v and k in df.columns:
            df = df[df[k].astype(str) == str(v)]
    cols = ["id", "asset", "tf", "kind", "moment", "side", "nearer", "outcome", "hours", "made_in"]
    return json.loads(df.sort_values("moment", ascending=False).head(limit)[cols].to_json(orient="records"))


def call_marks(row: dict) -> dict:
    """One call as marks for the chart, as the tools saw things at that moment: the bias's two levels, the liquidity
    each side, the imbalance, and which of them the call was about."""
    tf, t0, marks = row["tf"], int(row["moment"]), []

    def level(kind, price):
        if price is not None and not pd.isna(price):
            marks.append({"shape": "level", "kind": kind, "tf": tf, "price": float(price), "t0": t0 - 40 * 86400 if tf in ("1M", "1W") else t0 - 5 * 86400, "t1": None})

    level("level behind", row["behind"])
    level("level ahead", row["ahead"])
    level("buyside", row["buyside"])
    level("sellside", row["sellside"])
    gap = json.loads(row["imbalance"]) if isinstance(row.get("imbalance"), str) else None
    if gap:
        marks.append({"shape": "zone", "kind": gap[2] if gap[2] in ("BISI", "SIBI") else "VI", "tf": tf, "bottom": gap[0], "top": gap[1], "t0": t0 - 5 * 86400, "t1": None})
    marks.append({"shape": "vline", "kind": "→ bull" if row["side"] == "bull" else "→ bear", "tf": tf, "t0": t0, "t1": t0})
    names = {"liquidity": "buyside" if row["side"] == "bull" else "sellside", "bias": "level ahead", "imbalance": "the imbalance"}
    ended = {"true": "It came true", "undone": "It was undone", "unresolved": "It was left unresolved", "open": "It is still open",
             "same candle": "Both were reached inside one candle, so the order is not known"}[row["outcome"]]
    took = "" if row.get("hours") is None or pd.isna(row["hours"]) else f" after {row['hours']:.0f} hours"
    return {"asset": row["asset"], "tf": tf, "moment": t0, "marks": marks, "bias": {tf: row["side"]},
            "interesting": [f"A call from the tools backtest, made at this moment on the {tf}: with the {tf} {row['side']}, price might draw to [{names[row['kind']]} {tf}]." if row["kind"] != "imbalance"
                            else f"A call from the tools backtest, made at this moment on the {tf}: with the {tf} {row['side']}, price might reach the imbalance in its direction.",
                            "Step the replay forward to see what happened."],
            "considering": [f"{ended}{took}.", "Nearer at the time: " + {"target": "the target", "undo": "what would undo it", "level": "neither", None: "nothing to undo it"}[row.get("nearer")] + "."]}
