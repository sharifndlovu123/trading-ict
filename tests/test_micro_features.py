"""Microstructure features (research/scripts/micro_features.py) on hand-built bars with known answers, and the proof
that none of them reads anything at or after ``at`` (no look-ahead): every bar from ``at`` on is scrambled and the
value must not change."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import micro_features as mf  # noqa: E402

NY = "America/New_York"
T0 = "2024-01-09 09:30"


def bars(closes, highs=None, lows=None, vol=None, start=T0):
    c = np.asarray(closes, float)
    idx = pd.date_range(start, periods=len(c), freq="1min", tz=NY)
    return pd.DataFrame({"open": c, "high": c if highs is None else np.asarray(highs, float),
                         "low": c if lows is None else np.asarray(lows, float), "close": c,
                         "volume": np.ones(len(c)) if vol is None else np.asarray(vol, float)}, index=idx)


def flow(buy, sell, start=T0):
    idx = pd.date_range(start, periods=len(buy), freq="1min", tz=NY)
    b, s = np.asarray(buy, float), np.asarray(sell, float)
    return pd.DataFrame({"volume": b + s, "buy": b, "sell": s, "delta": b - s}, index=idx)


def end(df):
    return df.index[-1] + pd.Timedelta(minutes=1)


# ── windows ──

def test_window_excludes_the_bar_at_at_and_needs_cover():
    b = bars(range(10))
    w = mf.window(b, b.index[6], 4)
    assert list(w.close) == [2, 3, 4, 5]                    # 09:32 … 09:35; the 09:36 bar is not complete yet
    assert mf.window(b, b.index[1], 60) is None             # 1 bar of 60


# ── bar-based, known answers ──

def test_realized_vol():
    b = bars([10, 11, 9, 12])                               # changes +1, −2, +3
    assert mf.realized_vol(b, end(b), 4) == pytest.approx(math.sqrt(14))


def test_parkinson():
    b = bars([100] * 5, highs=[100 * math.exp(0.1)] * 5, lows=[100] * 5)
    assert mf.parkinson_vol(b, end(b), 5) == pytest.approx(0.1 / math.sqrt(4 * math.log(2)))


def test_roll_spread_hand_computed_and_zero_when_trending():
    b = bars([10, 11, 10, 11, 10])                          # Δ = +1 −1 +1 −1 → serial cov = −8/9
    assert mf.roll_spread(b, end(b), 5) == pytest.approx(2 * math.sqrt(8 / 9))
    assert mf.return_autocorr(b, end(b), 5) == pytest.approx(-8 / 9)
    up = bars([10, 11, 13, 16, 20, 25])                     # accelerating trend → positive covariance → 0
    assert mf.roll_spread(up, end(up), 6) == 0.0
    assert mf.return_autocorr(up, end(up), 6) > 0


def test_roll_recovers_a_simulated_spread():
    rng = np.random.default_rng(7)
    n, c = 4000, 0.5                                        # random-walk mid + iid bounce of ± half-spread
    mid = 100 + np.cumsum(rng.normal(0, 0.3, n))
    b = bars(mid + c * rng.choice([-1, 1], n))
    assert mf.roll_spread(b, end(b), n) == pytest.approx(2 * c, rel=0.1)


def test_corwin_schultz_pure_spread_and_trend():
    # the same range on every bar: all of it is spread
    b3 = bars([100.5] * 3, highs=[101] * 3, lows=[100] * 3)
    assert mf.corwin_schultz(b3, end(b3), 3) == pytest.approx(2 * 0.01 / 2.01)      # α = ln 1.01
    tr = bars([100.5, 101.5, 102.5], highs=[101, 102, 103], lows=[100, 101, 102])   # range doubles over 2 bars
    assert mf.corwin_schultz(tr, end(tr), 3) == 0.0                                 # α < 0 → 0 (all volatility)


def test_variance_ratio():
    b = bars(np.cumsum([0, 1, -1, 1, -1, 1, -1, 1, -1]))    # perfectly bouncing → 2-minute sums are all 0
    assert mf.variance_ratio(b, end(b), 9, q=2) == pytest.approx(0.0)
    b = bars(np.cumsum([0, 1, 1, -1, -1, 1, 1, -1, -1]))    # runs of two → VR(2) = (16/6) / (2 · 8/7)
    assert mf.variance_ratio(b, end(b), 9, q=2) == pytest.approx((16 / 6) / (2 * 8 / 7))
    rng = np.random.default_rng(1)
    rw = bars(np.cumsum(rng.normal(size=5000)))
    assert mf.variance_ratio(rw, end(rw), 5000, q=5) == pytest.approx(1.0, abs=0.1)


def test_amihud_and_intensity():
    b = bars([100, 100 * math.exp(0.01), 100, 100], vol=[5, 2, 4, 0])     # |r| = .01, .01, 0; volumes 2, 4, 0
    assert mf.amihud(bars([100, 100 * math.exp(0.01), 100, 100 * math.exp(0.02)], vol=[5, 2, 4, 8]), end(b), 4) == \
        pytest.approx((0.01 / 2 + 0.01 / 4 + 0.02 / 8) / 3)
    assert mf.intensity(b, end(b), 4) == 11


def test_tick_rule_and_imbalance():
    assert list(mf.tick_signs(np.array([5, 5, 6, 6, 4, 4, 7.0]))) == [1, 1, 1, 1, -1, -1, 1]
    b = bars([10, 11, 11, 10, 12], vol=[9, 1, 2, 3, 4])     # signs after the first bar: + + − + → (1+2−3+4)/10
    assert mf.tick_imbalance(b, end(b), 5, "long") == pytest.approx(0.4)
    assert mf.tick_imbalance(b, end(b), 5, "short") == pytest.approx(-0.4)


def test_kyle_lambda():
    x = np.array([1, -2, 3, -1, 2, -3.0])
    lam, t = mf.kyle_lambda(2 * x, x)
    assert lam == pytest.approx(2) and t == math.inf
    e = np.array([1, -1, 1, -1, 1, -1.0])
    lam, t = mf.kyle_lambda(2 * x + e, x)                   # by hand: Σx² = 28, Σxe = 12 → λ = 2 + 12/28
    assert lam == pytest.approx(2 + 12 / 28)
    resid = 2 * x + e - lam * x
    assert t == pytest.approx(lam / math.sqrt((resid ** 2).sum() / 5 / 28))
    b = bars([10, 12, 11, 15, 13, 14], vol=[1, 2, 1, 4, 2, 1])            # Δp = +2 −1 +4 −2 +1 on signed vol
    assert mf.kyle_bars(b, end(b), 6)[0] == pytest.approx(1.0)


def test_volume_burst():
    b = bars([1] * 10, vol=[2, 2, 2, 2, 2, 2, 2, 3, 10, 4])
    assert mf.volume_burst(b, end(b), recent=3, base=7) == pytest.approx(5.0)


def test_quoted_spread():
    bid, ask = bars([10, 10, 10, 10]), bars([10.5, 11, 9, 10.5])          # crossed minute counts as 0
    assert mf.quoted_spread(bid, ask, end(bid), 4) == pytest.approx((0.5 + 1 + 0 + 0.5) / 4)


def test_relative_uses_the_same_clock_on_previous_weekdays_only():
    days = pd.bdate_range("2024-01-02", "2024-01-12")
    parts = []
    for k, d in enumerate(days):                            # 09:00–09:59 each day; volume k+1 per minute
        idx = pd.date_range(f"{d.date()} 09:00", periods=60, freq="1min", tz=NY)
        parts.append(pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": k + 1.0}, index=idx))
    b = pd.concat(parts)
    at = pd.Timestamp("2024-01-12 10:00", tz=NY)            # last day: 9/min → 540; earlier days 60 … 480, median 270
    assert mf.seasonal(mf.intensity, b, at, days=8) == pytest.approx(270)
    assert mf.relative(mf.intensity, b, at, days=8) == pytest.approx(2.0)
    later = b.copy()
    later.loc[later.index >= at - pd.Timedelta(minutes=60), "volume"] = 1e9      # today's hour is not in its own norm
    assert mf.seasonal(mf.intensity, later, at, days=8) == pytest.approx(270)


def test_relative_is_wall_clock_across_dst():
    # US clocks moved on 2024-03-10: the 09:00 hour on Fri 8 March (EST) is the norm for Mon 11 March 10:00 (EDT)
    a = pd.date_range("2024-03-08 09:00", periods=60, freq="1min", tz=NY)
    c = pd.date_range("2024-03-07 09:00", periods=60, freq="1min", tz=NY)
    e = pd.date_range("2024-03-06 09:00", periods=60, freq="1min", tz=NY)
    f = lambda idx, v: pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": v}, index=idx)  # noqa: E731
    b = pd.concat([f(e, 1.0), f(c, 2.0), f(a, 3.0)])
    assert mf.seasonal(mf.intensity, b, pd.Timestamp("2024-03-11 10:00", tz=NY), days=3) == pytest.approx(120)


# ── flow-based, known answers ──

def test_flow_imbalance():
    f = flow([8, 6, 1], [2, 4, 9])                          # buy 15, sell 15
    assert mf.flow_imbalance(f, end(f), 3, "long") == pytest.approx(0.0)
    g = flow([9, 1, 1, 5], [0, 4, 4, 5])                    # the last three minutes: buy 7, sell 13
    assert mf.flow_imbalance(g, end(g), 3, "long") == pytest.approx(-0.3)
    assert mf.flow_imbalance(g, end(g), 3, "short") == pytest.approx(0.3)


def test_cvd_divergence_long_and_short():
    lows = [100, 99, 98, 99, 100, 99, 97, 98]               # last 4 minutes make a new low (97 < 98)
    px = bars(lows, highs=[x + 1 for x in lows], lows=lows)
    confirm = flow([0] * 8, [1, 1, 1, 0, 0, 5, 5, 5])       # cumulative delta also makes a new low
    diverge = flow([0, 0, 0, 0, 0, 2, 2, 2], [5, 5, 5, 0, 0, 1, 1, 1])   # cumulative delta holds above its old low
    at = end(px)
    assert mf.cvd_divergence(px, confirm, at, "long", recent=4, lookback=8) == -1.0
    assert mf.cvd_divergence(px, diverge, at, "long", recent=4, lookback=8) == 1.0
    flat = bars([100] * 8)
    assert mf.cvd_divergence(flat, confirm, at, "long", recent=4, lookback=8) == 0.0
    highs = [100, 101, 102, 101, 100, 101, 103, 102]        # short: new high at the end
    ps = bars(highs, highs=highs, lows=[x - 1 for x in highs])
    buy_confirm = flow([1, 1, 1, 0, 0, 5, 5, 5], [0] * 8)
    buy_diverge = flow([5, 5, 5, 0, 0, 1, 1, 1], [0, 0, 0, 0, 0, 2, 2, 2])
    assert mf.cvd_divergence(ps, buy_confirm, at, "short", recent=4, lookback=8) == -1.0
    assert mf.cvd_divergence(ps, buy_diverge, at, "short", recent=4, lookback=8) == 1.0


def test_absorbed():
    f = flow([1] * 6, [5] * 6)                              # sellers aggressive throughout
    assert mf.absorbed(bars([100, 100, 101, 100, 100, 100]), f, end(f), "long", mins=6) == 1.0   # price held
    assert mf.absorbed(bars([100, 99, 98, 97, 96, 95]), f, end(f), "long", mins=6) == 0.0         # price fell
    assert mf.absorbed(bars([100, 99, 98, 97, 96, 95]), f, end(f), "short", mins=6) == 0.0        # flow is with a short


def test_vpin():
    f = flow([8] * 6, [2] * 6)                              # every 20-lot bucket: 16 vs 4
    assert mf.vpin(f, end(f), bucket=20, n=3) == pytest.approx(0.6)
    alt = flow([10, 0, 10, 0], [0, 10, 0, 10])
    assert mf.vpin(alt, end(alt), bucket=10, n=4) == pytest.approx(1.0)
    assert mf.vpin(alt, end(alt), bucket=20, n=2) == pytest.approx(0.0)
    assert mf.vpin(alt, end(alt), bucket=5, n=4) == pytest.approx(1.0)       # a minute split over two buckets
    assert math.isnan(mf.vpin(alt, end(alt), bucket=20, n=3))               # not enough volume yet


def test_vpin_bucket_reads_only_earlier_days():
    from datetime import date
    dv = pd.Series([100.0, 200.0, 300.0, 9e9], index=[date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)])
    assert mf.vpin_bucket(dv, pd.Timestamp("2024-01-05 10:00", tz=NY), days=3, per_day=50) == pytest.approx(4.0)


def test_kyle_flow_and_delta_autocorr():
    px = bars([10, 12, 11, 15, 13, 14])
    f = flow([0, 2, 0, 4, 0, 1], [0, 0, 1, 0, 2, 0])        # delta = Δp → λ = 1
    assert mf.kyle_flow(px, f, end(px), 6)[0] == pytest.approx(1.0)
    alt = flow([3, 0, 3, 0, 3, 0], [0, 3, 0, 3, 0, 3])
    assert mf.delta_autocorr(alt, end(alt), 6) < -0.7


def test_large_trade_share():
    idx = pd.date_range(T0, periods=60, freq="1s", tz=NY)
    tr = pd.DataFrame({"size": [1] * 50 + [10] * 10}, index=idx)
    assert mf.large_trade_share(tr, idx[-1] + pd.Timedelta(seconds=1), 5) == pytest.approx(100 / 150)


# ── no look-ahead: scramble everything from `at` on ──

def _rand_bars(n=3000, seed=3):
    rng = np.random.default_rng(seed)
    c = 100 + np.cumsum(rng.normal(0, 0.2, n))
    idx = pd.bdate_range("2024-01-02", periods=n // 300)
    parts, k = [], 0
    for d in idx:                                            # 300 minutes from 08:00 on each weekday
        i = pd.date_range(f"{d.date()} 08:00", periods=300, freq="1min", tz=NY)
        cc = c[k:k + 300]
        parts.append(pd.DataFrame({"open": cc, "high": cc + rng.uniform(0, 0.3, 300), "low": cc - rng.uniform(0, 0.3, 300),
                                   "close": cc, "volume": rng.integers(1, 50, 300).astype(float)}, index=i))
        k += 300
    b = pd.concat(parts)
    b["buy"] = (b.volume * rng.uniform(0, 1, len(b))).round()
    b["sell"] = b.volume - b.buy
    b["delta"] = b.buy - b.sell
    b["spread"] = rng.uniform(0.5, 2, len(b))
    b["size"] = rng.integers(1, 30, len(b)).astype(float)
    return b


BAR_FNS = {
    "realized_vol": lambda b, at: mf.realized_vol(b, at),
    "parkinson_vol": lambda b, at: mf.parkinson_vol(b, at),
    "roll_spread": lambda b, at: mf.roll_spread(b, at),
    "return_autocorr": lambda b, at: mf.return_autocorr(b, at),
    "corwin_schultz": lambda b, at: mf.corwin_schultz(b, at),
    "variance_ratio": lambda b, at: mf.variance_ratio(b, at),
    "amihud": lambda b, at: mf.amihud(b, at),
    "intensity": lambda b, at: mf.intensity(b, at),
    "tick_imbalance": lambda b, at: mf.tick_imbalance(b, at, 60, "short"),
    "kyle_t_bars": lambda b, at: mf.kyle_t_bars(b, at),
    "volume_burst": lambda b, at: mf.volume_burst(b, at),
    "quoted_spread": lambda b, at: mf.quoted_spread(b, b.assign(close=b.close + b.spread), at),
    "spread_fn": lambda b, at: mf.spread_fn(b, at),
    "relative(realized_vol)": lambda b, at: mf.relative(mf.realized_vol, b, at, days=5),
    "relative(amihud)": lambda b, at: mf.relative(mf.amihud, b, at, days=5),
    "relative(intensity)": lambda b, at: mf.relative(mf.intensity, b, at, days=5),
    "seasonal(parkinson)": lambda b, at: mf.seasonal(mf.parkinson_vol, b, at, days=5),
    "flow_imbalance": lambda b, at: mf.flow_imbalance(b, at, 60, "long"),
    "cvd_divergence": lambda b, at: mf.cvd_divergence(b, b, at, "long"),
    "cvd_divergence_short": lambda b, at: mf.cvd_divergence(b, b, at, "short"),
    "absorbed": lambda b, at: mf.absorbed(b, b, at, "long"),
    "vpin": lambda b, at: mf.vpin(b, at, bucket=200, n=20),
    "kyle_flow": lambda b, at: mf.kyle_flow(b, b, at)[1],
    "delta_autocorr": lambda b, at: mf.delta_autocorr(b, at),
    "large_trade_share": lambda b, at: mf.large_trade_share(b, at, 60, 10),
    "vpin_bucket": lambda b, at: mf.vpin_bucket(b.volume.groupby(b.index.date).sum(), at, days=4),
}


@pytest.mark.parametrize("name", sorted(BAR_FNS))
def test_no_look_ahead(name):
    b = _rand_bars()
    fn = BAR_FNS[name]
    for at in (pd.Timestamp("2024-01-12 10:30", tz=NY), pd.Timestamp("2024-01-15 12:59", tz=NY)):
        before = fn(b, at)
        assert before is not None and not math.isnan(before), "the feature must have a value to compare"
        future = b.copy()
        rng = np.random.default_rng(11)
        m = future.index >= at                               # the bar at `at` and everything after it
        for col in future.columns:
            future.loc[m, col] = rng.uniform(1, 1e6, int(m.sum()))
        assert fn(future, at) == before
        assert fn(b[b.index < at], at) == before             # and it needs nothing beyond `at` to exist


# ── statistics ──

def test_bh_and_tercile_helpers():
    assert mf.bh([0.001, 0.04, 0.5, 0.9], q=0.10) == [True, True, False, False]
    assert mf.bh([0.2, 0.3, 0.5], q=0.10) == [False, False, False]
    x = pd.Series([1, 2, 3, 4, 5, 6, 10, 20, 30, 40, 50, 60.0])
    g = pd.Series(["a"] * 6 + ["b"] * 6)
    assert list(mf.terciles(x, g)) == [0, 0, 1, 1, 2, 2] * 2            # thirds inside each dataset
    assert mf.welch([1, 2, 3, 4], [1, 2, 3, 4]) == 0.0
    assert mf.prop_z(30, 60, 30, 60) == 0.0 and mf.prop_z(40, 60, 20, 60) > 3


def test_cluster_z_is_smaller_when_days_repeat():
    rng = np.random.default_rng(5)
    day_fx = rng.normal(size=40)
    days = np.repeat(np.arange(40), 10)
    x = np.repeat(rng.integers(0, 2, 40), 10).astype(float)             # the trait is constant within a day
    y = 0.5 * x + day_fx[days] + rng.normal(0, 0.1, 400)
    naive = mf.welch(y[x == 1], y[x == 0])
    assert abs(mf.cluster_z(y, x, days)[0]) < abs(naive)                # 400 rows, but only 40 independent days


def test_evaluate_finds_a_planted_effect_and_not_a_null():
    rng = np.random.default_rng(9)
    n = 1200
    d = pd.DataFrame({"dataset": rng.choice(["A", "B", "C"], n), "day": rng.integers(0, 300, n).astype(str),
                      "feat": rng.normal(size=n), "noise": rng.normal(size=n), "act_rel": rng.uniform(0.3, 2, n)})
    d["win"] = rng.uniform(size=n) < np.where(d.feat > 0.4, 0.55, 0.30)
    d["r"] = np.where(d.win, 2.0, -1.0)
    e = mf.evaluate(d, "feat")
    assert e["z_win"] > 4 and e["same_win"] == e["cells"] == 3 and e["d_r"] > 0.3
    assert abs(mf.evaluate(d, "noise")["z_win"]) < 3
