"""Two-sided liquidity → follow the side price shows (research/preregistered-gravitation-2026-11-16.md).

    uv run python research/scripts/gravitation_test.py [--workers 4]   → reports/gravitation-calls.parquet + summary

Per asset and NY trading day (2022-01-03 → 2024-06-28) at 08:30: liquidity map → nearest top-down buyside above /
sellside below (1w ∪ 1d). Two-sided = both within 1.5 ADR. Signal = first 15m displacement candle (08:30 → 12:00)
closing beyond everything traded since 00:00. Outcome = which pool trades first on 1m within 5 trading days of the
signal. Baseline = driftless gambler's ruin from the signal close: p = d_other / (d_side + d_other).
"""
import argparse
import math
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.events import displacement_mask
from ict_engine.concepts.liquidity_map import build
from ict_engine.data import dukascopy

NY = "America/New_York"
ASSETS = ("US100", "US500", "US30", "XAUUSD")
START, END, OOS = date(2022, 1, 3), date(2024, 6, 28), date(2023, 9, 29)
REACH_ADR, DAYS = 1.5, 5


def at(d, hh, mm=0):
    return pd.Timestamp(datetime.combine(d, time(hh, mm)), tz=NY)


def pools(m):
    ids = {it["id"]: it for it in m["items"]}
    td = m["key"].get("topdown", {})
    up = [ids[i] for tf in td for i in td[tf]["buyside"] if ids[i]["where"] == "above"]
    dn = [ids[i] for tf in td for i in td[tf]["sellside"] if ids[i]["where"] == "below"]
    return (min(up, key=lambda it: it["price"]) if up else None), (max(dn, key=lambda it: it["price"]) if dn else None)


def signal(bars, d):
    """First 15m displacement (08:30 → 12:00) closing beyond everything since 00:00 → (side, close_ts, close)."""
    seg = bars[(bars.index >= at(d, 0) - timedelta(days=2)) & (bars.index < at(d, 12))]
    m15 = resample(seg, "15m")
    disp = displacement_mask(m15)
    since = bars[(bars.index >= at(d, 0)) & (bars.index < at(d, 12))]
    for i, (t, r) in enumerate(m15.iterrows()):
        if t < at(d, 8, 30) or r.close_ts > at(d, 12) or not disp[i]:
            continue
        before = since[since.index < t]
        if before.empty:
            continue
        if r.close > before.high.max():
            return "up", r.close_ts, float(r.close)
        if r.close < before.low.min():
            return "down", r.close_ts, float(r.close)
    return None


def run_asset(asset):
    bars = dukascopy.load(asset, date(2021, 10, 1), END + timedelta(days=14))
    days = sorted({t.date() for t in bars.index if START <= t.date() <= END and t.weekday() < 5})
    rows = []
    for d in days:
        row = {"asset": asset, "day": d, "oos": d >= OOS}
        if bars[(bars.index >= at(d, 8, 25)) & (bars.index <= at(d, 8, 30))].empty:
            continue
        try:
            m = build(bars, at(d, 8, 30))
        except ValueError:
            continue
        up, dn = pools(m)
        row.update(price=m["price"], adr=m["adr"], up=up and up["price"], down=dn and dn["price"],
                   up_id=up and up["id"], down_id=dn and dn["id"])
        two = bool(up and dn and up["dist"] <= REACH_ADR * m["adr"] and dn["dist"] <= REACH_ADR * m["adr"])
        row["two_sided"] = two
        if not two:
            rows.append(row); continue
        s = signal(bars, d)
        if s is None:
            row["call"] = None; rows.append(row); continue
        side, ts, px = s
        row.update(call=side, signal_at=ts, signal_px=px)
        after_days = [x for x in days if x >= d][:DAYS]
        end = at(after_days[-1], 17) if after_days else ts + timedelta(days=7)
        fwd = bars[(bars.index > ts) & (bars.index <= end)]
        hu = np.flatnonzero(fwd.high.to_numpy() >= up["price"])
        hd = np.flatnonzero(fwd.low.to_numpy() <= dn["price"])
        iu, idn = (hu[0] if len(hu) else None), (hd[0] if len(hd) else None)
        if px >= up["price"] or px <= dn["price"]:          # the signal candle itself took a pool
            first = "up" if px >= up["price"] else "down"
        elif iu is None and idn is None or iu is not None and iu == idn:
            first = None
        elif idn is None or (iu is not None and iu < idn):
            first = "up"
        else:
            first = "down"
        d_up, d_dn = max(up["price"] - px, 0.0), max(px - dn["price"], 0.0)
        d_side, d_other = (d_up, d_dn) if side == "up" else (d_dn, d_up)
        row.update(first_pool=first, d_side_adr=d_side / m["adr"], d_other_adr=d_other / m["adr"],
                   p=(d_other / (d_side + d_other)) if d_side + d_other > 0 else 0.5)
        rows.append(row)
    return rows


def summary(df, label):
    c = df[df["call"].notna() & df["first_pool"].notna()]
    if c.empty:
        return f"{label}: no calls"
    hit = (c["call"] == c["first_pool"]).astype(float)
    exp, var = c.p.sum(), (c.p * (1 - c.p)).sum()
    z = (hit.sum() - exp) / math.sqrt(var) if var > 0 else 0.0
    far = c[c.d_side_adr > c.d_other_adr]
    fr = (far["call"] == far["first_pool"]).mean() if len(far) else float("nan")
    return (f"{label}: n {len(c)} · hits {int(hit.sum())} ({hit.mean():.0%}) · expected {exp:.1f} ({exp / len(c):.0%}) · "
            f"edge {hit.sum() - exp:+.1f} · z {z:.2f} · signalled pool farther: {len(far)} calls, hit {fr:.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    with ProcessPoolExecutor(min(a.workers, 10)) as ex:
        rows = [r for rs in ex.map(run_asset, ASSETS) for r in rs]
    df = pd.DataFrame(rows)
    df.to_parquet("reports/gravitation-calls.parquet")
    n = len(df); two = df.two_sided.sum(); calls = df.call.notna().sum() if "call" in df else 0
    print(f"days {n} · two-sided {two} ({two / n:.0%}) · signal by 12:00 {calls} · "
          f"neither/both pool {(df["call"].notna() & df["first_pool"].isna()).sum()}")
    print(summary(df[~df.oos], "in-sample "))
    print(summary(df[df.oos], "OOS       "))
    for x in ASSETS:
        print("  ", summary(df[df.asset == x], x))


if __name__ == "__main__":
    main()
