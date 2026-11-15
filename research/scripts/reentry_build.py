"""Re-entry review set (local only): in-sample re-entries from the re-entry sweep (research/preregistered-reentry-2026-11-16.md)
— each one shown with the stopped first trade before it in the same window. Sharif marks whether the re-entry was
valid, where he would have re-entered (or not), and his stop / TPs; the trade-handling page replays it.

    uv run python research/scripts/reentry_build.py [--n 24] [--seed 7]    # needs reports/reentry-<model>.parquet
    uv run python research/scripts/handling_server.py --port 8769 --data out/reentry --answers reports/reviews/reentry.jsonl
    → http://127.0.0.1:8769

In-sample only (decisions before 2023-09-29). Half won / half lost where possible, split across the two models.
"""
import argparse
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.data import dukascopy  # noqa: E402
from handling_build import item  # noqa: E402
from liqmap_build import DATA_FROM, num, wall  # noqa: E402

OUT = Path("out/reentry")
CUT = pd.Timestamp("2023-09-29")
VARIANT = "re-entry: after a stop, same side"


def pairs(model: str) -> pd.DataFrame:
    df = pd.read_parquet(f"reports/reentry-{model}.parquet")
    t = df[(df.variant_name == VARIANT) & (df.status == "traded")].copy()
    t["model_key"] = model
    re = t[t.reentry & (t.day < CUT)]
    out = []
    for r in re.itertuples():
        first = t[(t.asset == r.asset) & (t.day == r.day) & (t.window == r.window) & ~t.reentry
                  & (t.decided_at < r.decided_at)].sort_values("decided_at")
        if first.empty:
            continue
        f = first.iloc[-1]
        out.append({"idx": r.Index, "first_idx": f.name, "asset": r.asset, "model": model,
                    "won": bool(r.runner_r > 0), "day": r.day})
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    frames = {m: pd.read_parquet(f"reports/reentry-{m}.parquet") for m in ("2022_model", "mmxm")}
    cand = pd.concat([pairs(m) for m in frames], ignore_index=True)
    rnd = random.Random(a.seed)
    pick = []
    for (m, won), g in cand.groupby(["model", "won"]):
        k = a.n // 4
        pick += g.sample(min(k, len(g)), random_state=a.seed).to_dict("records")
    short = a.n - len(pick)                                  # top up from whatever is left
    if short > 0:
        took = {(p["model"], p["idx"]) for p in pick}
        rest = cand[[(m, i) not in took for m, i in zip(cand.model, cand.idx)]]
        pick += rest.sample(min(short, len(rest)), random_state=a.seed).to_dict("records")
    (OUT / "s").mkdir(parents=True, exist_ok=True)
    ids, cache = [], {}
    for p in pick:
        df = frames[p["model"]]
        row, first = df.loc[p["idx"]], df.loc[p["first_idx"]]
        if p["asset"] not in cache:
            cache[p["asset"]] = dukascopy.load(p["asset"], DATA_FROM, CUT.date() + timedelta(days=5))
        bars = cache[p["asset"]]
        r = SimpleNamespace(decided=row.decided_at, day=row.day, model=p["model"], asset=p["asset"], side=row.side,
                            kind="reentry", mfe_before_stop=None, mfe_session=None, mae_session=None)
        it = item(r, row, bars)
        it["id"] = f"re-{it['id']}"
        it["outcome"] = "won" if p["won"] else "lost"
        it["prior"] = {"entry": num(first.entry), "stop": num(first.stop), "tp1": num(first.tp1), "side": first.side,
                       "decided": wall(first.decided_at),
                       "filled": wall(first.filled_at) if pd.notna(first.filled_at) else None,
                       "exit_at": wall(first.exit_at) if pd.notna(first.exit_at) else None,
                       "r": num(first.runner_r if pd.notna(first.runner_r) else first.r)}
        (OUT / "s" / f"{it['id']}.json").write_text(json.dumps(it, separators=(",", ":")))
        ids.append(it["id"])
        print(it["id"], it["outcome"], flush=True)
    order = sorted(ids)
    rnd.shuffle(order)
    (OUT / "index.json").write_text(json.dumps({"generated": str(date.today()), "seed": a.seed, "ids": order}, indent=1))
    print(len(order), "re-entries →", OUT / "index.json")


if __name__ == "__main__":
    main()
