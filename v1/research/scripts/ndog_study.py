"""Closing the opening gap (NDOG), from Sharif's first note on the live sheet (2026-11-16, US100 11–12 Nov 2026).

His words: "Notice this NDOG, price will normally try to clean it up … with a buy closing it above and a sell closing
it below. Notice how we swept sellside and quickly reached into it."

The gap = the last price before the 17:00 New York close → the 18:00 open (on this CFD feed the last bar is 16:14).
A gap above the open is closed by a buy; a gap below by a sell. Three things are measured, per futures session
(18:00 → 16:55):
  A. how often the gap is reached (its near edge is the open itself), half filled (CE) and fully closed
  B. "at the open": trade toward the close of the gap from the 18:00 open, stop one gap-size away, target the far edge
  C. his trade: wait for a sweep of the liquidity on the other side (a session low that has stood ≥ 3 hours, for a
     buy), then a 15m close back above it → enter; stop under the sweep; target the gap's far edge. Only while the gap
     is still open.
Descriptive and in-sample. Futures cost.

    uv run python research/scripts/ndog_study.py     → reports/ndog-sessions.parquet, research/ndog/<date>-study.md
"""
from __future__ import annotations

import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.data import dukascopy  # noqa: E402
from ict_engine.data.instruments import cost_at  # noqa: E402

NY = "America/New_York"
ASSETS = ("US100", "US500", "US30")
START, END = date(2020, 1, 2), date(2026, 11, 13)
OLD_MIN = 180                      # a session low / high counts as resting liquidity once it has stood 3 hours


def sessions(bars: pd.DataFrame) -> list[dict]:
    """One row per futures session: the previous close, the 18:00 open and the bar positions of the session
    (open → the last bar before 16:55 the next trading day)."""
    t = bars.index
    mins = (t.hour * 60 + t.minute).to_numpy()
    ns = t.tz_convert("UTC").as_unit("ns").asi8
    since_prev = np.r_[0, np.diff(ns)] / 6e10               # minutes since the previous bar
    opens = np.flatnonzero((mins >= 1080) & (mins <= 1110) & (since_prev >= 45))   # first bar of the evening, after the break
    out = []
    for i in opens:
        prev = i - 1
        end_ts = (t[i].normalize() + pd.Timedelta(days=1, hours=16, minutes=55))
        j = int(np.searchsorted(ns, end_ts.value))
        if j - i < 600:                                    # a holiday stub
            continue
        out.append({"open_i": int(i), "end_i": j, "open_ts": t[i], "prev_close": float(bars.close.iloc[prev]),
                    "open": float(bars.open.iloc[i]), "weekend": (t[i] - t[prev]) > pd.Timedelta(hours=30)})
    return out


def fill_stats(o, h, lo, c, s: dict) -> dict:
    """A. Did the session reach the gap's 50% and its far edge (the previous close), and when (minutes from the open)?"""
    a, b = s["open_i"], s["end_i"]
    up = s["prev_close"] > s["open"]                       # the gap is above the open: a buy closes it
    reach = h[a:b] if up else lo[a:b]
    ce = (s["prev_close"] + s["open"]) / 2
    hit = lambda lv: np.flatnonzero(reach >= lv if up else reach <= lv)  # noqa: E731
    k_ce, k_full = hit(ce), hit(s["prev_close"])
    return {"ce_min": int(k_ce[0]) if len(k_ce) else None, "full_min": int(k_full[0]) if len(k_full) else None}


def trade(o, h, lo, c, start: int, end: int, long: bool, entry: float, stop: float, target: float) -> dict:
    """Stop first when both trade in one bar; flat at the close of the session's last bar."""
    s = 1.0 if long else -1.0
    risk = abs(entry - stop)
    for k in range(start, end):
        against, ours = (lo[k], h[k]) if long else (h[k], lo[k])
        if (stop - against) * s >= 0:
            return {"exit": "stop", "r": -1.0, "exit_i": k}
        if (ours - target) * s >= 0:
            return {"exit": "tp", "r": abs(target - entry) / risk, "exit_i": k}
    return {"exit": "time", "r": (c[end - 1] - entry) * s / risk, "exit_i": end - 1}


def at_open(o, h, lo, c, s: dict) -> dict | None:
    """B. From the 18:00 open toward the previous close; the stop one gap-size the other way (1 R = the gap)."""
    gap = s["prev_close"] - s["open"]
    if gap == 0:
        return None
    return {"entry": s["open"], "stop": s["open"] - gap, "target": s["prev_close"],
            **trade(o, h, lo, c, s["open_i"] + 1, s["end_i"], gap > 0, s["open"], s["open"] - gap, s["prev_close"])}


def after_sweep(o, h, lo, c, mins, s: dict, old_min: int = OLD_MIN) -> dict | None:
    """C. Gap above (a buy): the session low that has stood ``old_min`` minutes is traded through, then a 15m candle
    closes back above it while the gap is still open → buy that close; stop under the sweep's low; target the gap's
    far edge. Mirror for a gap below."""
    a, b = s["open_i"], s["end_i"]
    long = s["prev_close"] > s["open"]
    sg = 1.0 if long else -1.0
    target = s["prev_close"]
    ours = h if long else lo                               # toward the gap
    against = lo if long else h
    swept_level, sweep_ext, sweep_at = None, None, None
    for j in range(a + old_min, b - 30):
        if (ours[a:j + 1].max() if long else ours[a:j + 1].min()) * sg >= target * sg:
            return None                                    # the gap closed before any setup
        if swept_level is None:
            old = against[a:j - old_min + 1].min() if long else against[a:j - old_min + 1].max()
            cur = against[j - old_min + 1:j].min() if long else against[j - old_min + 1:j].max()
            rest = min(old, cur) if long else max(old, cur)          # the session extreme before this bar
            if (old - rest) * sg > 0:                      # the old extreme was already taken inside the last 3 hours
                continue
            if (old - against[j]) * sg > 0:
                swept_level, sweep_ext, sweep_at = old, against[j], j
            continue
        sweep_ext = min(sweep_ext, against[j]) if long else max(sweep_ext, against[j])
        if mins[j] % 15 == 14 and (c[j] - swept_level) * sg > 0:      # the 15m candle closing at this bar
            entry = c[j]
            if (target - entry) * sg <= 0 or entry == sweep_ext:
                return None
            return {"entry": float(entry), "stop": float(sweep_ext), "target": float(target), "swept": float(swept_level),
                    "sweep_i": sweep_at, "entry_i": j, "rr": abs(target - entry) / abs(entry - sweep_ext),
                    **trade(o, h, lo, c, j + 1, b, long, entry, sweep_ext, target)}
    return None


def run_asset(asset: str, start: date = START, end: date = END) -> pd.DataFrame:
    bars = dukascopy.load(asset, start - timedelta(days=45), end)
    o, h, lo, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    mins = (bars.index.hour * 60 + bars.index.minute).to_numpy()
    daily = bars.resample("1D").agg({"high": "max", "low": "min"}).dropna()
    adr = (daily.high - daily.low).rolling(20).mean().shift(1)
    rows = []
    for s in sessions(bars):
        if s["open_ts"] < pd.Timestamp(start, tz=NY):
            continue
        a = adr.asof(s["open_ts"].normalize())
        gap = s["prev_close"] - s["open"]
        row = {"asset": asset, "open_ts": s["open_ts"], "day": (s["open_ts"].normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
               "weekend": s["weekend"], "gap": gap, "gap_adr": abs(gap) / a if a and a > 0 else np.nan,
               "side": "buy (gap above)" if gap > 0 else "sell (gap below)", **fill_stats(o, h, lo, c, s)}
        for name, t in (("open", at_open(o, h, lo, c, s)), ("sweep", after_sweep(o, h, lo, c, mins, s))):
            if t is None:
                continue
            cost = cost_at(asset, t["entry"], s["open_ts"]) / abs(t["entry"] - t["stop"])
            row.update({f"{name}_exit": t["exit"], f"{name}_r": t["r"] - cost, f"{name}_rr": t.get("rr", 1.0), f"{name}_cost_r": cost})
            if name == "sweep":
                row.update(sweep_entry_at=bars.index[t["entry_i"]], sweep_entry=t["entry"], sweep_stop=t["stop"], sweep_target=t["target"],
                           sweep_risk_adr=abs(t["entry"] - t["stop"]) / a if a and a > 0 else np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def stat(g: pd.DataFrame, col: str) -> str:
    g = g[g[col + "_r"].notna()]
    n = len(g)
    if n < 3:
        return f"{n} | – | – | –"
    r = g[col + "_r"]
    return f"{n} | {100 * (g[col + '_exit'] == 'tp').mean():.1f} | {r.mean():+.3f} | {r.mean() / r.std() * math.sqrt(n):+.2f}"


def main():
    t = pd.concat([run_asset(a) for a in ASSETS], ignore_index=True)
    t["year"] = t.day.str.slice(0, 4)
    t["size"] = pd.cut(t.gap_adr, [0, 0.02, 0.05, 0.1, 0.2, 0.4, 10], labels=["< 0.02", "0.02–0.05", "0.05–0.1", "0.1–0.2", "0.2–0.4", "> 0.4"])
    reg = Path("reports/regimes.parquet")
    if reg.exists():
        t = t.merge(pd.read_parquet(reg)[["asset", "day", "vol", "state", "news"]], on=["asset", "day"], how="left")
    t.to_parquet("reports/ndog-sessions.parquet")
    md = [f"# Closing the opening gap: first look ({date.today()})", "",
          "From Sharif's first note on the live sheet (US100, 11–12 Nov 2026). Rule and code: `research/scripts/ndog_study.py`. "
          f"Three indices, {START} → {END}; the gap = the feed's last price before 17:00 New York → the 18:00 open; the session runs to 16:55. "
          "**Descriptive, in-sample; nothing here is a tested rule.** Gap size is in ADR (20-day average daily range).", "",
          "## A. Does the session close the gap?", "",
          "| Gap size (ADR) | Sessions | Reaches 50% | Fully closed | Closed within 2 h | Median minutes to close |", "|---|---|---|---|---|---|"]
    for k, g in t.groupby("size", observed=True):
        f = g.full_min.dropna()
        md.append(f"| {k} | {len(g)} | {100 * g.ce_min.notna().mean():.0f}% | {100 * g.full_min.notna().mean():.0f}% | {100 * (g.full_min < 120).mean():.0f}% | {f.median():.0f} |" if len(f) else f"| {k} | {len(g)} | – | – | – | – |")
    for name, title in (("open", "B. Trading toward the gap from the 18:00 open (stop one gap-size away, target the far edge)"),
                        ("sweep", "C. His trade: after a sweep of 3-hour-old session liquidity on the other side and a 15m close back (stop under the sweep, target the gap's far edge)")):
        md += ["", f"## {title}", "", "| Cut | Trades | Win % | R per trade (net) | z |", "|---|---|---|---|---|", f"| all | {stat(t, name)} |"]
        for col in ("size", "asset", "year", "side", "weekend", "vol", "news"):
            if col in t:
                md += [f"| {col}: {k} | {stat(g, name)} |" for k, g in t.dropna(subset=[col]).groupby(col, observed=True)]
    sw = t[t.sweep_r.notna()]
    md += ["", f"Sweep trades: median reward:risk {sw.sweep_rr.median():.2f}, median risk {sw.sweep_risk_adr.median():.2f} ADR; exits "
           + ", ".join(f"{k} {v}" for k, v in sw.sweep_exit.value_counts().items()) + "."]
    Path("research/ndog").mkdir(parents=True, exist_ok=True)
    Path(f"research/ndog/{date.today()}-study.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
