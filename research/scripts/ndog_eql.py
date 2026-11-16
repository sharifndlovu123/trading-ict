"""The gap as a target only after equal lows are swept and price pushes back (Sharif, 2026-11-16):

"I would find [the gap] interesting … we have EQLs created and it was swept, and then price has a high push upwards,
into the direction of the gap, it would be safe to assume we can try close that top gap. Because not all gaps will be
closed … I didn't find the gap as a possible closing point for the trade until the sellside was swept."

Per futures session with an opening gap still open (gap above = a buy; mirror for a gap below), on 15m candles:
  liquidity   untaken 15m swing lows of the session (2 candles each side); EQL = two of them at least an hour apart
              within ``EQ_TOL`` × ADR of each other
  sweep       a candle trades below the level
  push        within an hour, a 15m candle closes back above the level; a displacement = its range ≥ 1.5 × the median
              range of the last 20 candles and the close in its top 40%
  trade       buy that close; stop under the sweep's low; target the gap's far edge; flat at 16:55
Four versions, so each piece is measured: any swing low / equal lows × any close back / displacement.
Descriptive and in-sample.

    uv run python research/scripts/ndog_eql.py     → reports/ndog-eql-trades.parquet, research/ndog/<date>-eql-study.md
"""
from __future__ import annotations

import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ndog_study as nd  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402
from ict_engine.data.instruments import cost_at  # noqa: E402

EQ_TOL = 0.03          # equal lows: within 3% of the ADR of each other
MIN_APART = 4          # … and at least 4 candles (1 hour) apart
PUSH_WITHIN = 4        # the close back within 4 candles of the sweep
AGG = {"open": "first", "high": "max", "low": "min", "close": "last"}
VERSIONS = {"any low, any close back": (False, False), "any low, displacement": (False, True),
            "equal lows, any close back": (True, False), "equal lows, displacement": (True, True)}


def find(O, H, L, C, target: float, adr: float, need_eql: bool, need_disp: bool) -> dict | None:
    """Long case on 15m arrays of one session (the caller mirrors a short by negating prices). Returns the first
    setup: sweep candle ``k``, entry candle ``m``, the swept level, entry (close of ``m``) and stop."""
    n = len(C)
    rng = H - L
    for k in range(6, n - 1):
        if H[:k].max() >= target:
            return None                                    # the gap closed first
        # a swing low of the session (the opening candles count: their left side is the open itself), still untaken
        lows = [i for i in range(0, k - 2) if (i == 0 or L[i] < L[max(0, i - 2):i].min()) and L[i] < L[i + 1:i + 3].min() and L[i] <= L[i + 1:k].min()]
        if not lows:
            continue
        # the pools this candle takes; the deepest one is the reference (a sweep takes every pool above it too)
        if need_eql:
            pools = [(min(L[i], L[j]), max(L[i], L[j])) for a, i in enumerate(lows) for j in lows[a + 1:]
                     if j - i >= MIN_APART and abs(L[i] - L[j]) <= EQ_TOL * adr]
        else:
            pools = [(L[i], L[i]) for i in lows]
        taken = [p for p in pools if L[k] < p[0]]
        if not taken:
            continue
        level, top = min(taken)
        for m in range(k, min(n - 1, k + PUSH_WITHIN + 1)):
            if H[:m + 1].max() >= target:
                return None
            if C[m] <= top:
                continue
            base = np.median(rng[max(0, k - 20):k]) if k >= 4 else 0.0
            disp = base > 0 and rng[m] >= 1.5 * base and C[m] >= L[m] + 0.6 * rng[m]
            if need_disp and not disp:
                continue
            stop = float(L[k:m + 1].min())
            if C[m] >= target or C[m] <= stop:
                return None
            return {"k": k, "m": m, "level": float(level), "entry": float(C[m]), "stop": stop, "displacement": bool(disp)}
    return None


MIN_FVG = 0.02         # the push's gap must be at least 2% of the ADR (no slivers)
STOPS = ("gap bottom", "gap's first candle", "sweep low")


def sweep_of(O, H, L, C, target: float, adr: float, need_eql: bool) -> dict | None:
    """The first 15m candle of the session that takes a pool (long case), while the opening gap is still open."""
    for k in range(6, len(C) - 1):
        if H[:k].max() >= target:
            return None
        lows = [i for i in range(0, k - 2) if (i == 0 or L[i] < L[max(0, i - 2):i].min()) and L[i] < L[i + 1:i + 3].min() and L[i] <= L[i + 1:k].min()]
        pools = ([(min(L[i], L[j]), max(L[i], L[j])) for a, i in enumerate(lows) for j in lows[a + 1:] if j - i >= MIN_APART and abs(L[i] - L[j]) <= EQ_TOL * adr]
                 if need_eql else [(L[i], L[i]) for i in lows])
        taken = [p for p in pools if L[k] < p[0]]
        if taken:
            return {"k": k, "level": min(taken)[0], "top": min(taken)[1]}
    return None


def fvg_entry(h1, l1, c1, o1, t1, start: int, end: int, top: float, target: float, adr: float) -> dict | None:
    """Sharif's entry (long case, 1m arrays of the session from the sweep candle's first bar ``start``): the push back
    leaves a 5m fair value gap above the swept pool; a resting buy at the gap's 50%, moved to each newer gap; filled on
    the retrace while the opening gap is still open. Returns the fill and the three stop candidates."""
    n5 = (end - start) // 5
    if n5 < 4:
        return None
    H5 = h1[start:start + n5 * 5].reshape(n5, 5).max(1)
    L5 = l1[start:start + n5 * 5].reshape(n5, 5).min(1)
    sweep_low, limit, gap = l1[start], None, None
    for j in range(start, end):
        i5 = (j - start) // 5
        if (j - start) % 5 == 0 and i5 >= 3:               # the 5m candle i5-1 has just closed
            i = i5 - 1
            if L5[i] > H5[i - 2] and L5[i] - H5[i - 2] >= MIN_FVG * adr and H5[i - 2] > top:
                gap = {"bottom": float(H5[i - 2]), "top": float(L5[i]), "first_low": float(L5[i - 2])}
                limit = (gap["bottom"] + gap["top"]) / 2
        if limit is not None and l1[j] <= limit:
            if limit >= target:
                return None
            fill = min(limit, o1[j])
            return {"j": j, "entry": float(fill), "stops": {"gap bottom": gap["bottom"], "gap's first candle": gap["first_low"], "sweep low": float(sweep_low)}}
        if h1[j] >= target:
            return None                                    # the opening gap closed without us
        if limit is None:
            sweep_low = min(sweep_low, l1[j])
    return None


def run_fvg(asset: str, start: date = nd.START, end: date = nd.END) -> pd.DataFrame:
    bars = dukascopy.load(asset, start - timedelta(days=45), end)
    o, h, lo, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    daily = bars.resample("1D").agg({"high": "max", "low": "min"}).dropna()
    adr_s = (daily.high - daily.low).rolling(20).mean().shift(1)
    ns = bars.index.tz_convert("UTC").as_unit("ns").asi8
    rows = []
    for s in nd.sessions(bars):
        if s["open_ts"] < pd.Timestamp(start, tz=nd.NY):
            continue
        adr = adr_s.asof(s["open_ts"].normalize())
        gap = s["prev_close"] - s["open"]
        if not adr or adr <= 0 or gap == 0:
            continue
        long = gap > 0
        sg = 1.0 if long else -1.0
        f = bars.iloc[s["open_i"]:s["end_i"]][list(AGG)].resample("15min", label="left", closed="left").agg(AGG).dropna()
        O, C = f.open.to_numpy() * sg, f.close.to_numpy() * sg
        H, L = (f.high.to_numpy(), f.low.to_numpy()) if long else (-f.low.to_numpy(), -f.high.to_numpy())
        h1, l1 = (h, lo) if long else (-lo, -h)
        for pool, need_eql in (("any low", False), ("equal lows", True)):
            sw = sweep_of(O, H, L, C, s["prev_close"] * sg, adr, need_eql)
            if sw is None:
                continue
            j0 = int(np.searchsorted(ns, f.index[sw["k"]].tz_convert("UTC").value))
            x = fvg_entry(h1, l1, c * sg, o * sg, None, j0, s["end_i"], sw["top"], s["prev_close"] * sg, adr)
            if x is None:
                continue
            entry, target = x["entry"] * sg, s["prev_close"]
            for stop_name, st in x["stops"].items():
                stop = st * sg
                risk = abs(entry - stop)
                if risk <= 0:
                    continue
                t = nd.trade(o, h, lo, c, x["j"], s["end_i"], long, entry, stop, target)
                cost = cost_at(asset, entry, bars.index[x["j"]]) / risk
                rows.append({"pool": pool, "stop_at": stop_name, "asset": asset, "side": "buy (gap above)" if long else "sell (gap below)",
                             "open_ts": s["open_ts"], "day": (s["open_ts"].normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                             "weekend": s["weekend"], "gap_adr": abs(gap) / adr, "entry_at": bars.index[x["j"]], "entry": entry, "stop": stop,
                             "target": target, "rr": abs(target - entry) / risk, "risk_adr": risk / adr, "exit": t["exit"], "r": t["r"] - cost})
    return pd.DataFrame(rows)


def run_asset(asset: str, start: date = nd.START, end: date = nd.END) -> pd.DataFrame:
    bars = dukascopy.load(asset, start - timedelta(days=45), end)
    o, h, lo, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    daily = bars.resample("1D").agg({"high": "max", "low": "min"}).dropna()
    adr_s = (daily.high - daily.low).rolling(20).mean().shift(1)
    ns = bars.index.tz_convert("UTC").as_unit("ns").asi8
    rows = []
    for s in nd.sessions(bars):
        if s["open_ts"] < pd.Timestamp(start, tz=nd.NY):
            continue
        adr = adr_s.asof(s["open_ts"].normalize())
        gap = s["prev_close"] - s["open"]
        if not adr or adr <= 0 or gap == 0:
            continue
        long = gap > 0
        sg = 1.0 if long else -1.0
        f = bars.iloc[s["open_i"]:s["end_i"]][list(AGG)].resample("15min", label="left", closed="left").agg(AGG).dropna()
        O, C = f.open.to_numpy() * sg, f.close.to_numpy() * sg
        H, L = (f.high.to_numpy(), f.low.to_numpy()) if long else (-f.low.to_numpy(), -f.high.to_numpy())
        for name, (eql, disp) in VERSIONS.items():
            x = find(O, H, L, C, s["prev_close"] * sg, adr, eql, disp)
            if x is None:
                continue
            entry, stop, target = x["entry"] * sg, x["stop"] * sg, s["prev_close"]
            t_entry = f.index[x["m"]] + pd.Timedelta(minutes=15)
            j = int(np.searchsorted(ns, t_entry.tz_convert("UTC").value))
            if j >= s["end_i"]:
                continue
            t = nd.trade(o, h, lo, c, j, s["end_i"], long, entry, stop, target)
            risk = abs(entry - stop)
            cost = cost_at(asset, entry, t_entry) / risk
            rows.append({"version": name, "asset": asset, "side": "buy (gap above)" if long else "sell (gap below)", "open_ts": s["open_ts"],
                         "day": (s["open_ts"].normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), "weekend": s["weekend"],
                         "gap_adr": abs(gap) / adr, "entry_at": t_entry, "entry": entry, "stop": stop, "target": target,
                         "rr": abs(target - entry) / risk, "risk_adr": risk / adr, "displacement": x["displacement"],
                         "exit": t["exit"], "r": t["r"] - cost})
    return pd.DataFrame(rows)


def nd_session(ts: pd.Timestamp) -> str:
    m = ts.hour * 60 + ts.minute
    return ("evening + Asia 18:00–02:00" if m >= 1080 or m < 120 else "London 02:00–07:00" if m < 420 else
            "NY morning 07:00–12:00" if m < 720 else "NY afternoon 12:00–17:00")


def stat(g: pd.DataFrame) -> str:
    n = len(g)
    if n < 3:
        return f"{n} | – | – | –"
    sd = g.r.std()
    return f"{n} | {100 * (g.exit == 'tp').mean():.1f} | {g.r.mean():+.3f} | {g.r.mean() / sd * math.sqrt(n):+.2f}"


def main():
    t = pd.concat([run_asset(a) for a in nd.ASSETS], ignore_index=True)
    t["year"] = t.day.str.slice(0, 4)
    t["size"] = pd.cut(t.gap_adr, [0, 0.05, 0.1, 0.2, 0.4, 10], labels=["< 0.05", "0.05–0.1", "0.1–0.2", "0.2–0.4", "> 0.4"])
    t.to_parquet("reports/ndog-eql-trades.parquet")
    md = [f"# The gap as a target after equal lows are swept and price pushes back ({date.today()})", "",
          f"Sharif's explanation of his gap trade, coded in `research/scripts/ndog_eql.py`. Three indices, {nd.START} → {nd.END}, futures cost, "
          "one trade per session at most. **Descriptive, in-sample; nothing here is a tested rule.** Win = the gap's far edge before the stop.", "",
          "## The four versions", "", "| Liquidity swept, then | Trades | Win % | R per trade (net) | z |", "|---|---|---|---|---|"]
    md += [f"| {v} | {stat(t[t.version == v])} |" for v in VERSIONS]
    full = t[t.version == "equal lows, displacement"]
    for col, title in (("size", "Gap size (ADR)"), ("asset", "Index"), ("year", "Year"), ("side", "Side"), ("weekend", "Weekend gap")):
        md += ["", f"## Equal lows + displacement, by {title.lower()}", "", f"| {title} | Trades | Win % | R per trade (net) | z |", "|---|---|---|---|---|"]
        md += [f"| {k} | {stat(g)} |" for k, g in full.groupby(col, observed=True)]
    md += ["", f"Equal lows + displacement: median reward:risk {full.rr.median():.2f}, median risk {full.risk_adr.median():.2f} ADR; exits "
           + ", ".join(f"{k} {v}" for k, v in full.exit.value_counts().items()) + "."]
    v = pd.concat([run_fvg(x) for x in nd.ASSETS], ignore_index=True)
    v["year"] = v.day.str.slice(0, 4)
    v["size"] = pd.cut(v.gap_adr, [0, 0.05, 0.1, 0.2, 0.4, 10], labels=["< 0.05", "0.05–0.1", "0.1–0.2", "0.2–0.4", "> 0.4"])
    v["hour"] = v.entry_at.map(nd_session)
    v.to_parquet("reports/ndog-fvg-trades.parquet")
    md += ["", "## His entry: the retrace into the push's 5m fair value gap, at its 50%", "",
           "After the pool is swept, the push back leaves a 5m gap above the pool; buy its 50% on the retrace (the newest gap), while the opening gap is still open; "
           "target the opening gap's far edge. Three stop placements.", "",
           "| Pool swept | Stop | Trades | Win % | R per trade (net) | z | Median reward:risk |", "|---|---|---|---|---|---|---|"]
    for (pool, stp), g in v.groupby(["pool", "stop_at"]):
        md.append(f"| {pool} | {stp} | {stat(g)} | {g.rr.median():.2f} |")
    best = v[(v.pool == "equal lows") & (v.stop_at == "gap's first candle")]
    for col, title in (("size", "Gap size (ADR)"), ("asset", "Index"), ("year", "Year"), ("side", "Side"), ("hour", "When it filled (New York)"), ("weekend", "Weekend gap")):
        md += ["", f"### Equal lows, stop under the gap's first candle, by {title.lower()}", "", f"| {title} | Trades | Win % | R per trade (net) | z |", "|---|---|---|---|---|"]
        md += [f"| {k} | {stat(g)} |" for k, g in best.groupby(col, observed=True)]
    Path("research/ndog").mkdir(parents=True, exist_ok=True)
    Path(f"research/ndog/{date.today()}-eql-study.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
