"""Score a liquidity-map selection against Sharif's saved marks (reports/reviews/liqmap.jsonl, latest save per moment).

    uv run python research/scripts/liqmap_score.py [--json]     # --json: score the built set in out/liqmap/s (as built)
                                                                # default: rebuild each map with the current module

For each of his marks (levels and zones; trendlines skipped) we ask whether the selection has it:
  level  ↔ an engine buyside/sellside level within 0.1 ADR (its price or a merged twin)
  zone   ↔ an engine area that overlaps it (or a level inside it, for a gap he drew around a level)
Reports recall (his marks found) and how many lines the selection shows — fewer lines at the same recall is better.
Selections: all items · clean (old: prev week/day/month H/L + nearest 1w/1d + daily draw) · topdown (new key).
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

CORE = {"pwh", "pwl", "pdh", "pdl", "pmh", "pml"}


def old_clean(m):
    k, s = m["key"], {it["id"] for it in m["items"] if it["kind"] in CORE}
    for tf in ("1w", "1d"):
        s |= {v for v in (k.get("nearest", {}).get(tf) or {}).values() if v}
    if k.get("daily_draw"):
        s.add(k["daily_draw"])
    return s


def topdown(m):
    s = set()
    for tf, d in (m["key"].get("topdown") or {}).items():
        for v in d.values():
            s |= set(v)
    return s


def found(mark, items, adr):
    if mark["shape"] == "zone":
        lo, hi = mark["bottom"], mark["top"]
        return any((it["role"] == "area" and it["bottom"] <= hi and it["top"] >= lo) or
                   (it["role"] != "area" and lo <= it["price"] <= hi) for it in items)
    return any(it["role"] != "area" and abs(it["price"] - mark["price"]) <= 0.1 * adr for it in items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--answers", default="reports/reviews/liqmap.jsonl", help="reports/reviews/topdown.jsonl for the top-down set")
    ap.add_argument("--data", default="out/liqmap", help="out/topdown for the top-down set")
    a = ap.parse_args()
    saves = {}
    for line in open(a.answers):
        d = json.loads(line)
        saves[d["id"]] = d
    maps = {}
    if a.json:
        for mid in saves:
            maps[mid] = json.load(open(f"{a.data}/s/{mid}.json"))["map"]
    else:
        import pandas as pd
        from ict_engine.concepts.liquidity_map import build
        from ict_engine.data import dukascopy
        from liqmap_build import DATA_FROM
        for mid, d in saves.items():
            asset = mid.split("-")[0]
            at = pd.Timestamp(d["at"], unit="s").tz_localize("America/New_York")
            bars = dukascopy.load(asset, DATA_FROM, (at + pd.Timedelta(days=1)).date())
            maps[mid] = build(bars, at)
    sels = {"all": lambda m: {it["id"] for it in m["items"]}, "clean (old)": old_clean, "topdown": topdown}
    tot = defaultdict(lambda: [0, 0, 0])       # found, marks, lines
    by = defaultdict(lambda: [0, 0])
    misses = []
    for mid, d in saves.items():
        m = maps[mid]
        marks = [x for x in d["added"] if x["shape"] != "trend"]
        for name, f in sels.items():
            ids = f(m)
            its = [it for it in m["items"] if it["id"] in ids]
            hit = [found(x, its, m["adr"]) for x in marks]
            t = tot[name]
            t[0] += sum(hit); t[1] += len(marks); t[2] += len(its)
            if name == "topdown":
                for x, h in zip(marks, hit):
                    k = f"{x['tf']} {'zone' if x['shape'] == 'zone' else 'level'}"
                    by[k][0] += h; by[k][1] += 1
                    if not h:
                        misses.append(f"{mid} {x['tf']} {x['kind']} " + (f"{x['bottom']}–{x['top']}" if x["shape"] == "zone" else f"{x['price']}"))
    n = len(saves)
    print(f"{n} moments, {tot['all'][1]} marks (trendlines skipped)")
    for name, (f_, k, lines) in tot.items():
        print(f"  {name:12} found {f_}/{k} ({f_ / k:.0%}) · {lines / n:.1f} lines per moment")
    if by:
        print("  topdown by type:", {k: f"{v[0]}/{v[1]}" for k, v in sorted(by.items())})
        print("  topdown misses:\n   " + "\n   ".join(misses))


if __name__ == "__main__":
    main()
