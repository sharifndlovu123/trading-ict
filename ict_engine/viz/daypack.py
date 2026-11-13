"""Day pack — everything the engine saw and decided for one asset-day, as JSON.

This is the visual index: candles + context levels + time windows + detected
events + every setup (with gate trace, would-be plan and result) + the matching
ICT reference trade (mapped onto our feed). The same JSON is meant to feed the
OpenCharts adapter/overlay layer; ``write_html`` also renders a standalone
preview (viewer/daypack.html, lightweight-charts — the library OpenCharts uses).

    uv run python -m ict_engine.viz.daypack US100 2024-01-09            # → out/US100-2024-01-09.html
    uv run python -m ict_engine.viz.daypack US100 2024-01-09 --relaxed  # no HTF-pricing / bias gates

Times are exported as **NY wall-clock epoch seconds** (UTC epoch + NY offset) so a
chart that displays UTC shows New York time.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd

from ict_engine.concepts.bars import resample
from ict_engine.concepts.clock import windows_for
from ict_engine.concepts.context import build_context
from ict_engine.concepts.events import Event, fvgs, gap_lifecycle, structure, sweeps, swing_levels, swings
from ict_engine.data.instruments import get
from ict_engine.models.base import Setup, TradePlan
from ict_engine.models.model_2022 import Params
from ict_engine.sim.run import run_day

NY = "America/New_York"
ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "viewer" / "daypack.html"
OUT = ROOT / "out"


def wall(ts) -> int | None:
    """tz-aware timestamp → NY wall-clock epoch seconds."""
    if ts is None:
        return None
    ts = pd.Timestamp(ts)
    return int(ts.timestamp() + ts.utcoffset().total_seconds())


def _num(x):
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else round(x, 5)


def _ev(e: Event, end=None) -> dict:
    return {"kind": e.kind, "tf": e.tf, "dir": e.direction, "t": wall(e.origin_ts), "known": wall(e.ts),
            "top": _num(e.top), "bottom": _num(e.bottom), "end": wall(end),
            "meta": {k: (v if isinstance(v, (str, bool, int, float)) else str(v)) for k, v in e.meta.items()}}


def _plan(p: TradePlan | None) -> dict | None:
    if p is None:
        return None
    return {"side": p.side, "placed": wall(p.placed_at), "expires": wall(p.expires_at),
            "entry": _num(p.entry), "stop": _num(p.stop), "tp1": _num(p.tp1), "final": _num(p.final_target),
            "tp1_name": p.tp1_name, "final_name": p.final_name, "arm": _num(p.arm), "risk": _num(p.risk)}


def _setup(i: int, s: Setup) -> dict:
    r = s.result
    return {
        "id": i, "side": s.side, "decided": wall(s.decided_at), "variant": s.variant,
        "status": "traded" if s.traded else ("ordered" if s.plan else f"blocked@{s.failed_gate}"),
        "gates": [{"name": g.name, "passed": bool(g.passed), "detail": g.detail} for g in s.gates],
        "evidence": {k: _ev(e) for k, e in s.evidence.items()},
        "plan": _plan(s.plan), "would_plan": _plan(s.would_plan),
        "result": None if r is None else {
            "filled": wall(r.filled_at), "exit": wall(r.exit_at), "reason": r.exit_reason, "r": _num(r.r),
            "vote": r.vote, "ambiguous": r.ambiguous, "final_reached": r.final_reached,
            "runner_r": _num(r.runner_r)},
        "tags": {k: (v if isinstance(v, (str, bool, int, float)) or v is None else str(v)) for k, v in s.tags.items()},
    }


def _candles(df: pd.DataFrame) -> list[list]:
    return [[wall(ts), _num(o), _num(h), _num(l), _num(c)]
            for ts, o, h, l, c in zip(df.index, df.open, df.high, df.low, df.close)]


def _reference(asset: str, day: date, bars: pd.DataFrame, setups: list[Setup]) -> list[dict]:
    from ict_engine.eval.basis import estimate_offset
    from ict_engine.eval.cases import load_cases
    from ict_engine.eval.similarity import compare
    path = ROOT / "tests" / "cases" / "ict_live_exec.yaml"
    if not path.exists():
        return []
    out = []
    for c in load_cases(path):
        if c.trade.day != day or get(c.trade.market).name != asset:
            continue
        off = estimate_offset(bars, day, list(c.anchors))
        o = off.value or 0.0
        t = c.trade
        shift = (lambda x: None if x is None else _num(x + o))
        best = None
        for i, s in enumerate(setups):
            if s.would_plan is None:
                continue
            cmp = compare(s.snapshot(t.market), t, **c.compare_kwargs(off))
            if best is None or cmp.score > best[1].score:
                best = (i, cmp)
        when = t.entry_time or (t.entry_window[0] if t.entry_window else None)
        out.append({
            "id": c.id, "author": c.author, "confidence": c.confidence, "source": c.source, "notes": c.notes,
            "side": t.side, "model": t.model, "contract": c.contract,
            "time": wall(pd.Timestamp(datetime.combine(day, when), tz=NY)) if when else None,
            "window": [wall(pd.Timestamp(datetime.combine(day, w), tz=NY)) for w in t.entry_window] if t.entry_window else None,
            "offset": _num(off.value), "offset_n": off.n,
            "entry": shift(t.entry_price), "stop": shift(t.stop), "tp1": shift(t.tp1), "final": shift(t.final_target),
            "futures": {"entry": t.entry_price, "stop": t.stop, "tp1": t.tp1, "final": t.final_target},
            "best_setup": None if best is None else {"id": best[0], "score": best[1].score, "verdict": best[1].verdict,
                                                     "traits": best[1].traits, "differences": best[1].differences},
        })
    return out


def build_daypack(asset: str, day: date, params: Params = Params(), bars: pd.DataFrame | None = None) -> dict:
    if bars is None:
        from ict_engine.data.dukascopy import load
        prev_month = (day.replace(day=1) - timedelta(days=1)).replace(day=1)
        for start in (day - timedelta(days=45), prev_month, day.replace(day=1)):   # shrink lookback to what's downloaded
            try:
                bars = load(asset, start, day)
                break
            except FileNotFoundError:
                continue
        else:
            raise FileNotFoundError(f"no {asset} bars for {day} — run fetch first")
    a = get(asset)
    ctx = build_context(bars, day)
    d0 = pd.Timestamp(datetime.combine(day - timedelta(days=1), time(18)), tz=NY)
    d1 = pd.Timestamp(datetime.combine(day, time(16, 30)), tz=NY)
    day_1m = bars[(bars.index >= d0) & (bars.index < d1)]
    session = day_1m[day_1m.index >= pd.Timestamp(datetime.combine(day, time(0)), tz=NY)].assign(
        close_ts=lambda x: x.index)

    setups = run_day(bars, day, asset, params)

    sw = swings(session, "1m")
    gaps = [g for g in fvgs(session, "1m") if g.meta.get("displacement")]
    gap_rows = []
    for g in gaps:
        st = gap_lifecycle(g, session)
        gap_rows.append(_ev(g, end=st.inverted or st.filled or session.index[-1]))
    levels = list(ctx.liquidity) + swing_levels(swings(resample(session.drop(columns="close_ts"), "5m"), "5m"))

    windows = []
    for w in windows_for(a.clock, include_optional=False):
        start = pd.Timestamp(datetime.combine(day, w.start), tz=NY)
        if w.end <= w.start:            # wraps midnight → belongs to the evening before
            start = pd.Timestamp(datetime.combine(day - timedelta(days=1), w.start), tz=NY)
            end = pd.Timestamp(datetime.combine(day, w.end), tz=NY)
        else:
            end = pd.Timestamp(datetime.combine(day, w.end), tz=NY)
        windows.append({"name": w.name, "kind": w.kind, "start": wall(start), "end": wall(end)})

    pack = {
        "version": 1, "asset": asset, "futures_root": a.futures_root, "day": day.isoformat(), "tz": NY,
        "model": "2022_model", "variant": params.variant,
        "context": {"bias": ctx.bias, "bias_reason": ctx.bias_reason,
                    "levels": {k: _num(v) for k, v in ctx.levels.items()},
                    "ranges": {str(k): [_num(lo), _num(hi)] for k, (lo, hi) in ctx.ranges.items()},
                    "gaps": [{"name": g.name, "close": _num(g.close), "open": _num(g.open)} for g in ctx.gaps]},
        "candles": {"1m": _candles(day_1m), "5m": _candles(resample(day_1m, "5m"))},
        "windows": windows,
        "events": {
            "swings": [_ev(e) for e in sw],
            "fvgs": gap_rows,
            "sweeps": [_ev(e) for e in sweeps(session, levels)],
            "structure": [_ev(e) for e in structure(session, "1m", sw)],
        },
        "setups": [_setup(i, s) for i, s in enumerate(setups)],
    }
    pack["reference"] = _reference(asset, day, bars, setups)
    return pack


def write_html(pack: dict, path: Path) -> Path:
    html = TEMPLATE.read_text().replace("/*__DAYPACK__*/null", json.dumps(pack, separators=(",", ":")))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)
    return path


RELAXED = Params(use_bias=False, use_poi=False)                 # detection view: only time + trigger + target gates


def export(asset: str, day: date, relaxed: bool) -> tuple[Path, dict]:
    pack = build_daypack(asset, day, RELAXED if relaxed else Params())
    stem = f"{asset}-{day}{'-relaxed' if relaxed else ''}"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{stem}.json").write_text(json.dumps(pack, allow_nan=False))
    return write_html(pack, OUT / f"{stem}.html"), pack


def write_index(rows: list[tuple]) -> Path:
    """out/index.html — one row per reference trade, links to both variants' day packs."""
    import html as h
    trs = []
    for case_id, asset, day, links in rows:
        cells = []
        for label, path, ref in links:
            b = ref.get("best_setup") if ref else None
            verdict = f"{b['verdict']} {b['score']:.2f}" if b else "no setup"
            cells.append(f'<td><a href="{h.escape(path.name)}">{h.escape(label)}</a><br><small>{h.escape(verdict)}</small></td>')
        trs.append(f"<tr><td>{h.escape(case_id)}</td><td>{h.escape(asset)}</td>{''.join(cells)}</tr>")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ICT Day Packs</title><style>
:root{{--bg:#fff;--text:#1b1f24;--muted:#5b6470;--line:#dde1e6;--accent:#3867d6}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f1216;--text:#e6e9ed;--muted:#95a0ad;--line:#2a313a;--accent:#6c8cff}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--text);font:14px/1.5 system-ui,sans-serif}}
table{{border-collapse:collapse;width:100%;max-width:900px}}td,th{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}}
small{{color:var(--muted)}}a{{color:var(--accent)}}.wrap{{overflow-x:auto}}</style></head><body>
<h1>ICT Day Packs — 2022 model vs ICT's live executions</h1>
<p><small>Each link opens one asset-day: candles, levels, windows, detected events, every setup with its gate trace, and ICT's trade mapped onto the feed. Verdict = closest engine setup (any gate state) to ICT's trade.</small></p>
<div class="wrap"><table><tr><th>reference trade</th><th>asset</th><th>default gates</th><th>relaxed</th></tr>{''.join(trs)}</table></div></body></html>"""
    path = OUT / "index.html"
    path.write_text(page)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.viz.daypack")
    ap.add_argument("asset", nargs="?")
    ap.add_argument("day", nargs="?", type=date.fromisoformat)
    ap.add_argument("--relaxed", action="store_true", help="drop bias and POI gates")
    ap.add_argument("--references", action="store_true", help="export every reference-trade day + out/index.html")
    a = ap.parse_args(argv)
    if a.references:
        from ict_engine.eval.cases import load_cases
        rows = []
        for c in load_cases(ROOT / "tests" / "cases" / "ict_live_exec.yaml"):
            asset = get(c.trade.market).name
            links = []
            for relaxed in (False, True):
                path, pack = export(asset, c.trade.day, relaxed)
                ref = next((r for r in pack["reference"] if r["id"] == c.id), None)
                links.append(("relaxed" if relaxed else "default", path, ref))
            rows.append((c.id, asset, c.trade.day, links))
        print(write_index(rows))
        return
    if not (a.asset and a.day):
        ap.error("asset and day required (or --references)")
    print(export(a.asset, a.day, a.relaxed)[0])


if __name__ == "__main__":
    main()
