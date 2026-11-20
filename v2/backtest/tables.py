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
            "merged": count(df[df["kind"] == "merged"], ["tf", "merge", "nearer"]) if "merge" in df.columns else [],
            "merged_whose": count(df[df["kind"] == "merged"], ["merge", "whose", "nearer"]) if "merge" in df.columns else [],
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
    cols = [c for c in ["id", "asset", "tf", "kind", "moment", "side", "nearer", "outcome", "hours", "made_in", "merge", "what", "whose_tf"] if c in df.columns]
    return json.loads(df.sort_values("moment", ascending=False).head(limit)[cols].to_json(orient="records"))


TRADED_INDICES = ("US100", "US500", "US30")       # his: "when I say indices, stick to 100, 500 and 30"
REVIEWS = Path(__file__).resolve().parent / "reviews.jsonl"       # what he says about a call: his words, only ever added to
VERDICTS = ("right", "wrong", "not sure")


def check(df: pd.DataFrame, limit: int = 10, assets: tuple = TRADED_INDICES, tfs: tuple = ("1D", "4h")) -> list[dict]:
    """A short list for him to go through on the chart: merged calls where the two timeframes DISAGREED (``momentum``
    and ``key area``), on the indices he trades. He: "review all those bias calls with the momentum and key areas…
    max 10, and then if it's too far off we will have to do more later on."

    Mine: half of each; of each half, more that were undone with the target nearer (the clear misses) than that came
    true; newest first; no two from the same instrument within a fortnight, so one stretch of market is not seen ten
    times; the two higher timeframes that have enough of both."""
    if df.empty or "merge" not in df.columns:
        return []
    pool = df[(df["kind"] == "merged") & df["asset"].isin(assets) & df["tf"].isin(tfs)].sort_values(["moment", "id"], ascending=False)
    each, out = limit // 2, []
    for how in ("momentum", "key area"):
        misses = pool[(pool["merge"] == how) & (pool["outcome"] == "undone") & (pool["nearer"] == "target")]
        hits = pool[(pool["merge"] == how) & (pool["outcome"] == "true")]
        for part, want in ((misses, each - each // 3), (hits, each // 3)):
            got = 0
            for r in part.to_dict("records"):
                if got == want:
                    break
                if any(o["asset"] == r["asset"] and abs(o["moment"] - r["moment"]) < 14 * 86400 for o in out):
                    continue
                if sum(o["asset"] == r["asset"] for o in out) >= -(-limit // len(assets)):
                    continue
                out.append(r)
                got += 1
    cols = ["id", "asset", "tf", "moment", "side", "own_side", "above", "merge", "what", "whose_tf", "nearer", "outcome", "hours"]
    return json.loads(pd.DataFrame(out)[[c for c in cols if c in pool.columns]].to_json(orient="records")) if out else []


def add_review(path: Path, call_id: str, verdict: str, text: str, now: float) -> dict:
    """He says whether the read was right, and what it missed. Appended; nothing is ever rewritten."""
    if verdict not in VERDICTS:
        raise ValueError("the verdict is right, wrong or not sure")
    row = {"saved": int(now), "id": str(call_id)[:120], "verdict": verdict, "text": str(text)[:4000]}
    with path.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def reviews(path: Path) -> dict:
    """The latest thing he said about each call, by call id."""
    out = {}
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
                out[r["id"]] = r
            except Exception:
                continue
    return out


def ladder_marks(ladder: dict, t0: int) -> tuple[list, dict, list]:
    """What EVERY timeframe was reading at the moment of a call (he: "we would need to see what the higher frames are
    reading at least, because we don't see it"): each one's bias, its two levels, the nearest liquidity each side and
    the nearest imbalance each side, as marks labelled with their timeframe, and one line of words per timeframe,
    highest first. ``ladder``: ``{tf: read or None}``, highest first.

    Every mark starts at the candle it belongs to (the candle that made the high, the middle candle of the gap, the
    candle of the break) and ends at the moment of the call: nothing floats where no candle made it."""
    marks, bias, lines = [], {}, []
    for tf, r in ladder.items():
        if r is None:
            lines.append(f"{tf}: no bias read yet.")
            continue
        bias[tf] = r["side"]
        when = r.get("when") or {}
        near = [f"[{k} {tf}]" for k in ("buyside", "sellside") if r.get(k) is not None]
        gaps = {tuple(r[k]) + (when.get(k),) for k in ("imbalance_above", "imbalance_below", "inside") if r.get(k)}
        near += sorted({f"[{g[2]} {tf}]" for g in gaps})
        lines.append(f"{tf}: {r['side']}." + (" Nearest from price: " + ", ".join(near) + "." if near else " Nothing resting nearby.")
                     + (" Price is inside an imbalance of this timeframe." if r.get("inside") else ""))
        for kind in ("level behind", "level ahead", "buyside", "sellside"):
            key = kind.replace("level ", "")
            if r.get(key) is not None and when.get(key) is not None:
                marks.append({"shape": "level", "kind": kind, "tf": tf, "price": float(r[key]), "t0": int(when[key]), "t1": t0})
        for bottom, top, kind, made in sorted(gaps, key=lambda g: g[0]):
            if made is not None:
                marks.append({"shape": "zone", "kind": kind if kind in ("BISI", "SIBI") else "VI", "tf": tf, "bottom": bottom, "top": top, "t0": int(made), "t1": t0})
    return marks, bias, lines


def call_marks(row: dict, ladder: dict | None = None) -> dict:
    """One call as marks for the chart, as the tools saw things at that moment: the bias's two levels, the liquidity
    each side, the imbalance, and which of them the call was about. With ``ladder`` (every timeframe's read at that
    moment), what the other timeframes were reading is drawn and written too."""
    tf, t0, marks = row["tf"], int(row["moment"]), []
    others, all_bias, lines = ladder_marks(ladder, t0) if ladder else ([], {}, [])
    own = not ladder or ladder.get(tf) is None        # with the ladder, the call's own timeframe is drawn from it too (it knows the candle of each mark)

    def level(kind, price):
        if own and price is not None and not pd.isna(price):
            marks.append({"shape": "level", "kind": kind, "tf": tf, "price": float(price), "t0": t0 - 40 * 86400 if tf in ("1M", "1W") else t0 - 5 * 86400, "t1": None})

    level("level behind", row["behind"])
    level("level ahead", row["ahead"])
    level("buyside", row["buyside"])
    level("sellside", row["sellside"])
    is_merged = row["kind"] == "merged"
    at_tf = row.get("whose_tf") if is_merged and isinstance(row.get("whose_tf"), str) else tf       # a merged call's target may belong to the timeframe above
    gap = json.loads(row["imbalance"]) if isinstance(row.get("imbalance"), str) else None
    if gap and own:
        marks.append({"shape": "zone", "kind": gap[2] if gap[2] in ("BISI", "SIBI") else "VI", "tf": at_tf, "bottom": gap[0], "top": gap[1], "t0": t0 - 5 * 86400, "t1": None})
    elif is_merged and at_tf != tf and own:
        marks.append({"shape": "level", "kind": row["what"], "tf": at_tf, "price": float(row["target"]), "t0": t0 - 40 * 86400, "t1": None})
    marks.append({"shape": "vline", "kind": "→ bull" if row["side"] == "bull" else "→ bear", "tf": tf, "t0": t0, "t1": t0})
    names = {"liquidity": "buyside" if row["side"] == "bull" else "sellside", "bias": "level ahead", "imbalance": "the imbalance"}
    how = {"agree": f"the {tf} and the timeframe above agree ({row['side']})", "momentum": f"the {tf} is {row['side']} against the timeframe above: its momentum is followed",
           "key area": f"the timeframe above is {row['side']} and price is inside its imbalance, though the {tf} is against it"}.get(row.get("merge"))
    ended = {"true": "It came true", "undone": "It was undone", "unresolved": "It was left unresolved", "open": "It is still open",
             "same candle": "Both were reached inside one candle, so the order is not known"}[row["outcome"]]
    took = "" if row.get("hours") is None or pd.isna(row["hours"]) else f" after {row['hours']:.0f} hours"
    marks += others
    return {"asset": row["asset"], "tf": tf, "moment": t0, "marks": marks, "bias": all_bias or {tf: row["side"]},
            "ladder": lines,
            "interesting": [f"A merged call from the tools backtest, made at this moment: {how}. Nearest from price now: [{row['what']} {at_tf}]; price might draw to it." if is_merged
                            else f"A call from the tools backtest, made at this moment on the {tf}: with the {tf} {row['side']}, price might draw to [{names[row['kind']]} {tf}]." if row["kind"] != "imbalance"
                            else f"A call from the tools backtest, made at this moment on the {tf}: with the {tf} {row['side']}, price might reach the imbalance in its direction.",
                            *(["What each timeframe was reading at that moment, top to bottom:"] + lines if lines else []),
                            "Step the replay forward to see what happened."],
            "considering": [f"{ended}{took}.", "Nearer at the time: " + {"target": "the target", "undo": "what would undo it", "level": "neither", None: "nothing to undo it"}[row.get("nearer")] + "."]}
