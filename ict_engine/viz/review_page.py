"""Review page — what each model did well, what it got wrong, with links to example days.

    uv run python -m ict_engine.viz.review_page reports/backtest-*.parquet   # → out/review.html

One self-contained HTML page (viewer/review.html template, no build step, no chart
library) built from backtest tables (``ict_engine.eval.backtest``) with the
post-analysis in ``ict_engine.eval.review``:

1. overview per model family (2022_model, mmxm = mmbm + mmsm)
2. tips (``review.tips``)
3. what went wrong: cause shares (``review.diagnose``) + up to 5 example losing
   trades per cause, each linking to that day's day pack (``daypack.export``;
   that view runs the 2022 model, whatever model the example came from)
4. gate value per family
5. cross-model tables by window / weekday / hour (best named only at n ≥ 30)
6. bucket tables per family with an inline expectancy bar

All page text is HTML-escaped; the data is also embedded as JSON (NaN → null).
"""

from __future__ import annotations

import argparse
import html
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from ict_engine.eval import review as rv

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "viewer" / "review.html"
OUT = ROOT / "out"
MAX_EXAMPLES = 5
MAX_EXPORTS = 40
CROSS_MIN_N = 30
BUCKET_DIMS = ("window", "weekday", "hour", "side")
CROSS_DIMS = ("window", "weekday", "hour")
FAMILY_LABEL = {"2022_model": "2022 model", "mmxm": "MMxM (MMBM + MMSM)"}
CAUSE_TEXT = {
    "bias_wrong": "the day ran the opposite side (PDH/PDL) first",
    "wrong_side": "the mirrored trade at the same entry would have won",
    "stop_too_tight": "a 1.5× wider stop would have reached TP1",
    "target_too_far": "TP1 at 1R would have been hit before the stop",
    "ambiguous": "stop and TP1 inside one 1m bar (counted as a loss)",
    "time_exit": "closed at 16:00 without stop or TP1",
    "unexplained": "none of the above — the setup simply failed",
}
E = html.escape


# --- data ---------------------------------------------------------------------

def clean(x):
    """JSON-safe: NaN/inf → None, numpy/pandas scalars → Python, timestamps → ISO strings."""
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, pd.DataFrame):
        return [clean(r) for r in x.to_dict("records")]
    if isinstance(x, (pd.Timestamp, date)):
        return x.isoformat()
    if isinstance(x, np.generic):
        x = x.item()
    if isinstance(x, float):
        return None if math.isnan(x) or math.isinf(x) else x
    if x is None or isinstance(x, (str, bool, int)):
        return x
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    return str(x)


def pack_name(asset: str, day) -> str:
    """File name of the default-gates day pack ``daypack.export`` writes."""
    return f"{asset}-{pd.Timestamp(day):%Y-%m-%d}.html"


def _families(df: pd.DataFrame) -> list[str]:
    order = list(FAMILY_LABEL)
    return sorted(df.family.unique(), key=lambda f: (order.index(f) if f in order else len(order), f))


def _clock(row) -> str:
    ts = row.get("filled_at")
    if ts is None or pd.isna(ts):
        ts = row.get("decided_at")
    return "" if ts is None or pd.isna(ts) else pd.Timestamp(ts).strftime("%H:%M")


def examples(df: pd.DataFrame, n: int = MAX_EXAMPLES) -> dict:
    """{family: {cause: [example losing trade, ...]}} — up to ``n`` per cause, spread over the
    date range (one per asset-day), so the list is not just the first week."""
    t = rv.trades(df)
    losers = t[~t.vote.map(rv._true) & t.r.notna()]
    out: dict = {}
    for fam in _families(df):
        lf = losers[losers.family == fam]
        tags = lf.apply(rv.causes, axis=1) if len(lf) else pd.Series(dtype=object)
        out[fam] = {}
        for c in rv.CAUSES:
            hit = lf[[c in tg for tg in tags]] if len(lf) else lf
            hit = hit.sort_values(["day", "decided_at"] if "decided_at" in hit else ["day"])
            hit = hit.drop_duplicates(["asset", "day"])
            if hit.empty:
                continue
            idx = sorted(set(np.linspace(0, len(hit) - 1, min(n, len(hit))).round().astype(int)))
            out[fam][c] = [{"model": r.model, "asset": r.asset, "day": f"{pd.Timestamp(r.day):%Y-%m-%d}",
                            "time": _clock(r), "side": r.side, "r": float(r.r), "window": r.get("window"),
                            "href": pack_name(r.asset, r.day)}
                           for _, r in hit.iloc[idx].iterrows()]
    return out


def ensure_daypacks(ex: dict, out_dir: Path = OUT, cap: int = MAX_EXPORTS, export=None) -> dict:
    """Make sure every example's day pack exists; export missing ones (at most ``cap`` new
    days). Examples whose pack is still missing get ``href=None`` (shown without a link)."""
    if export is None:
        from ict_engine.viz.daypack import export
    have = {p.name for p in out_dir.glob("*.html")} if out_dir.exists() else set()
    tried: set[str] = set()
    made = 0
    for fam in ex.values():
        for items in fam.values():
            for e in items:
                name = e["href"]
                if name in have or name in tried:
                    continue
                tried.add(name)
                if made >= cap:
                    continue
                made += 1
                try:
                    export(e["asset"], date.fromisoformat(e["day"]), False)
                    have.add(name)
                except Exception as err:          # missing bars etc.: keep the example, drop the link
                    print(f"day pack {name}: {type(err).__name__}: {err}")
    for fam in ex.values():
        for items in fam.values():
            for e in items:
                if e["href"] not in have:
                    e["href"] = None
    return ex


def build(df: pd.DataFrame, ex: dict | None = None) -> dict:
    """Everything the page shows, as plain JSON-able data."""
    df = rv.prepare(df)
    t = rv.trades(df)
    fams = _families(df)
    data = {
        "range": [f"{df.day.min():%Y-%m-%d}", f"{df.day.max():%Y-%m-%d}"],
        "assets": sorted(df.asset.unique()), "families": fams, "tips": rv.tips(df),
        "overview": {}, "diagnose": {}, "gates": {}, "buckets": {}, "cross": {},
        "examples": ex if ex is not None else examples(df),
    }
    for fam in fams:
        d, tf = df[df.family == fam], t[t.family == fam]
        s = rv._stats("all trades", tf.r, tf.vote)
        s.update(setups=len(d), models=sorted(d.model.unique()), variants=sorted(d.variant.unique()),
                 assets=sorted(d.asset.unique()))
        data["overview"][fam] = s
        diag = [rv.diagnose(d, None)]
        if d.model.nunique() > 1:
            for m in sorted(d.model.unique()):
                x = rv.diagnose(d[d.model == m], None)
                if not x.empty:
                    diag.append(x.assign(bucket=m))
        diag = pd.concat([x for x in diag if not x.empty], ignore_index=True) if any(not x.empty for x in diag) else pd.DataFrame()
        data["diagnose"][fam] = diag
        data["gates"][fam] = rv.gate_value(d)
        data["buckets"][fam] = {dim: rv.buckets(d, dim) for dim in BUCKET_DIMS if dim in d}
    for dim in CROSS_DIMS:
        data["cross"][dim] = rv.cross_model(df, dim, min_n=CROSS_MIN_N)
    return clean(data)


# --- html ---------------------------------------------------------------------

def _r(v, digits=2) -> str:
    return "" if v is None else f"{v:+.{digits}f}"


def _pct(v) -> str:
    return "" if v is None else f"{v:.0%}"


def _cls(v) -> str:
    return "" if v is None else ("pos" if v > 0 else "neg" if v < 0 else "")


def _bar(v, scale) -> str:
    if v is None or not scale:
        return '<span class="bar"></span>'
    w = min(abs(v) / scale, 1) * 50
    return f'<span class="bar" title="{E(_r(v, 3))}R"><i class="{_cls(v) or "pos"}" style="width:{w:.1f}%"></i></span>'


def _table(head: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{h}</th>" for h in head)
    trs = "".join("<tr>" + "".join(c if c.startswith("<td") else f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def _win(s: dict) -> str:
    if s.get("win") is None:
        return ""
    return f'{_pct(s["win"])} <span class="muted">[{_pct(s["win_lo"])}–{_pct(s["win_hi"])}]</span>'


def _exp(s: dict) -> str:
    v = s.get("exp_r")
    se = s.get("exp_se")
    return f'<span class="{_cls(v)}">{E(_r(v, 3))}</span>' + (f' <span class="muted">± {se:.3f}</span>' if se is not None else "")


def _label(fam: str) -> str:
    return E(FAMILY_LABEL.get(fam, fam))


def _overview(d: dict) -> str:
    cards = []
    for fam in d["families"]:
        s = d["overview"][fam]
        cards.append(f"""<div class="card"><h3>{_label(fam)}</h3>
<div class="big {_cls(s['exp_r'])}">{E(_r(s['exp_r'], 3))}R</div><div class="muted">expectancy per trade ± {E('' if s['exp_se'] is None else f"{s['exp_se']:.3f}")} se</div>
<div class="kv">trades <b>{s['n']}</b></div><div class="kv">votes (TP1 before stop) <b>{s['votes']}</b></div>
<div class="kv">win rate (Wilson 95%) <b>{_win(s) or '—'}</b></div><div class="kv">setups seen <b>{s['setups']}</b></div>
<div class="kv">models <b>{E(', '.join(s['models']))}</b></div><div class="kv">assets <b>{E(', '.join(s['assets']))}</b></div>
<details><summary>variants</summary><div class="muted">{'<br>'.join(E(v) for v in s['variants'])}</div></details></div>""")
    return f'<section id="overview"><h2>Overview</h2><p class="note">Traded setups only. A vote = TP1 reached before the stop. Expectancy in R after costs; ± is one standard error.</p><div class="grid">{"".join(cards)}</div></section>'


def _tips(d: dict) -> str:
    if not d["tips"]:
        body = '<p class="note">No bucket passes the evidence bar yet.</p>'
    else:
        cards = []
        for x in d["tips"]:
            good = (x["exp_r"] or 0) > (x["rest_r"] or 0)
            cards.append(f"""<div class="card tip {'pos-tip' if good else 'neg-tip'}"><div class="head"><span>{E(str(x['model']))} · {E(str(x['dim']))} = {E(str(x['bucket']))}</span><span class="{'pos' if good else 'neg'}">{'better' if good else 'worse'} · z {E(_r(x['z'], 1))}</span></div>
<div class="kv">expectancy <b class="{_cls(x['exp_r'])}">{E(_r(x['exp_r']))}R</b></div><div class="kv">rest of the model's trades <b>{E(_r(x['rest_r']))}R</b></div>
<div class="kv">trades / win rate <b>{x['n']} · {_win(x)}</b></div></div>""")
        body = f'<div class="grid">{"".join(cards)}</div>'
    return ('<section id="tips"><h2>Tips</h2><p class="note">A bucket whose expectancy differs from the rest of the same model by |z| ≥ 2, '
            'with ≥ 20 trades on both sides and the same sign in the early and late half. Hypotheses to test as new variants — not rules.</p>'
            f"{body}</section>")


def _wrong(d: dict) -> str:
    parts = ['<section id="wrong"><h2>What went wrong</h2><p class="note">Share of losing trades with each likely cause '
             '(hindsight + one-factor counterfactuals; a loss can have several). Example days open the day pack — '
             '<b>day packs show the 2022-model view</b> with default gates, whatever model the example came from.</p>']
    for fam in d["families"]:
        rows = d["diagnose"].get(fam) or []
        parts.append(f"<h3>{_label(fam)}</h3>")
        if not rows:
            parts.append('<p class="note">No losing trades.</p>')
            continue
        head = ["", "losses"] + [E(c.replace("_", " ")) for c in rv.CAUSES]
        body = [[E(str(r["bucket"])), str(r["losses"])] + [_pct(r.get(c)) for c in rv.CAUSES] for r in rows]
        parts.append(_table(head, body))
        overall = rows[0]
        cards = []
        for c in sorted(rv.CAUSES, key=lambda c: -(overall.get(c) or 0)):
            share = overall.get(c) or 0
            ex = d["examples"].get(fam, {}).get(c, [])
            if not share and not ex:
                continue
            items = []
            for e in ex:
                label = f"{e['asset']} {e['day']} {e['time']}"
                link = f'<a href="{E(e["href"])}">{E(label)}</a>' if e.get("href") else f'<span>{E(label)}</span>'
                items.append(f'<li>{link}<span class="muted">{E(str(e["model"]))} · {E(str(e.get("window") or ""))}</span>'
                             f'<span>{E(str(e["side"]))}</span><span class="{_cls(e["r"])}">{E(_r(e["r"]))}R</span></li>')
            cards.append(f"""<div class="card cause"><div class="kv"><b>{E(c.replace('_', ' '))}</b><b>{_pct(share)}</b></div>
<div class="meter"><i style="width:{share * 100:.1f}%"></i></div><div class="muted">{E(CAUSE_TEXT.get(c, ''))}</div>
{f'<ul>{"".join(items)}</ul>' if items else ''}</div>""")
        parts.append(f'<div class="grid" style="margin-top:10px">{"".join(cards)}</div>')
    parts.append("</section>")
    return "".join(parts)


def _gates(d: dict) -> str:
    parts = ['<section id="gates"><h2>Gate value</h2><p class="note">Setups each gate blocked, simulated as if they had passed '
             '(shadow), vs the trades that passed every gate. A gate whose blocked setups beat the traded ones is filtering out winners.</p>']
    for fam in d["families"]:
        rows = d["gates"].get(fam) or []
        parts.append(f"<h3>{_label(fam)}</h3>")
        if not rows:
            parts.append('<p class="note">No rows.</p>')
            continue
        body = []
        for r in rows:
            vs = r.get("vs_traded_r")
            body.append([E(str(r["bucket"])), str(r["n"]), _win(r), _exp(r),
                         f'<span class="{_cls(vs)}">{E(_r(vs, 3))}</span>'])
        parts.append(_table(["", "n", "win (Wilson)", "exp R ± se", "vs traded R"], body))
    parts.append("</section>")
    return "".join(parts)


def _cross(d: dict) -> str:
    fams = d["families"]
    parts = ['<section id="cross"><h2>Cross-model</h2>'
             f'<p class="note">Expectancy (n trades) per bucket. The best family is highlighted only when it has n ≥ {CROSS_MIN_N}.</p>']
    if len(fams) < 2:
        parts.append('<p class="note">Only one model family in these tables.</p>')
    cards = []
    for dim in CROSS_DIMS:
        rows = d["cross"].get(dim) or []
        if not rows:
            continue
        body = []
        for r in rows:
            best = r.get("best")
            cells = [E(str(r["bucket"]))]
            for f in fams:
                v, n = r.get(f"{f} exp_r"), r.get(f"{f} n")
                txt = f'<span class="{_cls(v)}">{E(_r(v, 3))}</span> <span class="muted">({n or 0})</span>' if n else '<span class="muted">—</span>'
                cells.append(f'<td class="best">{txt}</td>' if best == f else txt)
            cells.append(E(FAMILY_LABEL.get(best, best) if best else "—"))
            body.append(cells)
        cards.append(f'<div><h3>By {E(dim)}</h3>{_table([E(dim)] + [_label(f) for f in fams] + ["best"], body)}</div>')
    parts.append(f'<div class="grid wide">{"".join(cards)}</div></section>')
    return "".join(parts)


def _buckets(d: dict) -> str:
    parts = ['<section id="buckets"><h2>Buckets</h2><p class="note">Traded setups per bucket, ranked by expectancy. '
             'Bar: expectancy (green right / red left of zero, scaled per table). Early/late = the two halves of the date range.</p>']
    for fam in d["families"]:
        parts.append(f"<h3>{_label(fam)}</h3>")
        cards = []
        for dim, rows in (d["buckets"].get(fam) or {}).items():
            if not rows:
                continue
            scale = max((abs(r["exp_r"]) for r in rows if r.get("exp_r") is not None), default=0)
            body = [[E(str(r["bucket"])), str(r["n"]), _win(r), _exp(r) + " " + _bar(r.get("exp_r"), scale),
                     f'<span class="muted">{E(_r(r.get("early_r")))} / {E(_r(r.get("late_r")))}</span>'] for r in rows]
            cards.append(f'<div><h3 class="muted">By {E(dim)}</h3>'
                         f'{_table([E(dim), "n", "win (Wilson)", "exp R ± se", "early / late"], body)}</div>')
        parts.append(f'<div class="grid wide">{"".join(cards)}</div>')
    parts.append("</section>")
    return "".join(parts)


def render(d: dict) -> str:
    """Full HTML page for ``build()`` output."""
    header = (f'<header><h1>ICT Model Review</h1><span class="chip">{E(d["range"][0])} → {E(d["range"][1])}</span>'
              f'<span class="chip">{E(", ".join(d["assets"]))}</span><nav>'
              '<a href="#overview">overview</a><a href="#tips">tips</a><a href="#wrong">what went wrong</a>'
              '<a href="#gates">gates</a><a href="#cross">cross-model</a><a href="#buckets">buckets</a>'
              '<a href="index.html">day packs</a><button id="theme" title="toggle theme" aria-label="toggle theme">◐</button></nav></header>')
    body = header + "<main>" + _overview(d) + _tips(d) + _wrong(d) + _gates(d) + _cross(d) + _buckets(d) + "</main>"
    blob = json.dumps(d, separators=(",", ":"), allow_nan=False)
    blob = blob.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")   # safe inside <script>
    page = TEMPLATE.read_text()
    return page.replace("<!--__BODY__-->", body, 1).replace("/*__REVIEW__*/null", blob, 1)


def write(df: pd.DataFrame, path: Path | None = None, export=None, cap: int = MAX_EXPORTS) -> Path:
    path = path or OUT / "review.html"
    ex = ensure_daypacks(examples(rv.prepare(df)), path.parent, cap, export)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(build(df, ex)))
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.viz.review_page")
    ap.add_argument("tables", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=OUT / "review.html")
    ap.add_argument("--max-exports", type=int, default=MAX_EXPORTS, help="cap on new day packs to export")
    a = ap.parse_args(argv)
    df = pd.concat([pd.read_parquet(p) for p in a.tables], ignore_index=True)
    print(write(df, a.out, cap=a.max_exports))


if __name__ == "__main__":
    main()
