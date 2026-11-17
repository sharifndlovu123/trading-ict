"""Liquidity, targets and stops — where price actually went (descriptive, in-sample only: 2022-01-03 → 2023-09-28;
selects nothing). Sharif 2026-11-15: "liquidity and TPs are very important … stops aren't placed so well sometimes …
respective to the models' own approach".

For every filled 2022 model / MMxM trade (futures backtests, 5 assets):
  A. liquidity taken   what the setup swept (2022 model: the swept level; MMxM: the purge/POI) → win rate, exp R
  B. targets           MFE (best price in our favour, in R) before the stop and by the close ignoring the stop;
                       every untaken level ahead at the decision (liquidity_reach types + 1h/4h volume imbalances)
                       → reached before the stop / by the close / next day, beside the random-walk rate 1/(1+d)
  C. stops             stopped trades that still reached TP1 by the close (stop hunted?), how far beyond the stop
                       price went first (depth in R), and whether the nearest 5m / 15m / 1h swing beyond the
                       model's own stop (its own approach, just one structure further) would have held

    uv run python research/scripts/liq_tp_stop_study.py [--workers 10]
      → reports/study-trades.parquet, reports/study-levels.parquet, out/liq-tp-stops.html
Same-bar stop and target → stop first (conservative).
"""
import argparse
import html
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from liquidity_reach import levels_ahead  # noqa: E402

from ict_engine.concepts.bars import resample  # noqa: E402
from ict_engine.concepts.context import build_context  # noqa: E402
from ict_engine.concepts.events import gap_lifecycle, swings, volume_imbalances  # noqa: E402
from ict_engine.data import dukascopy  # noqa: E402

NY = "America/New_York"
START, CUT = date(2022, 1, 3), date(2023, 9, 29)
MODELS = {"2022_model": "reports/backtest-{a}-2022-01-03-2024-06-28-futures.parquet",
          "mmxm": "reports/backtest-mmxm-{a}-2022-01-03-2024-06-28-futures.parquet"}
ASSETS = ("US100", "US500", "US30", "XAUUSD", "XAGUSD")
STOP_TFS = ("5m", "15m", "1h")
MFE_STEPS = (0.5, 1.0, 1.5, 2.0, 3.0, 5.0)
DEPTHS = (0.1, 0.25, 0.5, 1.0)


def vi_ahead(hist, decided, long, entry):
    out = []
    for tf in ("1h", "4h"):
        b = resample(hist, tf)
        b = b[b.close_ts <= decided]
        for g in volume_imbalances(b, tf):
            if g.ts > decided or g.direction == ("bull" if long else "bear"):
                continue
            near = g.bottom if long else g.top
            if ((near > entry) if long else (near < entry)) and gap_lifecycle(g, hist, until=decided).valid_at(decided):
                out.append((f"vi_{tf}", float(near), g.ts))
    return out


def swing_beyond(hist, decided, tf, beyond, long):
    b = resample(hist, tf)
    b = b[b.close_ts <= decided]
    kind = "swing_low" if long else "swing_high"
    sw = [e for e in swings(b, tf) if e.kind == kind and e.ts <= decided
          and ((e.bottom < beyond) if long else (e.top > beyond))]
    if not sw:
        return None
    e = max(sw, key=lambda e: e.ts)
    return float(e.bottom if long else e.top)


def liq_type(model, r):
    if model == "2022_model":
        n = str(r.liquidity or "")
        return n.split("@")[0] if "@" in n else (n or "none")
    p = str(r.poi or "")
    return p.split(" ")[0] + " " + p.split(" ")[1] if p.startswith("ran ") else ("htf FVG" if "FVG" in p else (p or "none"))


def first(mask, idx):
    return idx[mask.argmax()] if mask.any() else None


def job(args):
    model, asset = args
    d = pd.read_parquet(MODELS[model].format(a=asset))
    d = d[(d.status == "traded") & d.filled_at.notna()]
    d = d[(pd.to_datetime(d.day).dt.date >= START) & (pd.to_datetime(d.day).dt.date < CUT)]
    bars = dukascopy.load(asset, START - timedelta(days=30), CUT + timedelta(days=4))
    trades, levels = [], []
    for r in d.itertuples():
        day = pd.Timestamp(r.day).date()
        dec, fill = pd.Timestamp(r.decided_at), pd.Timestamp(r.filled_at)
        long, entry, stop = r.side == "long", float(r.entry), float(r.stop)
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        sgn = 1 if long else -1
        close = pd.Timestamp(datetime.combine(day, time(16, 55)), tz=NY)
        nxt = close + timedelta(days=1 if day.weekday() < 4 else 3)
        path = bars[(bars.index >= fill) & (bars.index <= nxt)]
        sess = path[path.index <= close]
        fav = (sess.high - entry) if long else (entry - sess.low)
        adv = (entry - sess.low) if long else (sess.high - entry)
        hit_stop = (sess.low <= stop) if long else (sess.high >= stop)
        t_stop = first(hit_stop.to_numpy(), sess.index)
        before = sess[sess.index < t_stop] if t_stop is not None else sess
        fav_b = (before.high - entry) if long else (entry - before.low)
        mfe_before = float(fav_b.max()) / risk if len(before) else 0.0
        hit_tp1 = (sess.high >= r.tp1) if long else (sess.low <= r.tp1)
        t_tp1 = first(hit_tp1.to_numpy(), sess.index)
        # adverse excursion before TP1 (the stop a trade needed to survive to TP1), ignoring our stop
        pre = sess[sess.index < t_tp1] if t_tp1 is not None else sess
        need = float(((entry - pre.low) if long else (pre.high - entry)).max()) / risk if len(pre) else 0.0
        hist = bars[(bars.index >= dec - timedelta(days=10)) & (bars.index < dec)]
        row = dict(model=model, asset=asset, day=str(day), decided=dec, side=r.side, risk=risk, window=r.window,
                   liq=liq_type(model, r), poi=r.poi, exit=r.exit, vote=bool(r.vote), runner_r=r.runner_r, r=r.r,
                   tp1_r=abs(r.tp1 - entry) / risk, final_r=abs(r.final - entry) / risk,
                   mfe_before_stop=mfe_before, mfe_session=float(fav.max()) / risk if len(sess) else 0.0,
                   mae_session=float(adv.max()) / risk if len(sess) else 0.0,
                   stopped=t_stop is not None and (t_tp1 is None or t_stop <= t_tp1),
                   tp1_by_close=t_tp1 is not None, need_r=need,
                   final_by_close=bool(((sess.high >= r.final) if long else (sess.low <= r.final)).any()))
        for tf in STOP_TFS:
            s = swing_beyond(hist, dec, tf, stop, long)
            row[f"swing_{tf}_r"] = abs(entry - s) / risk if s is not None else np.nan
        trades.append(row)
        ctx = build_context(bars[bars.index < pd.Timestamp(datetime.combine(day, time(0)), tz=NY) + timedelta(hours=17)], day)
        seen = set()
        for kind, price, formed in levels_ahead(hist, ctx, dec, long, entry) + vi_ahead(hist, dec, long, entry):
            key = (kind, round(price, 2))
            if key in seen:
                continue
            seen.add(key)
            m = ((path.high >= price) if long else (path.low <= price)).to_numpy()
            t = first(m, path.index)
            levels.append(dict(model=model, asset=asset, decided=dec, kind=kind, dist_r=abs(price - entry) / risk,
                               age_h=(dec - pd.Timestamp(formed)).total_seconds() / 3600,
                               before_stop=t is not None and (t_stop is None or t < t_stop),
                               by_close=t is not None and t <= close, by_next=t is not None))
    print(model, asset, len(trades), "trades", len(levels), "levels", flush=True)
    return trades, levels


# --- report ---------------------------------------------------------------------------------------------------------
def wilson(k, n, z=1.96):
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def table(df, fmt=None, cls=""):
    fmt = fmt or {}
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    rows = []
    for _, r in df.iterrows():
        cells = []
        for c in df.columns:
            v = r[c]
            s = fmt[c](v) if c in fmt and pd.notna(v) else ("" if pd.isna(v) else str(v))
            cells.append(f"<td>{html.escape(s)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


pct = lambda v: f"{v:.0%}"
r2 = lambda v: f"{v:+.2f}"
f1 = lambda v: f"{v:.1f}"


def keypoints(t: pd.DataFrame, lv: pd.DataFrame) -> str:
    """The highlighted findings, computed (not typed) so a rebuild keeps them honest."""
    names = {"2022_model": "2022 model", "mmxm": "MMxM"}
    out = []
    for m in ("2022_model", "mmxm"):
        g, L = t[t.model == m], lv[lv.model == m]
        st = g[g.stopped]
        h = st[st.tp1_by_close]
        L = L.assign(rw=1 / (1 + L.dist_r))
        s = L.groupby("kind").agg(n=("dist_r", "size"), bs=("before_stop", "mean"), rw=("rw", "mean"))
        s["edge"] = s.bs - s.rw
        best, worst = s[s.n >= 50].edge.idxmax(), s[s.n >= 50].edge.idxmin()
        a = g.groupby("liq").agg(n=("vote", "size"), exp=("runner_r", "mean"))
        a = a[a.n >= 30].sort_values("exp")
        risk = g.groupby("asset").risk.median()
        out.append(f"<li><b>{names[m]}</b><ul>"
                   f"<li class='hot'>Direction: by the close price reached 2 R our way on {(g.mfe_session >= 2).mean():.0%} of "
                   f"trades and 2 R <i>against</i> on {(g.mae_session >= 2).mean():.0%} — no better than a coin. The "
                   f"stop is small next to the day's range (median stop: "
                   + ", ".join(f"{k} {v:.1f}" for k, v in risk.items()) +
                   ") so price travels several R both ways.</li>"
                   f"<li class='hot'>Stops: {len(h) / max(len(st), 1):.0%} of stopped trades reached TP1 later the same day, but "
                   f"only {(h.need_r <= 1.25).sum() / max(len(st), 1):.0%} would have survived with ¼ R more room — the "
                   f"stop is inside the noise, not a little short. The 1h swing beyond it would have held "
                   f"{(h[h.swing_1h_r.notna()].need_r < h[h.swing_1h_r.notna()].swing_1h_r).sum() / max(len(st), 1):.0%} "
                   f"(median {g.swing_1h_r.median():.1f} R away; tested 2026-11-15: win rate up, expectancy flat).</li>"
                   f"<li>Liquidity taken: best {a.index[-1]} ({a.exp.iloc[-1]:+.2f} R, n {int(a.n.iloc[-1])}), worst "
                   f"{a.index[0]} ({a.exp.iloc[0]:+.2f} R, n {int(a.n.iloc[0])}) — groups with n ≥ 30.</li>"
                   f"<li>Targets ahead: no level type is hit much more than chance; best {best} "
                   f"({s.edge[best]:+.0%} vs random), worst {worst} ({s.edge[worst]:+.0%}).</li></ul></li>")
    return ("<div class='keys'><h2>Key points</h2><ul>" + "".join(out) + "</ul><p class='note'>Reading: entries are "
            "not yet picking the side — so targets and stop tweaks can only reshuffle a coin flip. The liquidity map "
            "(out/liqmap) is the next step: find the draw on the daily first, then hunt toward it.</p></div>")


def report(t: pd.DataFrame, lv: pd.DataFrame) -> str:
    parts = [keypoints(t, lv)]
    names = {"2022_model": "2022 model", "mmxm": "MMxM"}
    for m in ("2022_model", "mmxm"):
        g = t[t.model == m]
        L = lv[lv.model == m]
        parts.append(f'<section><h2>{names[m]} <span class="muted">— {len(g)} filled trades, in-sample</span></h2>')
        # A
        a = g.groupby("liq").agg(n=("vote", "size"), win=("vote", "mean"), exp_R=("runner_r", "mean"),
                                 tp1_by_close=("tp1_by_close", "mean")).sort_values("n", ascending=False).reset_index()
        a["win 95%"] = [f"{lo:.0%}–{hi:.0%}" for lo, hi in (wilson(round(w * n), n) for w, n in zip(a.win, a.n))]
        parts.append("<h3>A · Liquidity taken before the entry</h3>"
                     "<p class='note'>What the setup swept (2022 model: the level whose sweep triggered it; MMxM: the purge "
                     "behind the reversal). Win = TP1 before the stop.</p>")
        parts.append(table(a[["liq", "n", "win", "win 95%", "exp_R", "tp1_by_close"]].rename(
            columns={"liq": "liquidity taken", "exp_R": "exp R (runner)", "tp1_by_close": "TP1 by close (ignoring stop)"}),
            {"win": pct, "exp R (runner)": r2, "TP1 by close (ignoring stop)": pct}))
        # B — MFE
        rows = []
        for k in MFE_STEPS:
            rows.append(dict(reach=f"{k:g} R", before_stop=(g.mfe_before_stop >= k).mean(),
                             by_close=(g.mfe_session >= k).mean(), against=(g.mae_session >= k).mean(),
                             random_walk=1 / (1 + k)))
        parts.append("<h3>B · How far price went our way</h3>"
                     "<p class='note'>Share of trades whose best price reached each distance. <b>Before the stop</b> is what "
                     "the trade could bank; <b>by the close</b> ignores the stop; <b>against</b> is the same for the opposite "
                     "direction — if it matches 'by the close', the side we picked was no better than a coin. Random "
                     "walk: a level d R away is hit before a 1 R stop with chance 1/(1+d).</p>")
        parts.append(table(pd.DataFrame(rows).rename(columns={"before_stop": "before the stop", "by_close": "by the close",
                                                             "against": "against us, by the close", "random_walk": "random walk"}),
                           {"before the stop": pct, "by the close": pct, "against us, by the close": pct, "random walk": pct}))
        parts.append(f"<p class='note'>Model targets: TP1 median {g.tp1_r.median():.1f} R, reached before the stop "
                     f"{g.vote.mean():.0%}, by the close {g.tp1_by_close.mean():.0%} · final median {g.final_r.median():.1f} R, "
                     f"by the close {g.final_by_close.mean():.0%}.</p>")
        # B — levels
        L = L.assign(family=L.kind.str.replace(r"_(near|ce|far)$", "", regex=True))
        s = L.groupby("kind").agg(n=("dist_r", "size"), trades=("decided", "nunique"), med_R=("dist_r", "median"),
                                  before_stop=("before_stop", "mean"), by_close=("by_close", "mean"),
                                  by_next=("by_next", "mean"),
                                  rw=("dist_r", lambda x: float(np.mean(1 / (1 + x))))).reset_index()
        s["edge"] = s.before_stop - s.rw
        s = s.sort_values("edge", ascending=False)
        parts.append("<h3>B · Which levels ahead got hit</h3>"
                     "<p class='note'>Every untaken level ahead of the entry at the decision. <b>vs random</b> = hit rate before "
                     "the stop minus 1/(1+d) for the same distances: positive means price was drawn there more than "
                     "chance.</p>")
        parts.append(table(s.rename(columns={"kind": "level", "med_R": "median R away", "before_stop": "before stop",
                                             "by_close": "by close", "by_next": "next day", "rw": "random walk",
                                             "edge": "vs random"}),
                           {"median R away": f1, "before stop": pct, "by close": pct, "next day": pct,
                            "random walk": pct, "vs random": lambda v: f"{v:+.0%}"}))
        # C — stops
        st = g[g.stopped]
        hunted = st[st.tp1_by_close]
        rows = [dict(item="stopped out (stop before TP1)", n=len(st), share=len(st) / max(len(g), 1)),
                dict(item="… then TP1 reached by the close", n=len(hunted), share=len(hunted) / max(len(st), 1))]
        for k in DEPTHS:
            ok = hunted[hunted.need_r <= 1 + k]
            rows.append(dict(item=f"… needing ≤ {k:g} R more stop", n=len(ok), share=len(ok) / max(len(st), 1)))
        for tf in STOP_TFS:
            col = f"swing_{tf}_r"
            have = hunted[hunted[col].notna()]
            ok = have[have.need_r < have[col]]
            rows.append(dict(item=f"… the {tf} swing beyond the stop would have held", n=len(ok),
                             share=len(ok) / max(len(st), 1)))
        parts.append("<h3>C · Stops</h3>"
                     "<p class='note'>Shares below the first row are of the <b>stopped</b> trades. 'Needing ≤ k R more' = the "
                     "worst price before TP1 was within k R beyond our stop: a slightly deeper stop on the model's own "
                     "anchor would have survived. Swing rows: the model's stop moved one structure further (nearest "
                     "confirmed swing beyond it, known at the decision).</p>")
        parts.append(table(pd.DataFrame(rows), {"share": pct}))
        sw = pd.DataFrame([dict(timeframe=tf, found=g[f"swing_{tf}_r"].notna().mean(),
                                median_R=g[f"swing_{tf}_r"].median()) for tf in STOP_TFS])
        parts.append("<p class='note'>How far those swings are (in the model's R; 1.0 = the model's own stop):</p>")
        parts.append(table(sw.rename(columns={"median_R": "median distance (R)", "found": "trades with one"}),
                           {"trades with one": pct, "median distance (R)": lambda v: f"{v:.1f}"}))
        by = g.groupby("asset").agg(n=("vote", "size"), stopped=("stopped", "mean"),
                                    hunted=("tp1_by_close", lambda x: float((x & g.loc[x.index, "stopped"]).sum())),
                                    med_risk=("risk", "median")).reset_index()
        by["hunted"] = by.hunted / (by.stopped * by.n).clip(lower=1)
        parts.append(table(by.rename(columns={"stopped": "stopped share", "hunted": "of those, TP1 later",
                                             "med_risk": "median stop (price)"}),
                           {"stopped share": pct, "of those, TP1 later": pct, "median stop (price)": lambda v: f"{v:.2f}"}))
        parts.append("</section>")
    css = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a64;--line:#e4e1d8;--accent:#2b5c8a;--head:#f1eee6}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#a3a198;--line:#33322e;--accent:#8fb8e0;--head:#22211e}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:24px 16px}
h1{font-size:1.5rem;margin:0 0 4px}h2{font-size:1.25rem;margin:36px 0 8px;border-bottom:2px solid var(--accent);padding-bottom:4px}
h3{font-size:1rem;margin:22px 0 4px}.muted,.note{color:var(--muted)}.note{font-size:.9rem;margin:4px 0 8px}
table{border-collapse:collapse;width:100%;margin:6px 0 10px;font-variant-numeric:tabular-nums;font-size:.88rem;display:block;overflow-x:auto}
th,td{border-bottom:1px solid var(--line);padding:4px 8px;text-align:right;white-space:nowrap}
th{background:var(--head);position:sticky;top:0}td:first-child,th:first-child{text-align:left}
.keys{border:2px solid var(--accent);border-radius:8px;padding:4px 18px 10px;margin:18px 0;background:var(--head)}
.keys h2{border:0;margin-top:10px}.keys li{margin:4px 0}.hot{font-weight:600}
"""
    return (f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Liquidity, targets, stops</title><style>{css}</style></head><body>"
            f"<h1>Liquidity, targets and stops — where price went</h1>"
            f"<p class='muted'>2022 model + MMxM, futures backtests, US100 US500 US30 XAUUSD XAGUSD, in-sample "
            f"{START} → {CUT - timedelta(days=1)} only (descriptive; selects nothing; OOS untouched). Built "
            f"{datetime.now():%Y-%m-%d %H:%M}. Script: research/scripts/liq_tp_stop_study.py</p>"
            + "".join(parts) + "</body></html>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    os.environ.setdefault("ICT_COST_BASIS", "futures")
    if not a.report_only:
        jobs = [(m, x) for m in MODELS for x in ASSETS]
        with ProcessPoolExecutor(a.workers) as ex:
            res = list(ex.map(job, jobs))
        pd.DataFrame([t for tr, _ in res for t in tr]).to_parquet("reports/study-trades.parquet")
        pd.DataFrame([l for _, lv in res for l in lv]).to_parquet("reports/study-levels.parquet")
    t, lv = pd.read_parquet("reports/study-trades.parquet"), pd.read_parquet("reports/study-levels.parquet")
    Path("out").mkdir(exist_ok=True)
    Path("out/liq-tp-stops.html").write_text(report(t, lv))
    print("wrote out/liq-tp-stops.html", len(t), "trades", len(lv), "levels")


if __name__ == "__main__":
    main()
