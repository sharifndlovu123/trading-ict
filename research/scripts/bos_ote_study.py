"""BOS → OTE return, from Sharif's notes on the live sheet (2026-11-16, US100 11–16 Nov 2026).

His words: "Notice BOS here, and please check what the range is here, OTE I'm sure, or the breaker works too. And our
first TP would have been the PDL."

The sequence, as coded here (short side; longs mirror):
  1. a 1h candle CLOSES below the most recent confirmed 1h swing low (3 candles each side)  → break of structure
  2. the range = the highest high since that swing low formed  →  the lowest low since (it stretches while price
     keeps falling before the retrace)
  3. a resting limit at a retrace level of that range (0.62 = the start of the OTE); cancelled when 1h structure
     breaks the other way or after 3 days
  4. stop beyond the range high; first target the range low (the liquidity under the leg, the PDL when the entry is
     the next day); flat at 16:55 New York of the futures session the fill belongs to (18:00 → 16:55)
Any hour, including the Sunday open. Futures cost. Descriptive and in-sample: every period here has been looked at.

    uv run python research/scripts/bos_ote_study.py      → reports/bos-ote-trades.parquet, research/bos-ote/<date>-study.md
"""
from __future__ import annotations

import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.concepts.bars import resample  # noqa: E402
from ict_engine.concepts.events import structure  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402
from ict_engine.data.instruments import cost_at  # noqa: E402

NY = "America/New_York"
ASSETS = ("US100", "US500", "US30")
START, END = date(2020, 1, 2), date(2026, 11, 13)
STRENGTH = 3                      # the broken 1h swing: 3 candles each side
EXPIRY_MIN = 3 * 1380             # a resting order lives 3 trading days of 1m bars
ENTRIES = (0.5, 0.62, 0.705, 0.79)
PRIMARY = 0.62


def session_flat(ts: pd.Timestamp) -> pd.Timestamp:
    """16:55 New York of the futures session ``ts`` belongs to (a fill from 18:00 on belongs to the next day)."""
    d = ts.normalize() + pd.Timedelta(days=1) if ts.hour >= 17 else ts.normalize()
    while d.dayofweek >= 5:
        d += pd.Timedelta(days=1)
    return d + pd.Timedelta(hours=16, minutes=55)


def breaks(bars_1m: pd.DataFrame, strength: int = STRENGTH) -> list[dict]:
    """1h structure breaks with the range each one leaves: ``far`` = the extreme since the broken swing formed (the
    range's protected end) and ``near0`` = the extreme of the break so far, both known at the break's close."""
    h1 = resample(bars_1m, "1h")
    out = []
    for e in structure(h1, "1h", strength=strength):
        seg = h1[(h1.index >= e.meta["broken_swing"]) & (h1.index <= e.origin_ts)]
        if seg.empty:
            continue
        short = e.direction == "bear"
        far = float(seg.high.max()) if short else float(seg.low.min())
        far_at = seg.high.idxmax() if short else seg.low.idxmin()
        leg = seg[seg.index >= far_at]
        near0 = float(leg.low.min()) if short else float(leg.high.max())
        out.append({"ts": e.ts, "short": short, "kind": e.kind, "far": far, "near0": near0,
                    "displacement": bool(e.meta.get("displacement"))})
    return out


def replay(idx, o, h, lo, c, ev: dict, frac: float, cancel_at) -> dict | None:
    """One break → at most one trade. Arrays are the asset's 1m bars; ``cancel_at`` = the next break the other way."""
    s = 1.0 if ev["short"] else -1.0                      # work in "short space": prices × s flip a long into a short
    far, near = ev["far"], ev["near0"]
    i0 = int(np.searchsorted(idx, ev["ts"].value))
    end = min(len(idx), i0 + EXPIRY_MIN)
    for j in range(i0, end):
        if cancel_at is not None and idx[j] >= cancel_at:
            return None
        hi_j, lo_j = (h[j], lo[j]) if ev["short"] else (lo[j], h[j])     # "against us" / "our way" extremes
        entry = near + frac * (far - near)
        if (hi_j - entry) * s >= 0 and abs(far - near) > 0:
            fill = entry if (o[j] - entry) * s <= 0 else o[j]            # a gap through the limit fills at the open
            return _after_fill(idx, o, h, lo, c, j, ev, fill, far, near, frac)
        if (near - lo_j) * s > 0:                          # the leg stretches before the retrace
            near = lo_j
    return None


def _after_fill(idx, o, h, lo, c, j, ev, fill, far, near, frac) -> dict | None:
    s = 1.0 if ev["short"] else -1.0
    risk = abs(far - fill)
    if risk <= 0:
        return None
    t_fill = pd.Timestamp(idx[j], tz="UTC").tz_convert(NY)
    flat = session_flat(t_fill).tz_convert("UTC").value
    rr = abs(fill - near) / risk
    out = {"filled_at": t_fill, "entry": fill, "stop": far, "tp1": near, "risk": risk, "rr": rr, "frac": frac,
           "range": abs(far - near)}
    mfe = 0.0
    if ((h[j] if ev["short"] else lo[j]) - far) * s >= 0:   # the fill bar also traded the stop: a loss
        return {**out, "exit": "stop", "exit_at": t_fill, "r": -1.0, "mfe": 0.0}
    for k in range(j + 1, len(idx)):
        if idx[k] >= flat:
            px = c[k - 1]
            return {**out, "exit": "time", "exit_at": pd.Timestamp(idx[k - 1], tz="UTC").tz_convert(NY), "r": (fill - px) * s / risk, "mfe": mfe}
        against, ours = (h[k], lo[k]) if ev["short"] else (lo[k], h[k])
        if (against - far) * s >= 0:                       # stop first when both trade in one bar
            return {**out, "exit": "stop", "exit_at": pd.Timestamp(idx[k], tz="UTC").tz_convert(NY), "r": -1.0, "mfe": mfe}
        mfe = max(mfe, (fill - ours) * s / risk)
        if (near - ours) * s >= 0:
            return {**out, "exit": "tp1", "exit_at": pd.Timestamp(idx[k], tz="UTC").tz_convert(NY), "r": rr, "mfe": mfe}
    return None


def run_asset(asset: str, start: date = START, end: date = END) -> pd.DataFrame:
    bars = dukascopy.load(asset, start - timedelta(days=30), end)
    evs = [e for e in breaks(bars) if e["ts"] >= pd.Timestamp(start, tz=NY)]
    idx = bars.index.tz_convert("UTC").as_unit("ns").asi8     # ns: Timestamp.value is ns whatever the index unit
    o, h, lo, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    daily = bars.resample("1D").agg({"high": "max", "low": "min"}).dropna()
    adr = (daily.high - daily.low).rolling(20).mean().shift(1)
    rows = []
    for frac in ENTRIES:
        busy = None                                        # one idea at a time per index (per entry level)
        for n, ev in enumerate(evs):
            if busy is not None and ev["ts"] <= busy:
                continue
            nxt = next((x["ts"] for x in evs[n + 1:] if x["short"] != ev["short"]), None)
            t = replay(idx, o, h, lo, c, ev, frac, nxt.tz_convert("UTC").value if nxt is not None else None)
            if t is None:
                continue
            busy = t["exit_at"]
            a = adr.asof(t["filled_at"].normalize())
            cost = cost_at(asset, t["entry"], t["filled_at"]) / t["risk"]
            rows.append({"asset": asset, "side": "short" if ev["short"] else "long", "break_at": ev["ts"], "kind": ev["kind"],
                         "displacement": ev["displacement"], **t, "cost_r": cost, "r_net": t["r"] - cost,
                         "range_adr": t["range"] / a if a and a > 0 else np.nan,
                         "wait_h": (t["filled_at"] - ev["ts"]).total_seconds() / 3600})
    return pd.DataFrame(rows)


def stat(g: pd.DataFrame) -> str:
    n = len(g)
    if n < 2:
        return f"n {n}"
    w = (g.exit == "tp1").mean()
    sd = g.r_net.std()
    return f"{n} | {100 * w:.1f} | {g.r_net.mean():+.3f} | {g.r_net.mean() / sd * math.sqrt(n):+.2f}" if sd > 0 else f"{n} | {100 * w:.1f} | {g.r_net.mean():+.3f} | –"


def session_of(ts: pd.Timestamp) -> str:
    m = ts.hour * 60 + ts.minute
    return ("evening open 18:00–20:00" if m >= 1080 and m < 1200 else "Asia 20:00–02:00" if m >= 1200 or m < 120 else
            "London 02:00–07:00" if m < 420 else "NY morning 07:00–12:00" if m < 720 else "NY afternoon 12:00–17:00")


def main():
    t = pd.concat([run_asset(a) for a in ASSETS], ignore_index=True)
    t["day"] = t.filled_at.map(lambda x: session_flat(x).strftime("%Y-%m-%d"))
    t["year"] = t.day.str.slice(0, 4)
    t["session"] = t.filled_at.map(session_of)
    reg = Path("reports/regimes.parquet")
    if reg.exists():
        t = t.merge(pd.read_parquet(reg)[["asset", "day", "vol", "state", "backdrop", "news"]], on=["asset", "day"], how="left")
    t.to_parquet("reports/bos-ote-trades.parquet")
    p = t[t.frac == PRIMARY]
    md = [f"# BOS → OTE return: first look ({date.today()})", "",
          "From Sharif's notes on the live sheet (US100, 11–16 Nov 2026). Rule and code: `research/scripts/bos_ote_study.py`. "
          f"Three indices, {START} → {END}, futures cost, flat at 16:55 of the fill's session. **Descriptive, in-sample: every period "
          "here has been looked at; nothing below is a tested rule.** Win = the range low / high (TP1) before the stop.", "",
          "## Entry level (stop beyond the range's far end, TP1 the leg's extreme)", "",
          "| Retrace level | Trades | Win % | R per trade (net) | z |", "|---|---|---|---|---|"]
    md += [f"| {f:g} | {stat(t[t.frac == f])} |" for f in ENTRIES]
    for col, title in (("asset", "Index"), ("year", "Year"), ("side", "Side"), ("session", "When the order filled (New York)"),
                       ("kind", "Break kind (bos = with the previous break, mss = against it)"), ("displacement", "Break candle was a displacement"),
                       ("vol", "Volatility state of the day"), ("news", "High-impact news that day"), ("state", "Market state")):
        if col not in p:
            continue
        md += ["", f"## {title} (entry at {PRIMARY:g})", "", f"| {title.split(' (')[0]} | Trades | Win % | R per trade (net) | z |", "|---|---|---|---|---|"]
        md += [f"| {k} | {stat(g)} |" for k, g in p.dropna(subset=[col]).groupby(col)]
    q = pd.qcut(p.range_adr, 4, duplicates="drop")
    md += ["", f"## Size of the range, in ADR (entry at {PRIMARY:g})", "", "| Range / ADR | Trades | Win % | R per trade (net) | z |", "|---|---|---|---|---|"]
    md += [f"| {k} | {stat(g)} |" for k, g in p.groupby(q, observed=True)]
    md += ["", f"Exits at {PRIMARY:g}: " + ", ".join(f"{k} {v}" for k, v in p.exit.value_counts().items())
           + f". Median wait from the break to the fill {p.wait_h.median():.1f} h; median reward:risk {p.rr.median():.2f}."]
    Path("research/bos-ote").mkdir(parents=True, exist_ok=True)
    out = Path(f"research/bos-ote/{date.today()}-study.md")
    out.write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
