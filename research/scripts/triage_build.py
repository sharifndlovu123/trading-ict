"""Build the local triage review set: a seeded random sample of 2022 model and MMxM trades from the in-sample period
(2022-01-03 → 2023-09-28, futures-basis backtests), one JSON per setup with 4h/1h/15m/5m candles, the plan, the
entry FVG, the swept level, live 4h/daily FVGs, day levels and every bias read — all as known at the decision — plus
the outcome (shown only after Sharif answers).

    uv run python research/scripts/triage_build.py [--n 120] [--seed 7]   # → out/triage/{index.json, s/<id>.json}
    uv run python research/scripts/triage_server.py                       # → http://127.0.0.1:8765

The out-of-sample 30% (2023-09-29 → 2024-06-28) is never sampled, so rules learned from these answers can still be
tested on unseen data.
"""
import argparse
import json
import math
import os
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.context import build_context
from ict_engine.data import dukascopy
from ict_engine.models import entry_quality as eq
from ict_engine.models.registry import modules
from ict_engine.sim.run import run_day

NY = "America/New_York"
OUT = Path("out/triage")
START, CUT = date(2022, 1, 3), date(2023, 9, 29)          # in-sample only
MODELS = {"2022_model": "reports/backtest-{a}-2022-01-03-2024-06-28-futures.parquet",
          "mmxm": "reports/backtest-mmxm-{a}-2022-01-03-2024-06-28-futures.parquet"}
ASSETS = ("US100", "US500", "US30", "XAUUSD", "XAGUSD")
PANELS = {"4h": timedelta(days=16), "1h": timedelta(days=4), "15m": timedelta(hours=36), "5m": timedelta(hours=10)}


def wall(ts) -> int:
    t = pd.Timestamp(ts).tz_convert(NY)
    return int(t.tz_localize(None).timestamp())


def num(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 2)


def candles(df):
    return [[wall(t), num(o), num(h), num(l), num(c)] for t, o, h, l, c in zip(df.index, df.open, df.high, df.low, df.close)]


def sample(n: int, seed: int) -> pd.DataFrame:
    rows = []
    for m, pat in MODELS.items():
        for a in ASSETS:
            d = pd.read_parquet(pat.format(a=a))
            d = d[(d.status == "traded") & (pd.to_datetime(d.day).dt.date >= START) & (pd.to_datetime(d.day).dt.date < CUT)]
            rows.append(d.assign(model=m, asset=a))
    df = pd.concat(rows)
    per = n // len(MODELS)
    return pd.concat([g.sample(min(per, len(g)), random_state=seed) for _, g in df.groupby("model")]).sample(frac=1, random_state=seed)


def build(r, bars) -> dict | None:
    day = pd.Timestamp(r.day).date()
    dec = pd.Timestamp(r.decided_at)
    st = next((s for s in run_day(bars, day, r.asset, modules()[r.model].Params()) if s.decided_at == dec and s.plan), None)
    if st is None:
        return None
    end = pd.Timestamp(datetime.combine(day, time(17)), tz=NY)
    ctx = build_context(bars[bars.index < end], day)
    p, res = st.plan, st.result
    fvg, liq = st.evidence.get("fvg"), st.evidence.get("liquidity")
    panels, live = {}, {}
    for tf, span in PANELS.items():
        seg = bars[(bars.index >= dec - span) & (bars.index < end)]
        panels[tf] = candles(resample(seg, tf))
        live[tf] = candles(resample(seg[seg.index < dec], tf))     # blind view: last candle half-formed, as live
    gaps = [{"tf": tf, "dir": g.direction, "top": num(g.top), "bottom": num(g.bottom)}
            for tf in ("4h", "1d") for g in eq._live_htf_fvgs(bars, dec, tf)]
    gaps = sorted(gaps, key=lambda g: min(abs(g["top"] - p.entry), abs(g["bottom"] - p.entry)))[:4]   # nearest 4
    return {
        "id": f"{r.model}-{r.asset}-{dec:%Y%m%d-%H%M}", "model": {"2022_model": "2022 model", "mmxm": "MMxM"}[r.model],
        "family": r.model, "asset": r.asset, "day": str(day), "weekday": f"{dec:%A}", "window": r.window,
        "side": r.side, "decided": wall(dec), "entry": num(p.entry), "stop": num(p.stop), "tp1": num(p.tp1),
        "final": num(p.final_target), "tp1_name": p.tp1_name, "risk": num(p.risk),
        "fvg": [num(fvg.bottom), num(fvg.top)] if fvg is not None else None,
        "sweep": num(liq.bottom if r.side == "long" else liq.top) if liq is not None else None,
        "poi": r.poi, "liquidity": r.liquidity, "bias_used": r.bias, "bias_rule": r.bias_rule,
        "biases": {k: v[0] for k, v in ctx.biases.items()},
        "levels": {k: num(v) for k, v in ctx.levels.items() if k in ("pdh", "pdl", "pwh", "pwl", "midnight_open")},
        "htf_gaps": gaps, "news": r.news_event if isinstance(r.news_event, str) else "",
        "panels": panels, "live": live,
        "outcome": {"exit": res.exit_reason, "r": num(res.r), "runner_r": num(res.runner_r),
                    "filled": wall(res.filled_at) if res.filled_at is not None else None,
                    "exit_at": wall(res.exit_at) if res.exit_at is not None else None},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    os.environ.setdefault("ICT_COST_BASIS", "futures")
    pick = sample(a.n, a.seed)
    (OUT / "s").mkdir(parents=True, exist_ok=True)
    ids = []
    for asset, g in pick.groupby("asset"):
        bars = dukascopy.load(asset, START - timedelta(days=40), CUT + timedelta(days=2))
        for _, r in g.iterrows():
            item = build(r, bars)
            if item is None:
                print("skip (setup not reproduced)", r.model, asset, r.decided_at)
                continue
            (OUT / "s" / f"{item['id']}.json").write_text(json.dumps(item, separators=(",", ":")))
            ids.append(item["id"])
            print(item["id"], item["outcome"]["exit"], flush=True)
    order = sorted(ids)
    random.Random(a.seed).shuffle(order)               # mixed models/assets/dates, same order every build
    (OUT / "index.json").write_text(json.dumps({"generated": str(date.today()), "seed": a.seed, "period": [str(START), str(CUT)],
                                                "ids": order}, indent=1))
    print(len(order), "setups →", OUT / "index.json")


if __name__ == "__main__":
    main()
