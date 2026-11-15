"""Build the liquidity-map review set (local only): moments where Sharif opens a chart to hunt, each with the engine's
liquidity map as of that moment (ict_engine.concepts.liquidity_map) on daily / 4h / 1h / 15m candles, plus what
happened next (hidden in the viewer until he has marked the map).

    uv run python research/scripts/liqmap_build.py [--n 12] [--seed 11] [--at US100 2023-03-15 08:30 ...]
    uv run python research/scripts/liqmap_server.py      # → http://127.0.0.1:8766

Random moments are weekdays at 08:30 NY inside the in-sample period (2022-07-01 → 2023-09-28; history before it feeds
the daily map), so anything learned from the marks can still be tested on unseen data.
"""
import argparse
import json
import math
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.liquidity_map import _daily, build
from ict_engine.data import dukascopy

NY = "America/New_York"
OUT = Path("out/liqmap")
START, CUT = date(2022, 7, 1), date(2023, 9, 29)
ASSETS = ("US100", "US500", "US30", "XAUUSD")
PANELS = {"1d": timedelta(days=170), "4h": timedelta(days=25), "1h": timedelta(days=6), "15m": timedelta(days=2)}
FWD = {"1d": timedelta(days=14), "4h": timedelta(days=6), "1h": timedelta(days=3), "15m": timedelta(hours=30)}
HORIZON = timedelta(days=14)


def wall(ts) -> int:
    return int(pd.Timestamp(ts).tz_convert(NY).tz_localize(None).timestamp())


def num(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 2)


def candles(df):
    return [[wall(t), num(o), num(h), num(l), num(c)] for t, o, h, l, c in zip(df.index, df.open, df.high, df.low, df.close)]


def panel(bars, tf, a, b):
    seg = bars[(bars.index >= a) & (bars.index < b)]
    if seg.empty:
        return []
    if tf == "1d":
        d = _daily(seg)
        d.index = [pd.Timestamp(s).tz_localize(None).tz_localize(NY) if pd.Timestamp(s).tzinfo is None else s for s in d.index]
        return candles(d)
    return candles(resample(seg, tf))


def first_touch(fwd: pd.DataFrame, it: dict, last: float) -> int | None:
    """Wall time of the first 1m bar after the moment that trades to the level (areas: to the near edge)."""
    p = it["price"]
    m = (fwd.high >= p) if p > last else (fwd.low <= p)
    return wall(fwd.index[m.argmax()]) if m.any() else None


def moment(asset: str, at: pd.Timestamp, bars: pd.DataFrame) -> dict:
    m = build(bars, at)
    fwd = bars[(bars.index >= at) & (bars.index < at + HORIZON)]
    for it in m["items"]:
        it["hit"] = first_touch(fwd, it, m["price"])
    return {"id": f"{asset}-{at:%Y%m%d-%H%M}", "asset": asset, "at": wall(at), "label": f"{asset} · {at:%a %d %b %Y %H:%M} NY",
            "map": m,
            "live": {tf: panel(bars, tf, at - span, at) for tf, span in PANELS.items()},
            "fwd": {tf: panel(bars, tf, at, at + FWD[tf]) for tf in PANELS}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--at", nargs=3, action="append", metavar=("ASSET", "DATE", "HH:MM"), default=[])
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    days = [d.date() for d in pd.bdate_range(START, CUT - timedelta(days=1))]
    want = [(ASSETS[i % len(ASSETS)], pd.Timestamp(datetime.combine(rnd.choice(days), time(8, 30)), tz=NY))
            for i in range(a.n)]
    want += [(x, pd.Timestamp(f"{d} {hm}", tz=NY)) for x, d, hm in a.at]
    (OUT / "s").mkdir(parents=True, exist_ok=True)
    ids, cache = [], {}
    for asset, at in want:
        if asset not in cache:
            cache[asset] = dukascopy.load(asset, START - timedelta(days=200), CUT + timedelta(days=20))
        try:
            item = moment(asset, at, cache[asset])
        except ValueError as e:
            print("skip", asset, at, e)
            continue
        (OUT / "s" / f"{item['id']}.json").write_text(json.dumps(item, separators=(",", ":")))
        ids.append(item["id"])
        print(item["id"], len(item["map"]["items"]), "items", flush=True)
    order = sorted(set(ids))
    rnd.shuffle(order)
    (OUT / "index.json").write_text(json.dumps({"generated": str(date.today()), "seed": a.seed, "ids": order}, indent=1))
    print(len(order), "moments →", OUT / "index.json")


if __name__ == "__main__":
    main()
