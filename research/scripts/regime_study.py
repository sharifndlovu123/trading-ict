"""Market conditions per year, and every model's trades mapped onto them.

Sharif 2026-11-16: "identify the conditions of the market, what made 2020–21 … 25 to 26 so different … if something
works really well in most conditions that's a keeper, if something works when the market is consolidating we know this
helps more during consolidation periods."

    uv run python research/scripts/regime_study.py     → reports/regimes.parquet, reports/regime-trades.parquet,
                                                          research/regimes/<date>-study.md, out/market-conditions.html

1. Conditions per trading day for US100 / US500 / US30 (ict_engine.concepts.regime: state, backdrop, volatility, all
   known before the day starts) plus scheduled high-impact news that day (calendar from 2021).
2. Each year described: return, share of days trending up / down / consolidating, backdrop, volatility.
3. Every model's trades (the trade day's conditions): win rate and R per condition, and in how many years the sign
   holds. Trades on 2021 exist only for the PD-array-return model (the other models have never been run on it).
Descriptive: no rule is chosen here.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ict_engine.concepts.liquidity_map import _daily  # noqa: E402
from ict_engine.concepts.regime import daily_regimes  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402
from pattern_find import wilson  # noqa: E402

NY = "America/New_York"
ASSETS = ("US100", "US500", "US30")
T = lambda v: v is True or v == 1  # noqa: E731
OLD = {"2022 model": "backtest-{a}", "MMxM": "backtest-mmxm-{a}", "silver bullet": "backtest-silver_bullet-{a}"}
SPANS = ("2020-01-02-2020-12-31", "2022-01-03-2024-06-28", "2024-07-01-2026-11-12")
PDR = {"2020-01-02-2021-12-31": "recipe4", "2022-01-03-2024-06-28": "recipe4", "2024-07-01-2026-11-13": "recipe4b-confirm"}


def regimes() -> pd.DataFrame:
    from ict_engine.news import calendar
    cal = calendar.load()
    news_days = set(pd.to_datetime(cal[cal.impact == "high"].ts).dt.strftime("%Y-%m-%d"))
    first_news = str(pd.to_datetime(cal.ts).min().date())
    out = []
    for a in ASSETS:
        d = _daily(dukascopy.load(a, date(2019, 10, 1), date(2026, 11, 14)))
        r = daily_regimes(d)
        r["asset"], r["day"] = a, pd.DatetimeIndex(d.index).strftime("%Y-%m-%d")
        r["day_ret"] = (d.close / d.close.shift(1) - 1).to_numpy()
        r["day_range_pct"] = ((d.high - d.low) / d.close.shift(1)).to_numpy()
        r["news"] = [("yes" if x in news_days else "no") if x >= first_news else None for x in r.day]
        out.append(r.reset_index(drop=True))
    R = pd.concat(out, ignore_index=True)
    R = R[R.day >= "2020-01-01"]
    R["year"] = R.day.str.slice(0, 4).astype(int)
    return R


def trades() -> pd.DataFrame:
    rows = []
    for fam, pat in OLD.items():
        for a in ASSETS:
            for span in SPANS:
                f = Path(f"reports/{pat.format(a=a)}-{span}-futures.parquet")
                if not f.exists():
                    continue
                d = pd.read_parquet(f)
                d = d[(d.status == "traded") & d.r.notna()]
                rows.append(pd.DataFrame({"model": fam, "asset": a, "day": pd.to_datetime(d.day).dt.strftime("%Y-%m-%d"),
                                          "side": d.side, "r": d.r.astype(float), "win": d.vote.map(T)}))
    for span, tag in PDR.items():
        f = Path(f"reports/variants-pd_return-{span}-{tag}.parquet")
        d = pd.read_parquet(f)
        d = d[(d.status == "traded") & d.r.notna()]
        base = d[~d.variant.str.contains("structure_gate")]
        rec = d[d.variant.str.contains("structure_gate") & ~d.variant.str.contains("stop_buffer")]
        for name, g in (("PD-array return (baseline)", base), ("recipe, mornings", rec)):
            rows.append(pd.DataFrame({"model": name, "asset": g.asset, "day": pd.to_datetime(g.day).dt.strftime("%Y-%m-%d"),
                                      "side": g.side, "r": g.r.astype(float), "win": g.vote.map(T)}))
    t = pd.concat(rows, ignore_index=True)
    return t[t.asset.isin(ASSETS)]


def mdt(df: pd.DataFrame, index: bool = False) -> str:
    """A markdown table without extra dependencies."""
    d = df.reset_index() if index else df
    f = lambda v: "" if v is None or (isinstance(v, float) and v != v) else (f"{v:g}" if isinstance(v, float) else str(v))  # noqa: E731
    out = ["| " + " | ".join(str(c) for c in d.columns) + " |", "|" + "---|" * len(d.columns)]
    return "\n".join(out + ["| " + " | ".join(f(v) for v in r) + " |" for r in d.itertuples(index=False)])


def stat(g: pd.DataFrame) -> dict:
    n = len(g)
    if n == 0:
        return {"n": 0}
    lo, hi = wilson(int(g.win.sum()), n)
    sd = g.r.std()
    return {"n": n, "win": round(100 * g.win.mean(), 1), "lo": round(100 * lo), "hi": round(100 * hi),
            "r": round(float(g.r.mean()), 3), "z": round(float(g.r.mean() / sd * math.sqrt(n)), 2) if n > 1 and sd > 0 else None}


def years_agree(g: pd.DataFrame, min_n: int = 15) -> str:
    """In how many calendar years (with at least ``min_n`` trades) the mean R is positive."""
    ys = [(y, x.r.mean()) for y, x in g.groupby("year") if len(x) >= min_n]
    return f"{sum(m > 0 for _, m in ys)}/{len(ys)}" if ys else "–"


def main():
    R = regimes()
    R.to_parquet("reports/regimes.parquet")
    t = trades().merge(R[["asset", "day", "state", "backdrop", "vol", "news", "er20", "vol_rel", "year"]], on=["asset", "day"], how="left")
    t["with_state"] = np.select([(t.state == "trending up") & (t.side == "long"), (t.state == "trending down") & (t.side == "short"),
                                 t.state == "consolidating"], ["with the trend", "with the trend", "in consolidation"], "against the trend")
    t.to_parquet("reports/regime-trades.parquet")

    # 1. the years
    yr = []
    for y, g in R.groupby("year"):
        u = g[g.asset == "US500"]
        row = {"year": int(y), "US500 return %": round(100 * ((1 + u.day_ret.fillna(0)).prod() - 1), 1),
               "avg daily range %": round(100 * g.day_range_pct.mean(), 2)}
        for s in ("trending up", "trending down", "consolidating"):
            row[s + " %"] = round(100 * (g.state == s).mean())
        for b in ("bull", "bear", "mixed"):
            row["backdrop " + b + " %"] = round(100 * (g.backdrop == b).mean())
        for v in ("high", "normal", "low"):
            row["vol " + v + " %"] = round(100 * (g.vol == v).mean())
        row["median efficiency"] = round(float(g.er20.median()), 2)
        yr.append(row)
    Y = pd.DataFrame(yr)

    # 2. models × conditions
    cuts = {"state": "Market state", "with_state": "Trade vs the state", "backdrop": "Backdrop", "vol": "Volatility", "news": "High-impact news that day"}
    tables = {}
    for col, title in cuts.items():
        rows = []
        for (m, k), g in t.dropna(subset=[col]).groupby(["model", col]):
            rows.append({"model": m, "condition": k, **stat(g), "years positive": years_agree(g)})
        tables[title] = pd.DataFrame(rows)
    per_year = pd.DataFrame([{"model": m, "year": int(y), **stat(g)} for (m, y), g in t.groupby(["model", "year"])])
    combo = pd.DataFrame([{"model": m, "state": s, "vol": v, **stat(g), "years positive": years_agree(g, 10)}
                          for (m, s, v), g in t.dropna(subset=["state", "vol"]).groupby(["model", "state", "vol"]) if len(g) >= 25])

    today = date.today().isoformat()
    md = [f"# Market conditions by year, and each model in each condition ({today})", "",
          "Three US indices, 2020-01 → 2026-11. Conditions are known before each trading day starts (`ict_engine/concepts/regime.py`): "
          "**state** = trending up / trending down (20-day efficiency ratio ≥ 0.30, sign of the 20-day move) or consolidating; "
          "**backdrop** = bull / bear / mixed (close vs its 50-day average, 50-day vs 200-day); **volatility** = the 20-day average daily range "
          "against its own 250-day median (high > 1.25×, low < 0.8×). News = a scheduled high-impact US release that day (calendar from 2021). "
          "Descriptive: no rule is chosen here. The older models have never been run on 2021.", "", "## 1. What each year was", "",
          mdt(Y), "", "## 2. Each model per year", "",
          mdt(per_year.pivot(index="model", columns="year", values="r").round(3), index=True), "",
          "Trades:", "", mdt(per_year.pivot(index="model", columns="year", values="n").fillna(0).astype(int), index=True), ""]
    for title, tb in tables.items():
        md += [f"## {title}", "", mdt(tb), ""]
    md += ["## State × volatility (cells with at least 25 trades)", "", mdt(combo), ""]
    Path("research/regimes").mkdir(parents=True, exist_ok=True)
    Path(f"research/regimes/{today}-study.md").write_text("\n".join(md))
    data = {"years": Y.to_dict("records"), "per_year": per_year.to_dict("records"),
            "tables": {k: v.to_dict("records") for k, v in tables.items()}, "combo": combo.to_dict("records"), "generated": today}
    tpl = Path("viewer/market_conditions.html")
    if tpl.exists():
        Path("out/market-conditions.html").write_text(tpl.read_text().replace("/*DATA*/null", json.dumps(data, default=str)))
    print("\n".join(md[:14]))
    print(per_year.pivot(index="model", columns="year", values="r").round(3).to_string())
    for title, tb in tables.items():
        print("\n==", title); print(tb.to_string(index=False))


if __name__ == "__main__":
    main()
