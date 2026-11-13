"""Backtest — run a model over a date range and keep every setup as one row.

    uv run python -m ict_engine.eval.backtest US100 2023-01-01 2024-06-30 [--cap window|day]
    → reports/backtest-US100-2023-01-01-2024-06-30.parquet   (reports/ is git-ignored)

This table is what post-analysis (``ict_engine.eval.review``) reads. One row per
setup, traded or not, with:

    identity     model, variant, asset, style, day, side
    time         decided_at, weekday, hour, window, month, quarter
    context      daily bias + rule, hindsight day outcome (PDH or PDL first)
    gates        status, failed gate + detail, all gates as "name:0/1"
    plan         entry/stop/tp1/final, risk, arm, POI, liquidity level, FVG size
    result       real result (if the runner placed it): exit, R, vote, MAE
    shadow       the would-be plan simulated as if every gate passed and no cap
    cf_*         one-factor counterfactuals of the shadow plan: stop 1.5× wider
                 (cf_wide_stop_*), TP1 at 1R (cf_tp1_1r_*), opposite side at the same
                 entry with mirrored stop/TP1 (cf_flip_*)

``outcome`` and ``shadow_*`` are hindsight. They exist only to judge decisions
afterwards ("the bias gate blocked a winner"); no gate or plan may read them.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd

from ict_engine.concepts.context import build_context
from ict_engine.eval.bias import day_outcome
from ict_engine.models import model_2022
from ict_engine.models.base import Setup
from ict_engine.data.instruments import COST
from ict_engine.sim.run import run_day
from ict_engine.sim.simulate import simulate

NY = "America/New_York"
ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def _status(s: Setup) -> str:
    if s.traded:
        return "traded"
    if s.result is not None:
        return s.result.exit_reason            # placed but not filled: missed / not_filled / cancelled
    return f"blocked@{s.failed_gate}" if s.failed_gate else "no_plan"


def _result_cols(prefix: str, r) -> dict:
    if r is None:
        return {f"{prefix}exit": None, f"{prefix}r": None, f"{prefix}vote": None,
                f"{prefix}filled_at": None, f"{prefix}exit_at": None, f"{prefix}mae_r": None,
                f"{prefix}runner_r": None, f"{prefix}ambiguous": None}
    return {f"{prefix}exit": r.exit_reason, f"{prefix}r": r.r if r.filled_at is not None else None,
            f"{prefix}vote": r.vote, f"{prefix}filled_at": r.filled_at, f"{prefix}exit_at": r.exit_at,
            f"{prefix}mae_r": r.mae_r, f"{prefix}runner_r": r.runner_r, f"{prefix}ambiguous": r.ambiguous}


def setup_row(s: Setup, ctx, outcome: str, bias_rule: str, shadow) -> dict:
    p = s.plan or s.would_plan
    fail = next((g for g in s.gates if not g.passed), None)
    liq, fvg = s.evidence.get("liquidity"), s.evidence.get("fvg")
    bias = ctx.bias if bias_rule == "prev_day" else ctx.biases.get(bias_rule, (ctx.bias, ""))[0]
    t = s.decided_at
    row = {
        "model": s.model, "variant": s.variant, "asset": s.asset, "style": s.style,
        "day": pd.Timestamp(s.day), "side": s.side,
        "decided_at": t, "weekday": t.strftime("%a"), "hour": t.hour,
        "window": s.tags.get("window") or "none", "month": t.strftime("%Y-%m"), "quarter": f"Q{(t.month - 1) // 3 + 1}",
        "bias": bias, "bias_rule": bias_rule, "outcome": outcome,
        "status": _status(s), "failed_gate": fail.name if fail else None, "failed_detail": fail.detail if fail else None,
        "gates": " ".join(f"{g.name}:{int(g.passed)}" for g in s.gates),
        "entry": p.entry if p else None, "stop": p.stop if p else None, "tp1": p.tp1 if p else None,
        "final": p.final_target if p else None, "tp1_name": p.tp1_name if p else None,
        "risk": p.risk if p else None, "arm": p.arm if p else None,
        "tp1_r": abs(p.tp1 - p.entry) / p.risk if p and p.risk else None,
        "poi": s.tags.get("poi"), "liquidity": liq.meta.get("level") if liq else None,
        "liquidity_kind": liq.kind if liq else None,
        "fvg_size": (fvg.top - fvg.bottom) if fvg else None,
    }
    row.update(_result_cols("", s.result if s.result is not None and s.plan is not None else None))
    row.update(_result_cols("shadow_", shadow))
    return row


def counterfactuals(plan, bars_1m, close, cost) -> dict:
    """One factor changed at a time → which single change would have turned the trade around."""
    if plan is None:
        return {}
    sign = 1 if plan.side == "long" else -1
    flip_side = "short" if plan.side == "long" else "long"
    alts = {
        "wide_stop": replace(plan, stop=plan.entry - sign * 1.5 * plan.risk),
        "tp1_1r": replace(plan, tp1=plan.entry + sign * plan.risk),
        "flip": replace(plan, side=flip_side, stop=plan.entry + sign * plan.risk,
                        tp1=plan.entry - sign * abs(plan.tp1 - plan.entry),
                        final_target=plan.entry - sign * abs(plan.final_target - plan.entry), arm=None),
    }
    out = {}
    for name, alt in alts.items():
        r = simulate(alt, bars_1m, close, cost=cost)
        out[f"cf_{name}_vote"] = r.vote if r.filled_at is not None else None
        out[f"cf_{name}_r"] = r.r if r.filled_at is not None else None
    return out


def run(bars_1m: pd.DataFrame, start: date, end: date, asset: str,
        params: model_2022.Params = model_2022.Params(), cap_scope: str = "window",
        extras: bool = True) -> pd.DataFrame:
    """``extras`` = shadow + counterfactual simulations (post-analysis); off for fast variant sweeps."""
    rows, d = [], start
    cost = COST.get(asset, 0.0)
    while d <= end:
        if d.weekday() < 5:
            try:
                ctx = build_context(bars_1m, d)
            except ValueError:
                ctx = None
            if ctx is not None and "pdh" in ctx.levels:
                setups = run_day(bars_1m, d, asset, params, cap_scope=cap_scope, ctx=ctx)
                outcome = day_outcome(bars_1m, d, ctx.levels["pdh"], ctx.levels["pdl"])
                close = pd.Timestamp(datetime.combine(d, time(16)), tz=NY)
                for s in setups:
                    shadow = simulate(s.would_plan, bars_1m, close, cost=cost) if s.would_plan and extras else None
                    row = setup_row(s, ctx, outcome, params.bias_rule, shadow)
                    if extras:
                        row.update(counterfactuals(s.would_plan, bars_1m, close, cost))
                    rows.append(row)
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def load_range(asset: str, start: date, end: date) -> pd.DataFrame:
    from ict_engine.data.dukascopy import load
    first = start - timedelta(days=70)                      # warm-up for 20/40/60-day ranges
    while True:
        try:
            return load(asset, first, end)
        except FileNotFoundError:
            first = (first.replace(day=1) + timedelta(days=32)).replace(day=1)
            if first > start:
                raise


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ict_engine.eval.backtest")
    ap.add_argument("asset")
    ap.add_argument("start", type=date.fromisoformat)
    ap.add_argument("end", type=date.fromisoformat)
    ap.add_argument("--cap", choices=("window", "day"), default="window")
    a = ap.parse_args(argv)
    df = run(load_range(a.asset, a.start, a.end), a.start, a.end, a.asset, cap_scope=a.cap)
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"backtest-{a.asset}-{a.start}-{a.end}{'-capday' if a.cap == 'day' else ''}.parquet"
    df.to_parquet(path)
    traded = df[df.status == "traded"]
    print(f"{path}\n{len(df)} setups, {len(traded)} trades, votes {int(traded.vote.sum())}, "
          f"expectancy {traded.r.mean():+.3f}R" if len(traded) else f"{path}\n{len(df)} setups, no trades")


if __name__ == "__main__":
    main()
