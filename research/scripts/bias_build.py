"""Bias labelling set (local only): 20 in-sample moments; Sharif reads the bias on W / D / 4H / 1H (bull / bear / range)
before the engine's weekly-structure call is shown. Checks research/preregistered-weekly-structure-2026-11-16.md's rule
against his reading before any sweep.

    uv run python research/scripts/bias_build.py [--n 20] [--seed 11]
    uv run python research/scripts/liqmap_server.py --port 8770 --data out/bias --page viewer/bias.html \
        --answers reports/reviews/bias.jsonl          → http://127.0.0.1:8770

Moments: a random weekday 08:30 NY, 2022-07-01 → 2023-09-28 (in-sample), US100 US500 US30, stratified by the engine's
weekly call (bear / bull / neutral) so every kind is seen. Charts show only candles before the moment.
"""
import argparse
import json
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.concepts.bars import resample  # noqa: E402
from ict_engine.concepts.context import build_context, completed_daily, weekly_swings  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402
from liqmap_build import DATA_FROM, NY, num, panel, wall  # noqa: E402

OUT = Path("out/bias")
ASSETS = ("US100", "US500", "US30")
START, CUT = date(2022, 7, 1), date(2023, 9, 29)
PANELS = {"1w": timedelta(days=730), "1d": timedelta(days=200), "4h": timedelta(days=30), "1h": timedelta(days=7)}


def moment(asset, bars, d):
    at = pd.Timestamp(datetime.combine(d, time(8, 30)), tz=NY)
    if bars[(bars.index >= at - timedelta(minutes=5)) & (bars.index < at)].empty:
        return None
    ctx = build_context(bars, d)
    past = bars[bars.index < at]
    daily = completed_daily(resample(past, "1d"), d)
    w = weekly_swings(daily)
    sw = lambda xs: [[wall(pd.Timestamp(t).tz_localize(NY)), num(p)] for t, p in xs]
    return {"id": f"{asset}-{d:%Y%m%d}", "asset": asset, "at": wall(at), "day": str(d),
            "panels": {tf: panel(past, tf, at - span, at) for tf, span in PANELS.items()},
            "engine": {"weekly_structure": list(ctx.biases["weekly_structure"]), "htf40": list(ctx.biases["htf40"]),
                       "htf20": list(ctx.biases["htf20"]), "daily": list(ctx.biases["prev_day_dol"]),
                       "swing_highs": sw(w[1]) if w else [], "swing_lows": sw(w[2]) if w else []}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    bars = {x: dukascopy.load(x, DATA_FROM, CUT + timedelta(days=3)) for x in ASSETS}
    days = [START + timedelta(days=i) for i in range((CUT - START).days)]
    days = [d for d in days if d.weekday() < 5]
    want = {"bear": a.n // 3, "bull": a.n // 3}
    want["neutral"] = a.n - 2 * (a.n // 3)
    got, used, tries = {k: [] for k in want}, set(), 0
    while any(len(got[k]) < want[k] for k in want) and tries < 2000:
        tries += 1
        asset, d = rnd.choice(ASSETS), rnd.choice(days)
        if any(abs((d - u).days) < 21 for x, u in used if x == asset):     # spread the moments out
            continue
        try:
            it = moment(asset, bars[asset], d)
        except ValueError:
            continue
        if it is None:
            continue
        k = it["engine"]["weekly_structure"][0]
        if len(got[k]) < want[k]:
            got[k].append(it); used.add((asset, d))
    items = [it for k in got for it in got[k]]
    rnd.shuffle(items)
    (OUT / "s").mkdir(parents=True, exist_ok=True)
    for it in items:
        (OUT / "s" / f"{it['id']}.json").write_text(json.dumps(it, separators=(",", ":")))
        print(it["id"], it["engine"]["weekly_structure"][0], flush=True)
    (OUT / "index.json").write_text(json.dumps({"generated": str(date.today()), "seed": a.seed,
                                                "ids": [it["id"] for it in items]}, indent=1))
    print(len(items), "moments →", OUT / "index.json")


if __name__ == "__main__":
    main()
