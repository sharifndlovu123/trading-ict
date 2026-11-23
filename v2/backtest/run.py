"""Run the tools backtest over the candle files: at the start of each of his kill zones, on every trading day, the
tools read each higher timeframe, make their calls, and each call is followed until it comes true, is undone or runs
out of time. Design: v2/specs/2026-11-20-higher-timeframe-backtest.md.

    uv run python v2/backtest/run.py US30 --since 2025-01-01 --until 2025-12-31
    uv run python v2/backtest/run.py                            # what he trades: the three indices, gold and silver
    uv run python v2/backtest/run.py --all                      # every instrument, all the data (at most 8 at once)

This is the runner, so it is the one place the timeframes are named: he set them ("this backtest will be higher
timeframes, so lowest tf is probably hourly or 4h"). It changes no tool and no lesson. What it writes
(``v2/backtest/out/``) is rebuilt by running it and is not kept in git.

Since 20 Nov 2026 each timeframe below the top also makes one ``merged`` call (his correction after the first run; see
``calls.merged``); since 23 Nov 2026 it is read with EVERY timeframe above it, and a key area ends on a body close of
the area's own timeframe (his review of ten merged calls). The single-timeframe calls are kept beside it.

Mine, not his: two reads a day at the kill-zone starts; a call is not made again while the same call (same timeframe,
same kind, same target and level behind) is still open; a call is given 20 candles of its own timeframe.
"""
from __future__ import annotations

import argparse
import json
import sys
from bisect import bisect_left, bisect_right
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
for folder in sorted((HERE.parent / "concepts").glob("[0-9]*_*")) + [HERE, HERE.parent / "chart"]:
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import candles as cd  # noqa: E402
import pandas as pd  # noqa: E402
from calls import calls, merged, played_out, read, resolve  # noqa: E402
from sessions import KILL_ZONES, sessions  # noqa: E402

OUT = HERE / "out"
LADDER = ["1M", "1W", "1D", "4h", "1h"]          # highest first; the last is the lowest timeframe read
FINE = LADDER[-1]                                # what price traded to, and in what order, is taken from this one
KEEP = {"1M": 600, "1W": 600, "1D": 600, "4h": 600, "1h": 600}      # how many closed candles a read is given
HORIZON = 20
# What he trades (20 Nov 2026): "when I say indices, stick to 100, 500 and 30… gold and silver is just for a different
# chart, and silver is to have something to compare against gold." A backtest runs on these unless others are named.
TRADED = ["US100", "US500", "US30", "XAUUSD", "XAGUSD"]
EPOCH = pd.Timestamp("1970-01-01")


def secs(index: pd.DatetimeIndex) -> list[int]:
    return [int(v) for v in (index - EPOCH) // pd.Timedelta(seconds=1)]


def forming_index(times: list[int], moment: int) -> int:
    """Index of the candle that is forming at ``moment`` (the last one whose label is at or before it). Every candle
    before that index had closed by then. If no candle has started yet, 0."""
    return max(bisect_right(times, moment) - 1, 0)


def owners(m_index: pd.DatetimeIndex, tf: str, labels: pd.DatetimeIndex) -> list[int]:
    """For each lowest-timeframe candle, the index of the ``tf`` candle it belongs to (the same grouping the candle
    reader uses, so a daily candle starts at the evening reopen and not at midnight)."""
    if tf in cd.MINUTES:
        at = secs(labels)                                # once, not once per candle
        return [bisect_right(at, t) - 1 for t in secs(m_index)]
    day = cd.trading_day(m_index)
    key = day if tf == "1D" else day - pd.to_timedelta(day.day_of_week, unit="D") if tf == "1W" else day.to_period("M").to_timestamp()
    where = {int(v): i for i, v in enumerate(secs(labels))}
    return [where[t] for t in secs(pd.DatetimeIndex(key))]


def prepare(asset: str) -> dict:
    """An instrument's candles on every timeframe of the ladder, ready to be read at any moment."""
    m = cd.load_1m(asset)
    frames = {tf: cd.resample(m, tf) for tf in LADDER}
    c = {tf: cd.to_candles(frames[tf]) for tf in LADDER}
    t = {tf: [x["time"] for x in c[tf]] for tf in LADDER}
    own = {tf: owners(frames[FINE].index, tf, frames[tf].index) for tf in LADDER}
    closes = {tf: [(t[tf][n + 1], c[tf][n]["close"]) for n in range(len(c[tf]) - 1)] for tf in LADDER}   # when each candle closed, and where
    return {"c": c, "t": t, "own": own, "closes": closes}


def reads_at(p: dict, moment: int) -> dict:
    """What the tools see on EVERY timeframe of the ladder at one moment, highest first: ``{tf: (index of the candle
    forming, the read or None)}``. Each is read with the two timeframes above it, from candles that had closed, plus
    what its own forming candle has done so far."""
    c, t, own = p["c"], p["t"], p["own"]
    fine, j, reads = c[FINE], bisect_left(t[FINE], moment), {}
    for i, tf in enumerate(LADDER):
        k = forming_index(t[tf], moment)
        above = [c[u][max(0, forming_index(t[u], moment) - KEEP[u]):forming_index(t[u], moment)] for u in LADDER[max(0, i - 2):i]]
        parent = above[-1] if above else None
        grand = above[-2] if len(above) == 2 else None
        since_close = [fine[n] for n in range(max(0, j - 800), j) if own[tf][n] == k]       # what the forming candle has done
        reads[tf] = (k, read(c[tf][max(0, k - KEEP[tf]):k], parent, grand, since_close))
    return reads


def run_asset(asset: str, since: str | None = None, until: str | None = None) -> pd.DataFrame:
    p = prepare(asset)
    c, t = p["c"], p["t"]
    fine, ft = c[FINE], t[FINE]
    step = 3600
    starts = sorted(span[0] * 60 for span in KILL_ZONES.values())               # seconds after midnight, New York clock
    days = sorted({x - x % 86400 for x in ft})
    lo = int((pd.Timestamp(since) - EPOCH).total_seconds()) if since else days[0]
    hi = int((pd.Timestamp(until) - EPOCH).total_seconds()) + 86400 if until else days[-1] + 86400
    rows, still = [], {}
    for day in days:
        for start in starts:
            moment = day + start
            j = bisect_left(ft, moment)
            if not (lo <= moment < hi) or j >= len(ft) or ft[j] != moment:      # the market must be trading at that hour
                continue
            zone = next(name for name, span in KILL_ZONES.items() if span[0] * 60 == start)
            reads = reads_at(p, moment)
            for i, tf in enumerate(LADDER):
                k, r = reads[tf]
                if r is None:
                    continue
                up = reads[LADDER[i - 1]][1] if i else None
                up_side = up["side"] if up else None
                both = merged(r, [reads[u][1] for u in LADDER[:i]])                 # the whole ladder above, read together
                area_tf = LADDER[both["area_i"]] if both and both["area_i"] is not None else None
                ka = reads[area_tf][0] if area_tf else 0                            # a key area ends on a close of ITS timeframe
                area_closes = [(t[area_tf][n + 1], c[area_tf][n]["close"]) for n in range(ka, len(c[area_tf]) - 1)] if area_tf else None
                closes = [(t[tf][n + 1], c[tf][n]["close"]) for n in range(k, min(k + HORIZON + 1, len(c[tf]) - 1))]
                for call in calls(r) + ([both] if both else []):
                    same = (round(call["target"][0], 6), round(r["behind"], 6))
                    held = still.get((tf, call["kind"]))
                    if held and held[0] == same and moment < held[1]:
                        continue                                                    # the same call is still open: not made twice
                    res = resolve(call, fine[j:], closes, HORIZON, area_closes if call["kind"] == "merged" else None)
                    still[(tf, call["kind"])] = (same, res["at"] if res["at"] is not None else float("inf"))
                    at = res["at"]
                    bias_tf = area_tf if call["kind"] == "merged" and area_tf else tf     # the timeframe whose bias the call states
                    po = (played_out(call["side"], call["target"], call.get("bias_behind", r["behind"]), call["near"], fine, j,
                                     p["closes"][bias_tf], reads[bias_tf][0]) if call["target"][1] != "close" else {"played": None, "played_at": None})
                    rows.append({
                        "id": f"{asset}-{tf}-{call['kind']}-{moment}", "asset": asset, "tf": tf, "kind": call["kind"], "moment": moment,
                        "year": pd.Timestamp(moment, unit="s").year, "made_in": zone, "side": call["side"], "above": up_side,
                        "with_above": None if up_side is None else up_side == call["side"], "own_side": r["side"],
                        "merge": call.get("merge"), "what": call.get("what"), "whose": call.get("whose"),
                        "whose_tf": None if call.get("whose") is None else tf if call["whose"] == "own" else LADDER[call["whose_i"]],
                        "area_tf": area_tf if call["kind"] == "merged" else None, "price": r["price"], "near": r["near"],
                        "target": call["target"][0], "target_how": call["target"][1], "undo": json.dumps(call["undo"]),
                        "behind": r["behind"], "ahead": r["ahead"], "buyside": r["buyside"], "sellside": r["sellside"],
                        "imbalance": json.dumps(call["gap"] if call["kind"] == "merged" else r["imbalance_above"] if r["side"] == "bull" else r["imbalance_below"]),
                        "dist_target": call["dist_target"], "dist_undo": call["dist_undo"], "nearer": call["nearer"],
                        "outcome": res["outcome"], "at": at, "candles": res["candles"],
                        "bias_tf": bias_tf, "played": po["played"], "played_at": po["played_at"],
                        "played_hours": None if po["played_at"] is None else (po["played_at"] + step - moment) / 3600,
                        "hours": None if at is None else (at + step - moment) / 3600,
                        "resolved_in": None if at is None else "/".join(sessions((at % 86400) // 60)) or "outside",
                        "resolved_hour": None if at is None else (at % 86400) // 3600})
    return pd.DataFrame(rows)


def save(asset: str, since: str | None, until: str | None) -> str:
    df = run_asset(asset, since, until)
    OUT.mkdir(exist_ok=True)
    df.to_parquet(OUT / f"calls-{asset}.parquet")
    return f"{asset}: {len(df)} calls, " + ", ".join(f"{k} {v}" for k, v in df["outcome"].value_counts().items()) if len(df) else f"{asset}: no calls"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("assets", nargs="*", choices=sorted(cd.FOLDERS) + [[]])
    ap.add_argument("--all", action="store_true", help="every instrument in the data, including the ones kept only for testing")
    ap.add_argument("--since")
    ap.add_argument("--until")
    a = ap.parse_args()
    names = sorted(cd.FOLDERS) if a.all else a.assets or TRADED          # with nothing named: what he trades
    if len(names) == 1:
        print(save(names[0], a.since, a.until))
        return
    with ProcessPoolExecutor(max_workers=min(8, len(names))) as pool:              # the machine's limit is 10 workers
        for line in pool.map(save, names, [a.since] * len(names), [a.until] * len(names)):
            print(line)


if __name__ == "__main__":
    main()
