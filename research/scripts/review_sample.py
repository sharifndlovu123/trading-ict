"""Trade-review facts at scale: the checklist facts of trade_eval.py for every traded row of a backtest, so the
pattern finder can test the review rubric across all trades — and a stratified subset of fact sheets for written
reviews (trade-review skill).

    uv run python research/scripts/review_sample.py facts reports/backtest-mmxm-US100-...-futures.parquet [--workers 8] [--max 400]
        → reports/trade-facts-<name>.parquet   (the backtest's columns + k_* traits known at the entry + cf_* hindsight)
    uv run python research/scripts/review_sample.py sheets reports/backtest-...parquet --n 12 --out research/trade-reviews/sheets/<name>
        → one fact sheet (.md) per sampled trade: 4 worst, 4 typical losers, 2 winners, 2 stopped-then-target if any

k_* columns are known at the entry (traits). cf_* columns are hindsight (never traits; pattern_find skips cf_*).
Rows on or after 2024-07-01 are dropped (unseen data).
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trade_eval as te  # noqa: E402

UNSEEN = pd.Timestamp("2024-07-01", tz=te.NY)
_W: dict = {}


def traded(path: str) -> pd.DataFrame:
    d = pd.read_parquet(path)
    d = d[(d.status == "traded") & d.r.notna() & d.filled_at.notna()].copy()
    d["filled_at"] = pd.to_datetime(d.filled_at, utc=True).dt.tz_convert(te.NY)
    return d[d.filled_at < UNSEEN].reset_index(drop=True)


def traits(f: dict) -> dict:
    """Flat k_* (known at the entry) and cf_* (hindsight) columns from one evaluate() result."""
    k, a, long = f["known"], f["after"], f["side"] == "long"
    rg, st, tp = k["range"] or {}, k["levels"]["stop"] or {}, k["levels"]["tp1"] or {}
    against = "sellside" if long else "buyside"            # the pool a long wants taken first is sellside
    sw = k["swept_before"]
    out = {"k_side_matches_read": k["side_matches_read"], "k_read_kind": k["read_kind"],
           "k_right_half": rg.get("right_half"), "k_in_ote": rg.get("ote"),
           "k_range_depth": (None if not rg else round(rg["fraction_from_low"] if not long else 1 - rg["fraction_from_low"], 3)),
           "k_swept_before": bool(sw), "k_swept_our_side": any(s["role"] == against for s in sw),
           "k_stop_beyond_pool": st.get("beyond_it"), "k_stop_at_liquidity": st.get("at_liquidity"),
           "k_stop_gap_adr": st.get("gap_adr"), "k_pools_before_tp1": len(tp.get("pools_before", [])),
           "k_tp1_just_past_pool": bool(tp.get("just_past_a_pool")), "k_risk_adr": k["risk_adr"], "k_rr_tp1": k["rr_tp1"],
           "k_news_within_30m": bool(k["news"] and abs(k["news"]["mins"]) <= 30),
           "k_momentum": k["momentum_adr_per_candle"], "k_range_tf": k["range_tf"]}
    o = a["own"]
    out |= {"cf_mfe_r": o.get("mfe_r"), "cf_mae_r": o.get("mae_r"), "cf_overnight": o.get("overnight"),
            "cf_day_only_r": (a.get("day_only") or {}).get("r"), "cf_best_r": (a.get("reach") or {}).get("best_r"),
            "cf_stopped_then_target": a.get("stopped_then_target") is not None if o.get("why") == "stop" else None}
    return out


def _tps(r) -> list[tuple[float, float]]:
    return [(r.tp1, 0.5), (r.final, 0.5)] if abs(r.final - r.tp1) > 1e-9 else [(r.tp1, 1.0)]


def _one(i: int):
    r = _W["rows"].iloc[i]
    try:
        f = te.evaluate(r.asset, r.side, r.filled_at, float(r.entry), float(r.stop), _tps(r), be=True, bars=_W["bars"][r.asset])
        return i, traits(f)
    except Exception as e:                                   # keep the row, mark the failure
        return i, {"k_error": f"{type(e).__name__}: {e}"[:120]}


def _bars(assets) -> dict:
    from ict_engine.data import dukascopy
    return {a: dukascopy.load(a, date(2019, 10, 1) if a.startswith("US") else date(2021, 10, 1), date(2024, 7, 5)) for a in assets}


def facts(path: str, workers: int, cap: int) -> Path:
    d = traded(path)
    if cap and len(d) > cap:
        d = d.sample(cap, random_state=7).sort_values("filled_at").reset_index(drop=True)
    _W["rows"], _W["bars"] = d, _bars(d.asset.unique())
    with mp.get_context("fork").Pool(min(workers, 10)) as pool:
        res = dict(pool.imap_unordered(_one, range(len(d)), chunksize=4))
    out = pd.concat([d, pd.DataFrame([res[i] for i in range(len(d))])], axis=1)
    dst = Path("reports") / ("trade-facts-" + Path(path).stem.replace("backtest-", "") + ".parquet")
    out.to_parquet(dst)
    print(len(out), "trades →", dst, "| errors:", int(out.get("k_error", pd.Series(dtype=object)).notna().sum()))
    return dst


def pick(d: pd.DataFrame, n: int) -> pd.DataFrame:
    """A stratified subset for written reviews: the worst, typical losers, winners (seeded, spread over time)."""
    lose, win = d[d.r <= 0], d[d.r > 0]
    q = max(1, n // 3)
    parts = [lose.nsmallest(q, "r"), lose.drop(lose.nsmallest(q, "r").index).sample(min(q, max(0, len(lose) - q)), random_state=7),
             win.sample(min(n - 2 * q, len(win)), random_state=7)]
    return pd.concat(parts).sort_values("filled_at")


def sheets(path: str, n: int, out: Path):
    d = pick(traded(path), n)
    bars = _bars(d.asset.unique())
    out.mkdir(parents=True, exist_ok=True)
    for r in d.itertuples():
        f = te.evaluate(r.asset, r.side, r.filled_at, float(r.entry), float(r.stop), _tps(r), be=True, bars=bars[r.asset])
        note = f"[engine {r.model} trade · window {r.window} · POI {r.poi} · bias {r.bias} · engine result {r.r:+.2f} R ({r.exit})]"
        name = f"{r.filled_at:%Y-%m-%d-%H%M}-{r.asset}-{r.side}-{r.model}.md"
        (out / name).write_text(te.markdown(f, note))
        print(name, f"{r.r:+.2f} R")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["facts", "sheets"])
    ap.add_argument("path")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max", type=int, default=0, help="facts: sample at most this many trades")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.cmd == "facts":
        facts(a.path, a.workers, a.max)
    else:
        sheets(a.path, a.n, a.out or Path("research/trade-reviews/sheets") / Path(a.path).stem)


if __name__ == "__main__":
    main()
