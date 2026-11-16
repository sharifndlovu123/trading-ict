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
    return (d if _W.get("unseen") else d[d.filled_at < UNSEEN]).reset_index(drop=True)


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
           "k_momentum": k["momentum_adr_per_candle"], "k_range_tf": k["range_tf"],
           "k_activity": (k.get("activity") or {}).get("state"), "k_activity_rel": (k.get("activity") or {}).get("relative"),
           "k_activity_range_adr": (k.get("activity") or {}).get("range_adr"),
           "k_activity_net_adr": (k.get("activity") or {}).get("net_adr"),
           "k_session": k.get("session") or "normal",
           "k_flow_imb_5m": (k.get("order_flow") or {}).get("imb_5m"), "k_flow_imb_60m": (k.get("order_flow") or {}).get("imb_60m"),
           "k_flow_with_trade_60m": (k.get("order_flow") or {}).get("with_trade_60m"),
           "k_flow_rel_volume": (k.get("order_flow") or {}).get("rel_volume")}
    o = a["own"]
    out |= {"cf_mfe_r": o.get("mfe_r"), "cf_mae_r": o.get("mae_r"), "cf_overnight": o.get("overnight"),
            "cf_day_only_r": (a.get("day_only") or {}).get("r"), "cf_best_r": (a.get("reach") or {}).get("best_r"),
            "cf_stopped_then_target": a.get("stopped_then_target") is not None if o.get("why") == "stop" else None}
    tn = a.get("turn") or {}
    out |= {"cf_turn_depth_r": tn.get("depth_r"), "cf_turn_depth_adr": tn.get("depth_adr"),
            "cf_turn_beyond_stop_adr": tn.get("beyond_stop_adr"), "cf_turn_at_known_level": tn.get("at_known_level"),
            "cf_turn_run_after_adr": tn.get("run_after_adr"),
            "cf_turn_level": (tn.get("levels") or [None])[0]}
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
    early = ("US100", "US500", "US30", "US2000", "DE40", "UK100")          # cached from 2019-10; the rest from 2021-10
    return {a: dukascopy.load(a, date(2019, 10, 1) if a in early else date(2021, 10, 1), date(2026, 11, 14) if _W.get("unseen") else date(2024, 7, 5)) for a in assets}


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


def pick_balanced(frames: list[pd.DataFrame], n_each: int, seed: int = 7) -> pd.DataFrame:
    """``n_each`` winners and ``n_each`` losers, spread evenly over the given runs (model × asset), seeded."""
    out = []
    for won in (True, False):
        per, left = divmod(n_each, len(frames))
        for i, d in enumerate(frames):
            g = d[(d.r > 0) == won]
            k = min(len(g), per + (1 if i < left else 0))
            out.append(g.sample(k, random_state=seed + i))
    return pd.concat(out).sort_values("filled_at")


def sheets(path: str, n: int, out: Path, balanced: int = 0):
    paths = path.split(",")
    d = pick_balanced([traded(p) for p in paths], balanced) if balanced else pick(traded(paths[0]), n)
    bars = _bars(d.asset.unique())
    out.mkdir(parents=True, exist_ok=True)
    for r in d.itertuples():
        f = te.evaluate(r.asset, r.side, r.filled_at, float(r.entry), float(r.stop), _tps(r), be=True, bars=bars[r.asset])
        area = getattr(r, "liquidity", None)
        gap = getattr(r, "fvg_size", None)
        dec = getattr(r, "decided_at", None)
        note = (f"[engine {r.model} trade · window {r.window} · POI {r.poi} · bias {r.bias} · engine result {r.r:+.2f} R ({r.exit})"
                + (f" · area / liquidity: {area}" if isinstance(area, str) and area else "")
                + (f" · decided {pd.Timestamp(dec).tz_convert(te.NY):%H:%M}" if dec is not None and pd.notna(dec) else "")
                + (f" · trigger gap {float(gap):.2f} points" if gap is not None and pd.notna(gap) else "") + "]")
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
    ap.add_argument("--balanced", type=int, default=0, help="sheets: this many winners and this many losers, spread over the comma-separated runs")
    ap.add_argument("--include-unseen", action="store_true",
                    help="only for reviewing the trades of a pre-registered confirmation run on 2024-07 onward")
    a = ap.parse_args()
    _W["unseen"] = a.include_unseen
    if a.cmd == "facts":
        facts(a.path, a.workers, a.max)
    else:
        sheets(a.path, a.n, a.out or Path("research/trade-reviews/sheets") / Path(a.path.split(",")[0]).stem, a.balanced)


if __name__ == "__main__":
    main()
