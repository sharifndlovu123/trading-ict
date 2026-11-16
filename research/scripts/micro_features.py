"""Market-microstructure components as features known at a time ``at``, and the study that tests each one on the
backtest trades (research/microstructure/2026-11-16-study.md).

    uv run python research/scripts/micro_features.py build     → reports/micro-features-2026-11-16.parquet
    uv run python research/scripts/micro_features.py study     → research/microstructure/results-2026-11-16.{md,csv}

Every feature reads only bars whose start minute is < ``at`` (a bar labelled t covers [t, t+1m) and is complete at
t+1m), so a feature at a trade's fill minute uses nothing from the fill bar or later. tests/test_micro_features.py
proves that for each function by scrambling everything from ``at`` on.

Sources (PDF pages, see .claude/skills/microstructure-library): lopez = López de Prado, Advances in Financial ML,
ch.19; bouchaud = Trades, Quotes and Prices; hasbrouck = Empirical Market Microstructure; p03-cont, p10-easley,
p11-andersen = papers in references/microstructure/papers.

Hold-outs: nothing dated 2021 or ≥ 2024-07-01 is used as a trade or an outcome. Bars from 2021-10 → 2021-12 are read
only as look-back history for the first 2022 trades (the same as act_rel in time_activity.py).
"""
from __future__ import annotations

import math
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

NY = "America/New_York"
ROOT = Path(__file__).resolve().parents[2]
UNSEEN = pd.Timestamp("2024-06-29", tz=NY)          # nothing at or after this is ever loaded
FEATURES_OUT = ROOT / "reports" / "micro-features-2026-11-16.parquet"
TRADES = ROOT / "reports" / "time-activity-2026-11-16.parquet"
OUT_DIR = ROOT / "research" / "microstructure"


# ───────────────────────────── windows ─────────────────────────────

def window(bars: pd.DataFrame, at: pd.Timestamp, mins: int, min_cover: float = 0.5) -> pd.DataFrame | None:
    """Bars with ``at − mins`` ≤ start < ``at``; None when fewer than ``min_cover`` of the minutes are there."""
    i0 = bars.index.searchsorted(at - pd.Timedelta(minutes=mins), "left")
    i1 = bars.index.searchsorted(at, "left")
    return bars.iloc[i0:i1] if i1 - i0 >= max(3, mins * min_cover) else None


def relative(fn, bars: pd.DataFrame, at: pd.Timestamp, days: int = 20, **kw) -> float:
    """``fn(bars, at)`` ÷ the median of ``fn`` at the same NY wall-clock time on the previous ``days`` weekdays
    (intraday seasonality removed: bouchaud §4.2, pp.78-80; orderflow.md §3 "seasonality and depth")."""
    now, base = fn(bars, at, **kw), seasonal(fn, bars, at, days, **kw)
    return now / base if _ok(now) and _ok(base) and base > 0 else math.nan


def seasonal(fn, bars: pd.DataFrame, at: pd.Timestamp, days: int = 20, **kw) -> float:
    """The normal value of ``fn`` for this clock time: median over the previous ``days`` weekdays (none later)."""
    past = []
    for k in range(1, days * 2):
        p = at - pd.DateOffset(days=k)                     # wall-clock days: DST-aware
        if p.weekday() >= 5:
            continue
        v = fn(bars, p, **kw)
        if _ok(v):
            past.append(v)
        if len(past) >= days:
            break
    return float(np.median(past)) if len(past) >= max(3, days // 4) else math.nan


def _ok(v) -> bool:
    return v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))


# ───────────────────────────── bar-based (Dukascopy or CME 1m bars) ─────────────────────────────

def realized_vol(bars, at, mins: int = 60) -> float:
    """√Σ(Δclose)² over the window, in price units: the size of a typical move over ``mins`` minutes
    (bouchaud §2.1, pp.42-46: variogram V(τ) = E[(p_{t+τ} − p_t)²])."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan
    d = np.diff(w.close.to_numpy())
    return float(np.sqrt((d * d).sum()))


def parkinson_vol(bars, at, mins: int = 60) -> float:
    """High-low volatility per bar: √(mean(ln(H/L)²) / (4 ln 2)) (lopez §19.3.3, pp.310-311)."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan
    x = np.log(w.high.to_numpy() / w.low.to_numpy())
    return float(np.sqrt((x * x).mean() / (4 * math.log(2))))


def _serial_cov(d: np.ndarray) -> float:
    x, y = d[1:], d[:-1]
    return float(((x - x.mean()) * (y - y.mean())).mean()) if len(x) >= 2 else math.nan


def roll_spread(bars, at, mins: int = 60) -> float:
    """Roll's implied spread 2·√max(0, −cov(Δp_t, Δp_{t−1})), price units (lopez §19.3.2, pp.309-310;
    hasbrouck ch.3, pp.34-41). 0 when the serial covariance is positive (trending)."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan
    c = _serial_cov(np.diff(w.close.to_numpy()))
    return math.nan if math.isnan(c) else 2 * math.sqrt(max(0.0, -c))


def return_autocorr(bars, at, mins: int = 60) -> float:
    """Lag-1 autocorrelation of 1m price changes: > 0 trending, < 0 bouncing (bouchaud §2.1.2, pp.43-44)."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan
    d = np.diff(w.close.to_numpy())
    v = d.var()
    return _serial_cov(d) / v if v > 0 else math.nan


def corwin_schultz(bars, at, mins: int = 60) -> float:
    """Corwin–Schultz high-low spread as a fraction of price, mean over consecutive bar pairs, negative α set to 0
    (lopez §19.3.4, pp.311-312): β = Σ_{j=0,1} ln(H_{t−j}/L_{t−j})², γ = ln(H_{t−1,t}/L_{t−1,t})²,
    α = (√(2β) − √β)/(3 − 2√2) − √(γ/(3 − 2√2)), S = 2(e^α − 1)/(1 + e^α)."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan
    h, lo = w.high.to_numpy(), w.low.to_numpy()
    x = np.log(h / lo) ** 2
    beta = x[1:] + x[:-1]
    gamma = np.log(np.maximum(h[1:], h[:-1]) / np.minimum(lo[1:], lo[:-1])) ** 2
    den = 3 - 2 * math.sqrt(2)
    alpha = np.maximum(0.0, (math.sqrt(2) - 1) * np.sqrt(beta) / den - np.sqrt(gamma / den))
    return float((2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))).mean())


def variance_ratio(bars, at, mins: int = 120, q: int = 5) -> float:
    """Var(q-minute changes) ÷ (q · Var(1-minute changes)), overlapping sums: > 1 trending, < 1 mean-reverting,
    1 for a random walk (the volatility signature plot: bouchaud §2.1.3, pp.44-46; lehalle §A.13, pp.343-344)."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan
    d = np.diff(w.close.to_numpy())
    if len(d) < 2 * q:
        return math.nan
    v1 = d.var(ddof=1)
    dq = np.convolve(d, np.ones(q), "valid")
    return float(dq.var(ddof=1) / (q * v1)) if v1 > 0 else math.nan


def amihud(bars, at, mins: int = 60) -> float:
    """Amihud illiquidity: mean |Δln close| ÷ volume over the bars that traded (lopez §19.4.2, pp.315-316).
    High = price moves a lot per unit traded; low = much volume for little movement (absorption)."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan
    r = np.abs(np.diff(np.log(w.close.to_numpy())))
    v = w.volume.to_numpy()[1:]
    ok = v > 0
    return float((r[ok] / v[ok]).mean()) if ok.sum() >= 3 else math.nan


def intensity(bars, at, mins: int = 60) -> float:
    """Volume traded (or quoted, on Dukascopy) in the window: the speed of the volume clock
    (lopez §2.3.1, pp.53-55; p10-easley pp.6-10)."""
    w = window(bars, at, mins)
    return math.nan if w is None else float(w.volume.sum())


def tick_signs(prices: np.ndarray) -> np.ndarray:
    """Tick rule: +1 if the price rose, −1 if it fell, the previous sign if unchanged; b₀ = +1
    (lopez §19.3.1, p.309)."""
    b, last = np.empty(len(prices)), 1.0
    for i in range(len(prices)):
        if i and prices[i] != prices[i - 1]:
            last = 1.0 if prices[i] > prices[i - 1] else -1.0
        b[i] = last
    return b


def tick_imbalance(bars, at, mins: int = 60, side: str = "long") -> float:
    """Signed-volume imbalance with bar-level tick-rule signs, Σ b·v / Σ v over the window, flipped for shorts
    (> 0 = with the trade). A delta proxy when no aggressor side exists (orderflow.md §2)."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan
    b, v = tick_signs(w.close.to_numpy())[1:], w.volume.to_numpy()[1:]
    if v.sum() <= 0:
        return math.nan
    i = float((b * v).sum() / v.sum())
    return i if side == "long" else -i


def kyle_lambda(dp: np.ndarray, x: np.ndarray) -> tuple[float, float]:
    """Kyle's λ: OLS slope (no intercept) of price change on signed volume, and its t-value
    (lopez §19.4.1, pp.313-315; bouchaud ch.15, pp.309-316). López prefers the t-value as the feature."""
    dp, x = np.asarray(dp, float), np.asarray(x, float)
    sxx = float((x * x).sum())
    if len(x) < 5 or sxx <= 0:
        return math.nan, math.nan
    lam = float((x * dp).sum() / sxx)
    e = dp - lam * x
    se = math.sqrt(float((e * e).sum()) / (len(x) - 1) / sxx)
    return lam, (lam / se if se > 0 else math.inf)


def kyle_bars(bars, at, mins: int = 60) -> tuple[float, float]:
    """Kyle's λ from bars alone: Δclose on tick-rule-signed bar volume."""
    w = window(bars, at, mins)
    if w is None:
        return math.nan, math.nan
    c = w.close.to_numpy()
    return kyle_lambda(np.diff(c), tick_signs(c)[1:] * w.volume.to_numpy()[1:])


def kyle_t_bars(bars, at, mins: int = 60) -> float:
    return kyle_bars(bars, at, mins)[1]


def volume_burst(bars, at, recent: int = 5, base: int = 60) -> float:
    """Largest 1m volume of the last ``recent`` minutes ÷ the median 1m volume of the ``base`` minutes before
    them: a burst of liquidity demand such as a stop run (harris §4.5, pp.92-93: stops "add momentum")."""
    w = window(bars, at, recent + base)
    if w is None or len(w) <= recent + 3:
        return math.nan
    v = w.volume.to_numpy()
    med = float(np.median(v[:-recent]))
    return float(v[-recent:].max() / med) if med > 0 else math.nan


def quoted_spread(bid: pd.DataFrame, ask: pd.DataFrame, at, mins: int = 60) -> float:
    """Mean quoted spread (ask.close − bid.close, crossed = 0) over the window, price units
    (harris ch.14, pp.310-334; bouchaud ch.16, pp.317-337)."""
    wb, wa = window(bid, at, mins), window(ask, at, mins)
    if wb is None or wa is None:
        return math.nan
    s = (wa.close - wb.close).dropna().clip(lower=0.0)
    return float(s.mean()) if len(s) >= 3 else math.nan


def spread_fn(both: pd.DataFrame, at, mins: int = 60) -> float:
    """``quoted_spread`` on one frame that carries a ``spread`` column (for ``relative``)."""
    w = window(both, at, mins)
    return math.nan if w is None else float(w.spread.mean())


# ───────────────────────────── flow-based (CME trades with aggressor side) ─────────────────────────────

def flow_imbalance(flow: pd.DataFrame, at, mins: int = 60, side: str = "long") -> float:
    """Aligned trade imbalance (buy − sell)/(buy + sell) over the approach (bouchaud §11.4, pp.241-242;
    p03-cont §4, pp.16-20). > 0 = aggressors traded with the position."""
    w = window(flow, at, mins)
    if w is None:
        return math.nan
    tot = float(w.buy.sum() + w.sell.sum())
    if tot <= 0:
        return math.nan
    i = float(w.buy.sum() - w.sell.sum()) / tot
    return i if side == "long" else -i


def cvd_divergence(price: pd.DataFrame, flow: pd.DataFrame, at, side: str = "long", recent: int = 15,
                   lookback: int = 120) -> float:
    """Cumulative-delta divergence into the entry. For a long: +1 = price made a new low in the last ``recent``
    minutes (vs the rest of ``lookback``) but cumulative delta did not; −1 = both made a new low (the flow
    confirms the move against the trade); 0 = no new price extreme. Mirrored for shorts. NaN without data."""
    wp, wf = window(price, at, lookback), window(flow, at, lookback)
    if wp is None or wf is None:
        return math.nan
    cut = at - pd.Timedelta(minutes=recent)
    cvd = wf.delta.cumsum()
    sgn = 1.0 if side == "long" else -1.0
    px = (wp.low if side == "long" else wp.high) * sgn        # for both sides: "new extreme" = a new minimum
    cv = cvd * sgn
    p_old, p_new, c_old, c_new = px[px.index < cut], px[px.index >= cut], cv[cv.index < cut], cv[cv.index >= cut]
    if min(len(p_old), len(p_new), len(c_old), len(c_new)) < 3:
        return math.nan
    if p_new.min() >= p_old.min():
        return 0.0
    return 1.0 if c_new.min() >= c_old.min() else -1.0


def absorbed(price: pd.DataFrame, flow: pd.DataFrame, at, side: str = "long", mins: int = 30) -> float:
    """1 when aggressors traded against the position over the window (aligned imbalance < 0) and the price did not
    move against it (aligned close-to-close change ≥ 0): effort without result. Else 0."""
    wp, i = window(price, at, mins), flow_imbalance(flow, at, mins, side)
    if wp is None or math.isnan(i):
        return math.nan
    move = float(wp.close.iloc[-1] - wp.close.iloc[0]) * (1 if side == "long" else -1)
    return float(i < 0 and move >= 0)


def vpin(flow: pd.DataFrame, at, bucket: float, n: int = 50, max_rows: int = 6000) -> float:
    """VPIN = Σ|V_buy − V_sell| / (n·V) over the last ``n`` volume buckets of size ``bucket`` that ended before
    ``at`` (p10-easley pp.6-10; lopez §19.5.2, pp.319-320; critique p11-andersen pp.16-28). Uses the exchange's
    aggressor side; a minute straddling two buckets is split in proportion."""
    i1 = flow.index.searchsorted(at, "left")
    w = flow.iloc[max(0, i1 - max_rows):i1]
    if not _ok(bucket) or bucket <= 0 or w.empty:
        return math.nan
    buy, sell = w.buy.to_numpy()[::-1], w.sell.to_numpy()[::-1]          # newest first
    cv = np.concatenate([[0.0], np.cumsum(buy + sell)])
    if cv[-1] < n * bucket:
        return math.nan
    edges = np.arange(n + 1) * bucket
    cb = np.interp(edges, cv, np.concatenate([[0.0], np.cumsum(buy)]))
    cs = np.interp(edges, cv, np.concatenate([[0.0], np.cumsum(sell)]))
    return float(np.abs(np.diff(cb) - np.diff(cs)).sum() / (n * bucket))


def vpin_bucket(daily_volume: pd.Series, at, days: int = 20, per_day: int = 50) -> float:
    """Bucket size = mean daily volume of the previous ``days`` sessions ÷ ``per_day`` (p10-easley). ``daily_volume``
    is indexed by date; only dates before ``at``'s date are read."""
    past = daily_volume[daily_volume.index < at.date()].tail(days)
    return float(past.mean() / per_day) if len(past) >= days // 2 else math.nan


def kyle_flow(price: pd.DataFrame, flow: pd.DataFrame, at, mins: int = 60) -> tuple[float, float]:
    """Kyle's λ with true signs: 1m Δclose on the minute's delta (same minutes in both frames)."""
    wp, wf = window(price, at, mins), window(flow, at, mins)
    if wp is None or wf is None:
        return math.nan, math.nan
    j = pd.concat([wp.close.diff().rename("dp"), wf.delta], axis=1).dropna()
    return kyle_lambda(j.dp.to_numpy(), j.delta.to_numpy())


def delta_autocorr(flow: pd.DataFrame, at, mins: int = 120) -> float:
    """Lag-1 autocorrelation of 1m delta: persistence of the order flow (bouchaud ch.10, pp.206-223;
    lopez §19.6.5, p.322)."""
    w = window(flow, at, mins)
    if w is None:
        return math.nan
    d = w.delta.to_numpy()
    v = d.var()
    return _serial_cov(d) / v if v > 0 else math.nan


def large_trade_share(trades: pd.DataFrame, at, mins: int = 60, min_size: int = 10) -> float:
    """Share of the window's volume done in trades of ≥ ``min_size`` contracts (order-size distribution:
    lopez §19.6.1, p.320; bouchaud §10.2, pp.208-209)."""
    i0 = trades.index.searchsorted(at - pd.Timedelta(minutes=mins), "left")
    i1 = trades.index.searchsorted(at, "left")
    s = trades["size"].to_numpy()[i0:i1]
    return float(s[s >= min_size].sum() / s.sum()) if len(s) >= 50 else math.nan


# ───────────────────────────── statistics ─────────────────────────────

def welch(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return 0.0 if se == 0 or math.isnan(se) else float((a.mean() - b.mean()) / se)


def prop_z(k1: int, n1: int, k2: int, n2: int) -> float:
    if not n1 or not n2:
        return 0.0
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return 0.0 if se == 0 else (k1 / n1 - k2 / n2) / se


def p_two_sided(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2))


def bh(pvals: list[float], q: float = 0.10) -> list[bool]:
    """Benjamini–Hochberg: which tests pass at false-discovery rate ``q``."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    ok, cut = [False] * m, 0
    for rank, i in enumerate(order, 1):
        if pvals[i] <= q * rank / m:
            cut = rank
    for rank, i in enumerate(order, 1):
        ok[i] = rank <= cut
    return ok


def cluster_z(y, X, groups) -> np.ndarray:
    """OLS of y on X (an intercept is added) with cluster-robust standard errors; z of each X column.
    Trades on one day are not independent (several models take the same move; the indices move together)."""
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(y)), np.asarray(X, float).reshape(len(y), -1)])
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    e = y - X @ beta
    g = pd.factorize(np.asarray(groups))[0]
    S = np.zeros((X.shape[1], g.max() + 1))
    np.add.at(S.T, g, X * e[:, None])
    V = xtx_inv @ (S @ S.T) @ xtx_inv
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(se > 0, beta / se, 0.0)[1:]


def terciles(x: pd.Series, groups: pd.Series) -> pd.Series:
    """0 / 1 / 2 by thirds of ``x`` within each group (a dataset), so assets and periods aren't mixed."""
    pct = x.groupby(groups).rank(pct=True)
    return pd.Series(np.select([pct <= 1 / 3, pct > 2 / 3], [0.0, 2.0], 1.0), index=x.index).where(x.notna())


def evaluate(df: pd.DataFrame, col: str, split: str = "dataset", binary: bool = False, min_cell: int = 15) -> dict:
    """Top vs bottom third of ``col`` (or 1 vs 0 for ``binary``): n, win %, mean R per bucket, differences with
    Welch z and day-clustered z, the sign count across ``split`` values, the capped-R version, and the overlap
    with act_rel."""
    d = df[df[col].notna()].copy()
    d["b"] = d[col].astype(float) * 2 if binary else terciles(d[col], d.dataset)
    lo, hi = d[d.b == 0], d[d.b == 2]
    out = {"component": col, "n": len(d)}
    for name, g in (("lo", lo), ("mid", d[d.b == 1]), ("hi", hi)):
        out |= {f"n_{name}": len(g), f"win_{name}": g.win.mean() * 100 if len(g) else math.nan,
                f"r_{name}": g.r.mean() if len(g) else math.nan}
    if len(lo) < 5 or len(hi) < 5:
        return out | {"z_r": 0.0, "z_win": 0.0, "p_r": 1.0, "p_win": 1.0}
    e = pd.concat([lo, hi])
    top = (e.b == 2).astype(float)
    out["d_r"], out["z_r"] = hi.r.mean() - lo.r.mean(), welch(hi.r, lo.r)
    out["zc_r"] = float(cluster_z(e.r, top, e.day)[0])
    out["d_win"] = (hi.win.mean() - lo.win.mean()) * 100
    out["z_win"] = prop_z(int(hi.win.sum()), len(hi), int(lo.win.sum()), len(lo))
    out["zc_win"] = float(cluster_z(e.win.astype(float), top, e.day)[0])
    cap_hi, cap_lo = hi.r.clip(upper=10), lo.r.clip(upper=10)
    out["d_r_cap"], out["z_r_cap"] = cap_hi.mean() - cap_lo.mean(), welch(cap_hi, cap_lo)
    same_r = same_w = cells = 0
    for _, g in e.groupby(split):
        a, b = g[g.b == 2], g[g.b == 0]
        if len(a) < min_cell or len(b) < min_cell:
            continue
        cells += 1
        same_r += np.sign(a.r.mean() - b.r.mean()) == np.sign(out["d_r"])
        same_w += np.sign(a.win.mean() - b.win.mean()) == np.sign(out["d_win"])
    out |= {"cells": cells, "same_r": int(same_r), "same_win": int(same_w)}
    a = d.dropna(subset=[col, "act_rel"])
    out["rho_act"] = float(a[col].rank().corr(a["act_rel"].rank())) if len(a) > 10 else math.nan   # Spearman
    c = e.dropna(subset=["act_rel"])
    if len(c) > 30 and col != "act_rel":                   # does it say anything once activity is known?
        ar = c.act_rel.groupby(c.dataset).rank(pct=True)
        zz = cluster_z(c.r, np.column_stack([(c.b == 2).astype(float), ar]), c.day)
        zw = cluster_z(c.win.astype(float), np.column_stack([(c.b == 2).astype(float), ar]), c.day)
        out["zc_r_given_act"], out["zc_win_given_act"] = float(zz[0]), float(zw[0])
    out["p_r"], out["p_win"] = p_two_sided(out["z_r"]), p_two_sided(out["z_win"])
    return out


# ───────────────────────────── building the feature table ─────────────────────────────

BAR_COMPONENTS = ["spread_rel", "spread_r", "roll_sig", "autocorr1", "cs_bp", "rv_rel", "pk_rel", "tod_season", "vr5",
                  "amihud_rel", "intensity_rel", "tick_imb", "kyle_t", "vol_burst", "risk_sigma"]
FLOW_COMPONENTS = ["imb30", "imb60", "imb120", "cvd_div", "absorbed", "vpin", "kyle_t_true", "nq_amihud_rel",
                   "nq_intensity_rel", "delta_ac", "large_share"]
MODEL_FILES = {"2022_model": "backtest-{a}", "mmxm": "backtest-mmxm-{a}", "silver_bullet": "backtest-silver_bullet-{a}"}
SPANS = {"2022-24": "2022-01-03-2024-06-28", "2020": "2020-01-02-2020-12-31"}


def load_trades() -> pd.DataFrame:
    """The study's trades (cameron and MMxM-on-gold dropped) with entry / stop / risk from the source backtests."""
    t = pd.read_parquet(TRADES)
    t = t[(t.family != "cameron") & ~((t.family == "mmxm") & (t.asset == "XAUUSD"))].copy()
    assert t.filled_at.max() < UNSEEN and not (t.filled_at.dt.year == 2021).any()
    src = []
    for (per, a, fam), _ in t.groupby(["period", "asset", "family"]):
        f = ROOT / "reports" / f"{MODEL_FILES[fam].format(a=a)}-{SPANS[per]}-futures.parquet"
        d = pd.read_parquet(f, columns=["status", "side", "filled_at", "decided_at", "entry", "stop", "tp1", "risk", "r"])
        d = d[(d.status == "traded") & d.r.notna() & d.filled_at.notna()].copy()
        d["filled_at"] = pd.to_datetime(d.filled_at, utc=True).dt.tz_convert(NY)
        d["period"], d["asset"], d["family"] = per, a, fam
        src.append(d.drop(columns=["status", "r"]))
    key = ["period", "asset", "family", "filled_at", "side"]
    t = t.merge(pd.concat(src).drop_duplicates(key), on=key, how="left", validate="m:1")
    t["dataset"] = t.asset + " " + t.period
    t["day"] = t.filled_at.dt.strftime("%Y-%m-%d")
    return t.reset_index(drop=True)


def _bars(asset: str, period: str, price: str = "bid") -> pd.DataFrame:
    from ict_engine.data import dukascopy
    a, b = (date(2019, 10, 1), date(2020, 12, 31)) if period == "2020" else (date(2021, 10, 1), date(2024, 6, 28))
    d = dukascopy.load(asset, a, b, price=price)
    return d[d.index < UNSEEN]


def bar_features(args) -> pd.DataFrame:
    asset, period, rows = args
    bars = _bars(asset, period)
    try:
        ask = _bars(asset, period, "ask")
        both = pd.DataFrame({"spread": (ask.close - bars.close).clip(lower=0.0)}).dropna()
    except FileNotFoundError:
        both = None
    out = []
    for i, side, at, risk in rows:
        rv = realized_vol(bars, at)
        s1 = rv / math.sqrt(59) if _ok(rv) else math.nan           # per-minute σ over the last hour
        roll = roll_spread(bars, at)
        w = window(bars, at, 60)
        px = float(w.close.iloc[-1]) if w is not None else math.nan
        f = {"i": i, "rv60": rv, "roll": roll,
             "roll_sig": roll / s1 if _ok(roll) and _ok(s1) and s1 > 0 else math.nan,
             "autocorr1": return_autocorr(bars, at),
             "cs_bp": corwin_schultz(bars, at) * 1e4,
             "rv_rel": relative(realized_vol, bars, at),
             "pk_rel": relative(parkinson_vol, bars, at),
             "vr5": variance_ratio(bars, at),
             "amihud_rel": relative(amihud, bars, at),
             "intensity_rel": relative(intensity, bars, at),
             "tick_imb": tick_imbalance(bars, at, 60, side),
             "kyle_t": kyle_t_bars(bars, at),
             "vol_burst": volume_burst(bars, at),
             "risk_sigma": risk / rv if _ok(rv) and rv > 0 and _ok(risk) else math.nan,
             "px": px}
        if both is not None:
            sp = spread_fn(both, at)
            f |= {"spread": sp, "spread_rel": relative(spread_fn, both, at),
                  "spread_r": sp / risk if _ok(sp) and _ok(risk) and risk > 0 else math.nan}
        out.append(f)
    return pd.DataFrame(out)


def flow_features(t: pd.DataFrame) -> pd.DataFrame:
    """Flow components for US100 trades filled 2024-01-02 → 2024-06-28 (NQ, in-sample half only)."""
    from ict_engine.data import orderflow
    flow = pd.read_parquet(ROOT / "data" / "orderflow" / "NQ-flow1m-2024.parquet")
    flow = flow[flow.index < UNSEEN]
    nq = orderflow.load(date(2023, 10, 1), date(2024, 6, 29), schema=orderflow.BARS)
    nq = orderflow.tidy_bars(nq) if "ts_event" in nq.columns else nq
    nq = nq[nq.index < UNSEEN]
    hrs = nq[(nq.index.hour * 60 + nq.index.minute >= 90) & (nq.index.hour < 17)]
    daily = hrs.volume.groupby(hrs.index.date).sum()
    u = t[(t.asset == "US100") & (t.filled_at >= pd.Timestamp("2024-01-02", tz=NY)) & (t.filled_at < UNSEEN)]
    out = []
    for i, r in u.iterrows():
        at, side = r.filled_at, r.side
        out.append({"i": i, "imb30": flow_imbalance(flow, at, 30, side), "imb60": flow_imbalance(flow, at, 60, side),
                    "imb120": flow_imbalance(flow, at, 120, side), "cvd_div": cvd_divergence(nq, flow, at, side),
                    "absorbed": absorbed(nq, flow, at, side), "vpin": vpin(flow, at, vpin_bucket(daily, at)),
                    "kyle_t_true": kyle_flow(nq, flow, at)[1], "nq_amihud_rel": relative(amihud, nq, at),
                    "nq_intensity_rel": relative(intensity, nq, at), "delta_ac": delta_autocorr(flow, at)})
    o = pd.DataFrame(out).set_index("i")
    o["large_share"] = math.nan
    for m in range(1, 7):                                  # trades month by month (≈ 8M rows each)
        f = ROOT / "data" / "orderflow" / f"NQ-trades-2024-{m:02d}.parquet"
        um = u[u.filled_at.dt.month == m]
        if not f.exists() or um.empty:
            continue
        tr = pd.read_parquet(f, columns=["size"])
        tr = tr[tr.index < UNSEEN]
        for i, r in um.iterrows():
            o.loc[i, "large_share"] = large_trade_share(tr, r.filled_at)
        del tr
    return o


def build() -> pd.DataFrame:
    from multiprocessing import Pool
    t = load_trades()
    jobs = [(a, p, [(i, r.side, r.filled_at, r.risk) for i, r in g.iterrows()])
            for (a, p), g in t.groupby(["asset", "period"])]
    with Pool(4) as pool:                                  # ≤ 4 workers
        parts = pool.map(bar_features, jobs)
    f = pd.concat(parts).set_index("i")
    t = t.join(f)
    t["tod_season"] = t.act_range_adr / t.act_rel          # the normal 60-min range for this clock time, in ADR
    t = t.join(flow_features(t))
    t.to_parquet(FEATURES_OUT)
    print(len(t), "trades →", FEATURES_OUT)
    return t


# ───────────────────────────── the study ─────────────────────────────

def _fmt(v, nd=2, sign=False):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    return f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"


def study() -> None:
    t = pd.read_parquet(FEATURES_OUT)
    assert t.filled_at.max() < UNSEEN and not (t.filled_at.dt.year == 2021).any()
    rows = []
    ref = evaluate(t, "act_rel") | {"kind": "reference"}
    for c in BAR_COMPONENTS:
        rows.append(evaluate(t, c) | {"kind": "bars"})
    u = t[t.imb30.notna() | t.vpin.notna() | t.cvd_div.notna()].copy()
    u["half"] = np.where(u.filled_at.dt.month <= 3, "2024-Q1", "2024-Q2")
    for c in FLOW_COMPONENTS:
        if c == "cvd_div":                                 # divergence (+1) vs flow-confirmed new extreme (−1)
            v = u.assign(cvd_div=u.cvd_div.map({1.0: 1.0, -1.0: 0.0}))
            rows.append(evaluate(v, c, split="half", binary=True, min_cell=8) | {"kind": "flow"})
        else:
            rows.append(evaluate(u, c, split="half", binary=c == "absorbed", min_cell=8) | {"kind": "flow"})
    res = pd.DataFrame(rows)
    p = list(res.p_r) + list(res.p_win)
    ok = bh(p, 0.10)
    res["bh_r"], res["bh_win"] = ok[:len(res)], ok[len(res):]
    res = pd.concat([pd.DataFrame([ref]), res], ignore_index=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT_DIR / "results-2026-11-16.csv", index=False)
    L = [f"Tests: {len(p)} ({len(rows)} components × 2 targets: mean R and win rate). Benjamini–Hochberg q 0.10 on the "
         f"Welch / two-proportion p-values; passing: {sum(ok)}.", "",
         "| Component | n | Bottom third: n · win % · R | Middle | Top third: n · win % · R | ΔR top−bottom (z; day-clustered z) "
         "| ΔR capped 10R (z) | Δwin pts (z; clustered) | Same sign: R / win | ρ with act_rel | z after activity: R / win | FDR |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in res.iterrows():
        cell = lambda k: f"{int(r['n_' + k])} · {_fmt(r['win_' + k], 1)} · {_fmt(r['r_' + k], 3, True)}"  # noqa: E731
        fdr = "ref" if r.kind == "reference" else ("R" if r.bh_r else "") + (" win" if r.bh_win else "") or "no"
        L.append(f"| {r.component} | {int(r.n)} | {cell('lo')} | {cell('mid')} | {cell('hi')} | "
                 f"{_fmt(r.get('d_r'), 3, True)} ({_fmt(r.get('z_r'), 2, True)}; {_fmt(r.get('zc_r'), 2, True)}) | "
                 f"{_fmt(r.get('d_r_cap'), 3, True)} ({_fmt(r.get('z_r_cap'), 2, True)}) | "
                 f"{_fmt(r.get('d_win'), 1, True)} ({_fmt(r.get('z_win'), 2, True)}; {_fmt(r.get('zc_win'), 2, True)}) | "
                 f"{_fmt(r.get('same_r'), 0)}/{_fmt(r.get('cells'), 0)} · {_fmt(r.get('same_win'), 0)}/{_fmt(r.get('cells'), 0)} | "
                 f"{_fmt(r.get('rho_act'), 2, True)} | {_fmt(r.get('zc_r_given_act'), 2, True)} / "
                 f"{_fmt(r.get('zc_win_given_act'), 2, True)} | {fdr} |")
    (OUT_DIR / "results-2026-11-16.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    {"build": build, "study": study}[sys.argv[1] if len(sys.argv) > 1 else "study"]()
