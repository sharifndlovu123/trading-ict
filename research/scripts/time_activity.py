"""Entry time and market activity for every traded row of many backtests (fast: only the activity fact, no read).

    uv run python research/scripts/time_activity.py   → reports/time-activity-2026-11-16.parquet

Activity = the range of the 60 minutes before the fill ÷ the median range of the same clock window over the previous
20 weekdays (trade_eval.activity, vectorised): < 0.6 quiet, > 1.5 busy. Known at the fill. Unseen data (2024-07+) is
never loaded.
"""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.concepts.liquidity_map import _daily  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402

NY = "America/New_York"
MODELS = {"2022_model": "backtest-{a}", "mmxm": "backtest-mmxm-{a}", "silver_bullet": "backtest-silver_bullet-{a}",
          "cameron": "backtest-cameron-{a}"}
SETS = [("2022-24", a, "2022-01-03-2024-06-28") for a in ("US100", "US500", "US30", "XAUUSD")] + \
       [("2020", a, "2020-01-02-2020-12-31") for a in ("US100", "US500", "US30")]


def window_range(idx: np.ndarray, hi: np.ndarray, lo: np.ndarray, t1: np.datetime64, mins: int = 60):
    a, b = np.searchsorted(idx, t1 - np.timedelta64(mins, "m")), np.searchsorted(idx, t1)
    return None if b - a < mins // 2 else float(hi[a:b].max() - lo[a:b].min())


def activity_fast(idx, hi, lo, t: pd.Timestamp, days: int = 20):
    """(range now, range ÷ the median of the same NY clock window on the previous ``days`` weekdays)."""
    now = window_range(idx, hi, lo, np.datetime64(t.tz_convert("UTC").tz_localize(None)))
    past = []
    for k in range(1, days * 2):
        p = t - pd.Timedelta(days=k)                       # same NY wall-clock time (DST-aware)
        if p.weekday() >= 5:
            continue
        r = window_range(idx, hi, lo, np.datetime64(p.tz_convert("UTC").tz_localize(None)))
        if r is not None:
            past.append(r)
        if len(past) >= days:
            break
    med = float(np.median(past)) if past else None
    return now, (now / med if now is not None and med else None)


def main():
    out = []
    for a in sorted({s[1] for s in SETS}):
        b = dukascopy.load(a, date(2019, 10, 1) if a.startswith("US") else date(2021, 10, 1), date(2024, 7, 1))
        idx = b.index.tz_convert("UTC").tz_localize(None).to_numpy()
        hi, lo = b.high.to_numpy(), b.low.to_numpy()
        dd = _daily(b)
        adr = (dd.high - dd.low).rolling(20).mean().shift(1)
        adr.index = pd.DatetimeIndex(dd.index).tz_localize(None).normalize()
        for per, asset, span in SETS:
            if asset != a:
                continue
            for m, pat in MODELS.items():
                f = Path(f"reports/{pat.format(a=a)}-{span}-futures.parquet")
                if not f.exists():
                    continue
                d = pd.read_parquet(f)
                d = d[(d.status == "traded") & d.r.notna() & d.filled_at.notna()].copy()
                if d.empty:
                    continue
                d["filled_at"] = pd.to_datetime(d.filled_at, utc=True).dt.tz_convert(NY)
                res = [activity_fast(idx, hi, lo, t) for t in d.filled_at]
                d["act_range"], d["act_rel"] = [r[0] for r in res], [r[1] for r in res]
                day = d.filled_at.dt.tz_localize(None).dt.normalize()
                d["adr"] = adr.reindex(day, method="ffill").to_numpy()
                d["act_range_adr"], d["risk_adr"] = d.act_range / d.adr, d.risk / d.adr
                d["activity"] = np.select([d.act_rel < 0.6, d.act_rel > 1.5], ["quiet", "busy"], "normal")
                d["period"], d["family"], d["fill_hour"] = per, m, d.filled_at.dt.hour
                d["win"] = d.vote.map(lambda v: v is True or v == 1)
                keep = ["period", "family", "asset", "model", "side", "filled_at", "fill_hour", "window", "weekday", "r",
                        "runner_r", "win", "cf_tp1_1r_r", "cf_tp1_1r_vote", "tp1_r", "risk_adr", "act_rel", "act_range_adr",
                        "activity", "news", "bias", "liquidity_kind", "exit"]
                out.append(d[[c for c in keep if c in d]])
        print(a, sum(len(x) for x in out), flush=True)
    o = pd.concat(out, ignore_index=True)
    o.to_parquet("reports/time-activity-2026-11-16.parquet")
    print(len(o), "trades → reports/time-activity-2026-11-16.parquet")


if __name__ == "__main__":
    main()
