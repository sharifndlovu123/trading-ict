"""Score a model against the reference trades — pipeline stage 9.

    uv run python -m ict_engine.eval.report            # 2022 model, default + relaxed variants

For every reference day: run the model, map ICT's futures prices onto our feed
with the case's anchors, and find the engine trade most similar to ICT's.
Prints one row per reference case plus the gate that blocked the nearest setup
when nothing traded.

Two scores per variant: **own cases** (ICT trades labelled with this model — the
fair test) and **all cases** (every reference trade — a detection check, since
other models' trades share liquidity/MSS/FVG steps).
"""

from __future__ import annotations

from collections import Counter
from datetime import timedelta

from ict_engine.data.dukascopy import load
from ict_engine.data.instruments import get
from ict_engine.eval.basis import estimate_offset
from ict_engine.eval.cases import load_cases
from ict_engine.eval.similarity import compare
from ict_engine.models.model_2022 import MODEL, Params
from ict_engine.sim.run import run_day

CASES = "tests/cases/ict_live_exec.yaml"
OLD_WINDOWS = ("london_kz", "ny_am_kz", "ny_pm_kz")
VARIANTS = {                                   # name -> (params, cap_scope)
    "v1 defaults (first run)": (Params(windows=OLD_WINDOWS, use_htf_pricing=True, neutral_bias="block"), "day"),
    "current defaults": (Params(), "day"),
    "current, cap per window": (Params(), "window"),
    "current, + 20-day pricing": (Params(use_htf_pricing=True), "day"),
    "current, no bias": (Params(use_bias=False), "day"),
    "current, bias draw_htf": (Params(bias_rule="draw_htf"), "day"),
    "current, neutral bias blocks": (Params(neutral_bias="block"), "day"),
}


def score(params: Params, cases=None, data_start=None, cap_scope: str = "day"):
    cases = cases or load_cases(CASES)
    rows = []
    for c in cases:
        asset = get(c.trade.market).name
        start = data_start or (c.trade.day - timedelta(days=60))
        try:
            bars = load(asset, max(start, c.trade.day.replace(day=1) - timedelta(days=62)), c.trade.day)
        except FileNotFoundError:
            bars = load(asset, c.trade.day.replace(day=1), c.trade.day)
        setups = run_day(bars, c.trade.day, asset, params, cap_scope=cap_scope)
        off = estimate_offset(bars, c.trade.day, list(c.anchors))
        kw = c.compare_kwargs(off)
        traded = [s for s in setups if s.traded]
        best, best_s = None, None
        for s in traded:
            cmp = compare(s.snapshot(c.trade.market), c.trade, **kw)
            if best is None or cmp.score > best.score:
                best, best_s = cmp, s
        same_side = [s for s in setups if s.side == ("long" if c.trade.side == "long" else "short") and "fvg" in s.evidence]
        blocked = Counter(s.failed_gate for s in same_side if s.plan is None and s.failed_gate)
        seen_best, seen_s = None, None              # detection: most similar setup the engine SAW
        for s in setups:
            if s.would_plan is None:
                continue
            cmp = compare(s.snapshot(c.trade.market), c.trade, **kw)
            if seen_best is None or cmp.score > seen_best.score:
                seen_best, seen_s = cmp, s
        rows.append((c, best, best_s, len(traded), blocked, seen_best, seen_s))
    return rows


def tally(rows):
    """(traded like ICT, seen) counts — 'like' = match or similar."""
    ok = ("match", "similar")
    return (sum(1 for r in rows if r[1] and r[1].verdict in ok),
            sum(1 for r in rows if r[5] and r[5].verdict in ok))


def main():
    for name, (p, cap) in VARIANTS.items():
        rows = score(p, cap_scope=cap)
        own = [r for r in rows if r[0].trade.model == MODEL]
        (ft, st), (fo, so) = tally(rows), tally(own)
        print(f"\n=== {name}  [{p.variant}, cap/{cap}]\n"
              f"    own cases ({MODEL}): traded like ICT {fo}/{len(own)}, seen {so}/{len(own)}   "
              f"all cases: traded {ft}/{len(rows)}, seen {st}/{len(rows)}")
        for c, best, s, n, blocked, sb, ss in rows:
            print(f"  {'*' if c.trade.model == MODEL else ' '}", end="")
            if best:
                r = s.result
                print(f"{c.id:36} {best.verdict:9} {best.score:.2f}  engine {s.side} {s.result.filled_at:%H:%M} "
                      f"{r.exit_reason} {r.r:+.2f}R  ({n} trade{'s' if n != 1 else ''})")
            else:
                why = ", ".join(f"{g}×{k}" for g, k in blocked.most_common(3)) or "no same-side setup with FVG"
                print(f"{c.id:36} {'—':9}       no engine trade; same-side setups blocked at: {why}")
            if sb:
                print(f"   {'':36} seen: {sb.verdict} {sb.score:.2f} at {ss.decided_at:%H:%M} "
                      f"blocked@{ss.failed_gate or 'cap/none'}  [{', '.join(f'{k} {v:.2f}' for k, v in sb.traits.items())}]")



if __name__ == "__main__":
    main()
