"""PD-array audit: are the engine's arrays found correctly, and are they the ones a trader would use?

Three checks, from mechanical to judgement:
  1. definition   every area on the liquidity map is re-derived from that timeframe's own candles (the FVG's three
                  candles, the IFVG's close through, the OB / breaker candle) — edges must match.
  2. timing/state every area was known before the moment (formed and, for an IFVG, inverted by a close at or before
                  it); nothing on the map comes from the future.
  3. agreement    every zone Sharif drew in a review page (FVG / gap / IFVG / order block / breaker, with its timeframe,
                  at that review's moment) is looked up among the engine's arrays: found on the same TF and kind
                  (match / partial), found on another TF or as another kind, found by the detector but left off the
                  map (a usage filter), or missing (a detection gap). His marks are the reference for "correct".

    uv run python research/scripts/pd_audit.py [--sources topdown,liqmap,reentry,plans,trades] [--limit 0] \
        [--out research/pd-audit/<date>.md]

Read-only on reports/reviews/*.jsonl. In-sample review moments only (the pages are in-sample by construction).
"""
from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path

import pandas as pd

NY = "America/New_York"
SOURCES = ("topdown", "liqmap", "reentry", "plans", "trades")
KIND = {"fvg": "fvg", "gap": "fvg", "ifvg": "ifvg", "order block": "ob", "ob": "ob", "breaker": "breaker"}
ENGINE_FAMILY = {"fvg": {"fvg", "vi"}, "ifvg": {"ifvg"}, "ob": {"ob"}, "breaker": {"breaker", "mitigation"}}
WINDOW = {"5m": timedelta(days=7), "15m": timedelta(days=20), "1h": timedelta(days=60), "4h": timedelta(days=200),
          "1d": timedelta(days=800), "1w": timedelta(days=2600)}
TF_SEC = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800}


# ------------------------------------------------------------------------------------------------------- the marks

def _wall(t) -> pd.Timestamp:
    return pd.Timestamp(int(t), unit="s").tz_localize(NY)


def moment_of(rec: dict) -> pd.Timestamp | None:
    """When the review was judged: where watch mode stopped, else the time in the item id (…-YYYYMMDD-HHMM)."""
    if rec.get("watched_to"):
        return _wall(rec["watched_to"])
    parts = rec["id"].split("-")
    for i in range(len(parts) - 1):
        if len(parts[i]) == 8 and parts[i].isdigit() and len(parts[i + 1]) == 4 and parts[i + 1].isdigit():
            return pd.Timestamp(f"{parts[i]} {parts[i + 1]}", tz=NY)
    for p in parts:
        if len(p) == 8 and p.isdigit():
            return pd.Timestamp(f"{p} 08:30", tz=NY)
    return None


def asset_of(rec: dict) -> str | None:
    if rec.get("asset"):
        return rec["asset"]
    for p in rec["id"].split("-"):
        if p in ("US100", "US500", "US30", "XAUUSD", "XAGUSD", "DXY", "EURUSD"):
            return p
    return None


def load_marks(sources=SOURCES, root: Path = Path("reports/reviews")) -> list[dict]:
    out = []
    for s in sources:
        f = root / f"{s}.jsonl"
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            at, asset = moment_of(rec), asset_of(rec)
            if at is None or asset is None:
                continue
            for key in ("added", "marks", "mine"):
                for m in rec.get(key) or []:
                    if not isinstance(m, dict) or m.get("shape") != "zone":
                        continue
                    k = KIND.get(str(m.get("kind", "")).lower())
                    if not k or m.get("tf") not in TF_SEC or m.get("top") is None:
                        continue
                    out.append({"source": s, "id": rec["id"], "asset": asset, "at": at, "tf": m["tf"], "kind": k,
                                "drawn": m.get("kind"), "top": float(max(m["top"], m["bottom"])),
                                "bottom": float(min(m["top"], m["bottom"])),
                                "t0": _wall(m["t0"]) if m.get("t0") else None})
    # the same zone saved twice (re-saves) counts once
    seen, uniq = set(), []
    for m in out:
        key = (m["id"], m["tf"], m["kind"], round(m["top"], 2), round(m["bottom"], 2))
        if key not in seen:
            seen.add(key); uniq.append(m)
    return uniq


# ------------------------------------------------------------------------------------------------- engine arrays

def frames(bars: pd.DataFrame, at: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """Closed candles per timeframe before ``at``, built the engine's way (NY sessions for D, Monday weeks for W)."""
    from ict_engine.concepts.bars import resample
    from ict_engine.concepts.liquidity_map import _daily, weekly
    out = {}
    for tf, span in WINDOW.items():
        h = bars[(bars.index >= at - span) & (bars.index < at)]
        if h.empty:
            continue
        if tf == "1d":
            f = _daily(h)
        elif tf == "1w":
            f = weekly(_daily(h))
        else:
            f = resample(h, tf)
            f = f.assign(close_ts=f["close_ts"] + pd.Timedelta(minutes=1))
        out[tf] = f[f["close_ts"] <= at]
    return out


def engine_arrays(bars: pd.DataFrame, at: pd.Timestamp, fr: dict | None = None) -> list[dict]:
    """Every PD array the detectors find per timeframe, known by ``at`` (event ``ts`` ≤ at)."""
    from ict_engine.concepts.events import breaker_blocks, fvgs, inversions, order_blocks, volume_imbalances
    fr = fr or frames(bars, at)
    out = []
    for tf, f in fr.items():
        if len(f) < 5:
            continue
        gaps = fvgs(f, tf)
        hist = bars[(bars.index >= f.index[0]) & (bars.index < at)]
        inv = inversions(gaps, hist, tf_bars={tf: f} if tf in ("1d", "1w") else None)
        evs = gaps + volume_imbalances(f, tf) + inv + order_blocks(f, tf, confirm="open", single=True) + breaker_blocks(f, tf)
        for e in evs:
            if e.ts is None or pd.Timestamp(e.ts) > at:
                continue
            out.append({"tf": tf, "kind": e.kind, "dir": e.direction, "top": float(e.top), "bottom": float(e.bottom),
                         "origin": pd.Timestamp(e.origin_ts), "known": pd.Timestamp(e.ts)})
    return out


def iou(a_top, a_bot, b_top, b_bot) -> float:
    inter = max(0.0, min(a_top, b_top) - max(a_bot, b_bot))
    union = max(a_top, b_top) - min(a_bot, b_bot)
    return inter / union if union > 0 else 0.0


NEAR_BARS = 5          # the engine's array must form within this many candles of where he anchored the zone


def judge(mark: dict, arrays: list[dict], map_areas: list[dict]) -> dict:
    """The verdict for one drawn zone against the engine's arrays at the same moment. When his drawing has a time
    anchor (its left edge, t0), an array only counts if it formed within NEAR_BARS candles of it: the same price from
    a candle years earlier is a coincidence, not the array he drew ("same price, other candle")."""
    fam = ENGINE_FAMILY[mark["kind"]]
    t0 = mark.get("t0")
    near = lambda a: t0 is None or abs((a["origin"] - t0).total_seconds()) <= NEAR_BARS * TF_SEC[a["tf"]]
    def best(pred):
        c = [(iou(mark["top"], mark["bottom"], a["top"], a["bottom"]), a) for a in arrays if pred(a) and near(a)]
        c = [x for x in c if x[0] > 0]
        return max(c, key=lambda x: x[0]) if c else (0.0, None)
    s_same, a_same = best(lambda a: a["tf"] == mark["tf"] and a["kind"] in fam)
    s_tf, a_tf = best(lambda a: a["tf"] != mark["tf"] and a["kind"] in fam)
    s_kind, a_kind = best(lambda a: a["tf"] == mark["tf"] and a["kind"] not in fam)
    if s_same >= 0.5:
        v, s, a = "match", s_same, a_same
    elif s_same >= 0.2:
        v, s, a = "partial", s_same, a_same
    elif s_tf >= 0.5:
        v, s, a = "other TF", s_tf, a_tf
    elif s_kind >= 0.5:
        v, s, a = "other kind", s_kind, a_kind
    else:
        v, s, a = "missing", max(s_same, s_tf, s_kind), a_same or a_tf or a_kind
        if t0 is not None:                                          # is there one at that price, just another candle?
            far = [(iou(mark["top"], mark["bottom"], x["top"], x["bottom"]), x) for x in arrays
                   if x["tf"] == mark["tf"] and x["kind"] in fam]
            far = [y for y in far if y[0] >= 0.5]
            if far:
                v, (s, a) = "same price, other candle", max(far, key=lambda y: y[0])
    on_map = any(iou(mark["top"], mark["bottom"], m["top"], m["bottom"]) >= 0.3 for m in map_areas)
    off = None
    if a is not None and mark.get("t0") is not None:
        off = round((a["origin"] - mark["t0"]).total_seconds() / TF_SEC[a["tf"]], 1)
    return {"verdict": v, "iou": round(s, 2), "engine": a, "on_map": on_map, "bars_from_his_anchor": off}


# ------------------------------------------------------------------------------------------- definition / timing

def check_map(bars: pd.DataFrame, at: pd.Timestamp, items: list[dict], fr: dict) -> list[str]:
    """Problems with the liquidity map's areas at ``at`` (empty = clean): from the future, inverted edges, or an
    FVG/IFVG whose edges no three candles on its timeframe produce."""
    from ict_engine.concepts.events import fvgs, volume_imbalances
    probs = []
    gaps = {tf: fvgs(f, tf) for tf, f in fr.items() if tf in ("1w", "1d", "4h", "1h") and len(f) >= 3}
    vis = {tf: volume_imbalances(f, tf) for tf, f in fr.items() if tf in ("1w", "1d", "4h", "1h") and len(f) >= 3}
    tol = 0.006                                                    # the map rounds prices to 2 decimals
    for it in items:
        if it["role"] != "area":
            continue
        if it["top"] is None or it["bottom"] is None or it["top"] < it["bottom"]:
            probs.append(f"{it['label']}: inverted edges")
            continue
        if it["top"] == it["bottom"]:
            probs.append(f"{it['label']} at {it['top']:.2f}: zero width after rounding (a sliver the map should drop)")
            continue
        formed = pd.Timestamp(it["formed"]) if it.get("formed") else None
        if formed is not None and formed.tz is None:
            formed = formed.tz_localize(NY)
        if formed is not None and formed >= at:
            probs.append(f"{it['label']} {it['bottom']:.2f}–{it['top']:.2f}: formed {formed} — after the moment")
        pool = gaps if it["kind"] in ("fvg", "ifvg") else vis if it["kind"] == "vi" else None
        if pool is not None and it["tf"] in pool:
            same = [g for g in pool[it["tf"]] if abs(g.top - it["top"]) < tol and abs(g.bottom - it["bottom"]) < tol]
            if not same:
                probs.append(f"{it['label']} {it['bottom']:.2f}–{it['top']:.2f}: no {it['tf']} candles give these edges")
            elif formed is not None and not any(pd.Timestamp(g.origin_ts) == formed for g in same):
                probs.append(f"{it['label']} {it['bottom']:.2f}–{it['top']:.2f}: edges match but the formation candle differs "
                             f"(map {formed}, candles {[str(g.origin_ts) for g in same][:2]})")
    return probs


# ----------------------------------------------------------------------------------------------------------- run

def run(sources=SOURCES, limit: int = 0) -> tuple[pd.DataFrame, list[str]]:
    from ict_engine.concepts.liquidity_map import build
    from ict_engine.data import dukascopy
    marks = load_marks(sources)
    if limit:
        marks = marks[:limit]
    bars_by, rows, probs = {}, [], []
    by_moment: dict = {}
    for m in marks:
        by_moment.setdefault((m["asset"], m["at"]), []).append(m)
    for (asset, at), ms in sorted(by_moment.items(), key=lambda x: x[0][1]):
        if asset not in bars_by:
            from datetime import date
            bars_by[asset] = dukascopy.load(asset, date(2019, 10, 1) if asset.startswith("US") else date(2021, 10, 1),
                                            date(2024, 7, 1))
        bars = bars_by[asset]
        fr = frames(bars, at)
        arrays = engine_arrays(bars, at, fr)
        try:
            items = build(bars, at)["items"]
        except ValueError:
            items = []
        areas = [i for i in items if i["role"] == "area"]
        probs += [f"{asset} {at:%Y-%m-%d %H:%M}: {p}" for p in check_map(bars, at, items, fr)]
        for m in ms:
            j = judge(m, arrays, areas)
            a = j["engine"] or {}
            rows.append({**{k: m[k] for k in ("source", "id", "asset", "tf", "kind", "drawn", "top", "bottom")},
                         "at": m["at"], "verdict": j["verdict"], "iou": j["iou"], "on_map": j["on_map"],
                         "engine_tf": a.get("tf"), "engine_kind": a.get("kind"), "engine_top": a.get("top"),
                         "engine_bottom": a.get("bottom"), "engine_origin": a.get("origin"),
                         "bars_from_his_anchor": j["bars_from_his_anchor"]})
    return pd.DataFrame(rows), probs


def report(df: pd.DataFrame, probs: list[str]) -> str:
    L = ["# PD-array audit", "",
         f"{len(df)} zones Sharif drew across {df.id.nunique()} review moments ({', '.join(sorted(df.source.unique()))}), "
         "each looked up among the engine's arrays at the same moment (detectors run on every TF, 5m–1w).", "",
         "## Agreement with his zones", "",
         "| kind | TF | n | match | partial | other TF | other kind | same price, other candle | missing | on the map |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for (k, tf), g in df.groupby(["kind", "tf"]):
        c = g.verdict.value_counts()
        L.append(f"| {k} | {tf} | {len(g)} | {c.get('match', 0)} | {c.get('partial', 0)} | {c.get('other TF', 0)} | "
                 f"{c.get('other kind', 0)} | {c.get('same price, other candle', 0)} | {c.get('missing', 0)} | {int(g.on_map.sum())} |")
    c = df.verdict.value_counts()
    found = c.get("match", 0) + c.get("partial", 0)
    L += ["", f"**Found on the same TF and kind, formed within {NEAR_BARS} candles of his anchor: {found}/{len(df)} ({found / max(1, len(df)):.0%}); "
              f"somewhere (any TF/kind): {len(df) - c.get('missing', 0) - c.get('same price, other candle', 0)}/{len(df)}; on the liquidity map: {int(df.on_map.sum())}/{len(df)}.**",
          "", "Reading it: *missing* = the detector has nothing there (a definition gap, or he drew it differently); "
          "*other TF / other kind* = found, but labelled differently from how he sees it; found but *not on the map* = "
          "a usage filter (distance, top-N per side, filled/lifecycle) dropped it.", "",
          "## Definition and timing checks on the map", ""]
    L += ([f"- {p}" for p in probs[:60]] + ([f"- … {len(probs) - 60} more"] if len(probs) > 60 else [])) if probs else ["Clean: every map area was formed before its moment and its edges re-derive from its timeframe's candles."]
    miss = df[df.verdict.isin(["missing", "other kind", "partial", "same price, other candle"])]
    L += ["", "## To look at (missing / partial / other kind)", "",
          "| source | id | TF | his kind | his zone | verdict | engine's nearest | IoU |", "|---|---|---|---|---|---|---|---|"]
    for r in miss.itertuples():
        eng = f"{r.engine_tf} {r.engine_kind} {r.engine_bottom:.2f}–{r.engine_top:.2f}" if r.engine_kind else "–"
        L.append(f"| {r.source} | {r.id} | {r.tf} | {r.drawn} | {r.bottom:.2f}–{r.top:.2f} | {r.verdict} | {eng} | {r.iou} |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=",".join(SOURCES))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out")
    a = ap.parse_args()
    df, probs = run(a.sources.split(","), a.limit)
    md = report(df, probs)
    print(md)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(md)
        df.to_csv(Path(a.out).with_suffix(".csv"), index=False)


if __name__ == "__main__":
    main()
