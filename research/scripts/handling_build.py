"""Trade-handling review set (local only): in-sample 2022 model / MMxM trades whose call was right — price moved our way
— whether they won or got cut off. Sharif 2026-11-15: "give me your set of trades that were moving in our direction so
that I can show you better handling of stop losses … stop loss and TP should be the same thing but a different
approach". He places his own stop / TPs (and entry, if he'd move it) on each; the viewer replays them on the 1m path.

    uv run python research/scripts/handling_build.py [--n 24] [--seed 5]   # needs reports/study-trades.parquet
    uv run python research/scripts/handling_server.py                      # → http://127.0.0.1:8767

Picked from reports/study-trades.parquet (liq_tp_stop_study.py): price went ≥ 2 R our way by the close, and either
  cut   it first moved ≥ 0.5 R our way, was stopped, and still ran (≈ 60%)
  won   TP1 before the stop (≈ 40%)
Charts show the whole day (hindsight is the point here), the week/day context, the engine's plan and the liquidity map
as of the decision.
"""
import argparse
import json
import random
from datetime import datetime, time, timedelta
from pathlib import Path

import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.concepts.liquidity_map import build as liqmap  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402
from liqmap_build import DATA_FROM, num, panel, wall  # noqa: E402

NY = "America/New_York"
OUT = Path("out/handling")
MODELS = {"2022_model": "reports/backtest-{a}-2022-01-03-2024-06-28-futures.parquet",
          "mmxm": "reports/backtest-mmxm-{a}-2022-01-03-2024-06-28-futures.parquet"}
SPAN = {"1w": timedelta(days=730), "1d": timedelta(days=170), "4h": timedelta(days=16), "1h": timedelta(days=4),
        "15m": timedelta(hours=40), "5m": timedelta(hours=14)}


def pick(n: int, seed: int) -> pd.DataFrame:
    t = pd.read_parquet("reports/study-trades.parquet")
    t = t[t.mfe_session >= 2]
    cut = t[t.stopped & (t.mfe_before_stop >= 0.5)]
    won = t[~t.stopped & t.vote]
    k_cut = round(n * 0.6)
    out = []
    for df, k, kind in ((cut, k_cut, "cut"), (won, n - k_cut, "won")):
        per = {m: k // 2 + (k % 2 if m == "2022_model" else 0) for m in MODELS}
        for m, g in df.groupby("model"):
            out.append(g.sample(min(per[m], len(g)), random_state=seed).assign(kind=kind))
    return pd.concat(out).sample(frac=1, random_state=seed)


def item(r, row, bars) -> dict:
    dec, day = pd.Timestamp(r.decided), pd.Timestamp(r.day).date()
    close = pd.Timestamp(datetime.combine(day, time(16, 55)), tz=NY)
    end = pd.Timestamp(datetime.combine(day, time(17)), tz=NY)
    path = bars[(bars.index > dec) & (bars.index <= close)]
    m = liqmap(bars, dec)
    return {
        "id": f"{r.model}-{r.asset}-{dec:%Y%m%d-%H%M}", "kind": r.kind,
        "model": {"2022_model": "2022 model", "mmxm": "MMxM"}[r.model], "asset": r.asset, "day": str(day),
        "label": f"{r.asset} · {dec:%a %d %b %Y %H:%M} NY · {r.side}", "side": r.side, "decided": wall(dec),
        "filled": wall(row.filled_at) if pd.notna(row.filled_at) else None,
        "exit_at": wall(row.exit_at) if pd.notna(row.exit_at) else None, "exit": row.exit,
        "entry": num(row.entry), "stop": num(row.stop), "tp1": num(row.tp1), "final": num(row.final),
        "tp1_name": row.tp1_name, "poi": row.poi, "liquidity": row.liquidity, "window": row.window,
        "r": num(row.r), "runner_r": num(row.runner_r), "risk": num(abs(row.entry - row.stop)),
        "mfe_before_stop": num(r.mfe_before_stop), "mfe_close": num(r.mfe_session), "mae_close": num(r.mae_session),
        "map": {"price": m["price"], "adr": m["adr"], "items": m["items"], "key": m["key"]},
        "panels": {tf: panel(bars, tf, dec - span, end) for tf, span in SPAN.items()},
        "path": [[wall(t), num(h), num(l)] for t, h, l in zip(path.index, path.high, path.low)],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--seed", type=int, default=5)
    a = ap.parse_args()
    sel = pick(a.n, a.seed)
    (OUT / "s").mkdir(parents=True, exist_ok=True)
    ids = []
    for asset, g in sel.groupby("asset"):
        bars = dukascopy.load(asset, DATA_FROM, pd.Timestamp(g.day.max()).date() + timedelta(days=3))
        for r in g.itertuples():
            bt = pd.read_parquet(MODELS[r.model].format(a=asset))
            row = bt[(bt.status == "traded") & (pd.to_datetime(bt.decided_at) == pd.Timestamp(r.decided))].iloc[0]
            it = item(r, row, bars)
            (OUT / "s" / f"{it['id']}.json").write_text(json.dumps(it, separators=(",", ":")))
            ids.append(it["id"])
            print(it["id"], it["kind"], it["exit"], flush=True)
    order = sorted(ids)
    random.Random(a.seed).shuffle(order)
    (OUT / "index.json").write_text(json.dumps({"generated": str(datetime.now().date()), "seed": a.seed, "ids": order}, indent=1))
    print(len(order), "trades →", OUT / "index.json")


if __name__ == "__main__":
    main()
