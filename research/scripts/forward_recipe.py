"""Forward log of the recipe (research/forward-recipe-v1.md): append the frozen variant's new trades with their
conditions. Prints counts only until the first-look condition is met.

    uv run python research/scripts/forward_recipe.py [--no-fetch] [--end YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

START = date(2026, 11, 14)                       # the first day after the data used to choose the candidates
ASSETS = ("US100", "US500", "US30")
VARIANT = "recipe4: recipe3, mornings only"
OUT = Path("reports/forward/recipe-forward.parquet")
LOG = Path("research/forward/recipe-forward-log.md")
FIRST_LOOK_N, FIRST_LOOK_DATE = 60, date(2027, 11, 16)
NY = "America/New_York"


def tag(t: pd.DataFrame) -> pd.DataFrame:
    """Conditions known before the day (regime, news, weekday, session) and at the fill (range half)."""
    from ict_engine.concepts.liquidity_map import _daily
    from ict_engine.concepts.regime import daily_regimes
    from ict_engine.data import dukascopy
    from ict_engine.news import calendar
    from ict_engine.news.holidays import session_note
    import trade_eval as te
    from review_sample import traits, _tps
    cal = calendar.load()
    news_days = set(cal[cal.impact == "high"].ts.dt.strftime("%Y-%m-%d"))
    out = []
    for a, g in t.groupby("asset"):
        bars = dukascopy.load(a, date(2019, 10, 1), date.today() + timedelta(days=1))
        d = _daily(bars)
        r = daily_regimes(d)
        r["day"] = pd.DatetimeIndex(d.index).strftime("%Y-%m-%d")
        g = g.merge(r[["day", "state", "backdrop", "vol"]], on="day", how="left")
        g["news_day"] = g.day.isin(news_days)
        g["monday"] = pd.to_datetime(g.day).dt.dayofweek == 0
        g["session"] = [session_note(date.fromisoformat(x)) or "normal" for x in g.day]
        half = []
        for row in g.itertuples():
            try:
                f = te.evaluate(a, row.side, pd.Timestamp(row.filled_at).tz_convert(NY), float(row.entry), float(row.stop),
                                _tps(row), be=True, bars=bars)
                half.append(traits(f)["k_right_half"])
            except Exception:
                half.append(None)
        g["right_half"] = half
        out.append(g)
    t = pd.concat(out, ignore_index=True)
    t["cand2"] = (t.vol == "high") | t.news_day
    t["cand3"] = t.cand2 & (t.right_half == True) & ~t.monday & (t.session == "normal")  # noqa: E712
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    a = ap.parse_args()
    if a.end < START:
        print(f"no forward data yet: the window starts {START}, data would end {a.end}")
        return
    if not a.no_fetch:
        for x in ASSETS:
            subprocess.run(["uv", "run", "python", "-m", "ict_engine.data.dukascopy", "fetch", x, str(START - timedelta(days=5)), str(a.end)], check=False)
    from ict_engine.eval.variants import PD_RETURN_VARIANTS, sweep
    try:
        df = sweep(START, a.end, ASSETS, {VARIANT: PD_RETURN_VARIANTS[VARIANT]}, workers=3)
    except (FileNotFoundError, ValueError):
        df = pd.DataFrame()                                   # no bars for the window yet
    if "status" in df:
        t = df[(df.status == "traded") & df.r.notna()].copy()
        t["day"] = pd.to_datetime(t.day).dt.strftime("%Y-%m-%d")
        t = t[t.day >= str(START)]
    else:
        t = pd.DataFrame()
    old = pd.read_parquet(OUT) if OUT.exists() else pd.DataFrame()
    if len(t):
        key = lambda x: x.asset.astype(str) + "|" + x.decided_at.astype(str)  # noqa: E731
        new = t[~key(t).isin(set(key(old)) if len(old) else set())]
        if len(new):
            old = pd.concat([old, tag(new)], ignore_index=True)
            OUT.parent.mkdir(parents=True, exist_ok=True)
            old.to_parquet(OUT)
    n1 = len(old)
    n2 = int(old.cand2.sum()) if n1 else 0
    n3 = int(old.cand3.sum()) if n1 else 0
    look = n2 >= FIRST_LOOK_N or date.today() >= FIRST_LOOK_DATE
    lines = [f"- {date.today()}: data to {a.end}; trades: all {n1}, candidate 2 (high vol or news day) {n2}, candidate 3 {n3}"
             + ("" if not look else " — FIRST LOOK condition met: score with the decision rule in research/forward-recipe-v1.md")]
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write("\n".join(lines) + "\n")
    print(lines[0])
    if look and n1:
        for name, g in (("1 all", old), ("2 high vol or news", old[old.cand2]), ("3 + right half, not Monday", old[old.cand3])):
            if len(g) > 1:
                print(f"  candidate {name}: n {len(g)} win {100 * g.vote.map(lambda v: v is True or v == 1).mean():.1f}% "
                      f"mean R {g.r.mean():+.3f} z {g.r.mean() / g.r.std() * math.sqrt(len(g)):+.2f} (cluster by day before deciding)")


if __name__ == "__main__":
    main()
