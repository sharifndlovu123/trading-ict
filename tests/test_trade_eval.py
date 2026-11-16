"""Post-trade facts (research/scripts/trade_eval.py) on hand-built 1m candles with known answers: the trader's own
management, the day-only (flat 16:55 NY) version, excursions, pools taken after the entry, the liquidity run before it,
and the stop / TP checks against known liquidity. Context uses only bars before the entry (no look-ahead)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from trade_eval import flat_time, level_checks, range_place, reach, simulate, swept_before, taken  # noqa: E402

NY = "America/New_York"


def bars(rows, start="2024-01-09 09:30", freq="1min"):
    idx = pd.date_range(start, periods=len(rows), freq=freq, tz=NY)
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)


# a short: entry 100, stop 105 (risk 5), TP1 95 (50 %), TP2 90 (50 %)
SHORT = [(98, 100.5, 97, 100),     # 09:30 fills at 100
         (100, 101, 96, 97),       # 09:31
         (97, 97, 94.5, 95),       # 09:32 TP1 95
         (95, 99, 92, 93),         # 09:33
         (93, 93, 89, 90)]         # 09:34 TP2 90


def test_partials_and_be():
    b = bars(SHORT)
    r = simulate(b, False, 100, 105, [(95, .5), (90, .5)], b.index[0], be=True)
    assert r["filled"] == b.index[0] and r["r"] == pytest.approx(0.5 * 1 + 0.5 * 2)
    assert r["tp_hits"] == 2 and r["why"] == "targets" and r["mfe_r"] == pytest.approx(2.2)
    assert r["mae_r"] == pytest.approx(-0.2) and not r["overnight"]


def test_stop_at_entry_after_tp1():
    rows = SHORT[:3] + [(95, 100.5, 95, 100)]          # back to 100 after TP1 → the rest out at entry
    b = bars(rows)
    r = simulate(b, False, 100, 105, [(95, .5), (90, .5)], b.index[0], be=True)
    assert r["r"] == pytest.approx(0.5) and "stop at entry" in r["events"][-1]


def test_same_bar_stop_and_target_is_the_stop():
    b = bars([(100, 106, 94, 100)])
    r = simulate(b, False, 100, 105, [(95, 1.0)], b.index[0])
    assert r["r"] == -1.0 and r["why"] == "stop"


def test_not_filled_and_bad_levels():
    b = bars([(90, 95, 89, 94)])
    assert simulate(b, False, 100, 105, [(95, 1.0)], b.index[0])["filled"] is None
    with pytest.raises(ValueError):
        simulate(b, False, 100, 95, [(90, 1.0)], b.index[0])          # stop on the wrong side
    with pytest.raises(ValueError):
        simulate(b, False, 100, 105, [(101, 1.0)], b.index[0])        # TP behind the entry


def test_day_only_flat_at_1655_and_overnight_flag():
    rows = [(98, 100.5, 97, 99)] + [(99, 99.5, 98, 98)] * 3        # 16:50–16:53 on Tue
    b = pd.concat([bars(rows, "2024-01-09 16:50"), bars([(98, 98, 89, 90)], "2024-01-10 09:30")])
    held = simulate(b, False, 100, 105, [(90, 1.0)], b.index[0])
    assert held["r"] == pytest.approx(2.0) and held["overnight"]
    assert flat_time(b.index[0]) == pd.Timestamp("2024-01-09 16:55", tz=NY)
    day = simulate(b, False, 100, 105, [(90, 1.0)], b.index[0], flat_at=flat_time(b.index[0]))
    assert day["why"] == "flat" and day["r"] == pytest.approx((100 - 98) / 5) and not day["overnight"]


def test_evening_fill_belongs_to_the_next_trading_day():
    assert flat_time(pd.Timestamp("2024-01-09 19:00", tz=NY)) == pd.Timestamp("2024-01-10 16:55", tz=NY)


def test_reach_and_pools_taken_in_time_order():
    b = bars(SHORT)
    rc = reach(b, False, 100, 5, b.index[0])
    assert rc["best_r"] == pytest.approx(2.2) and rc["worst_r"] == pytest.approx(-0.2)
    items = [{"role": "sellside", "price": 93.5, "label": "PDL", "tf": "1d", "kind": "pdl"},
             {"role": "sellside", "price": 96.5, "label": "Asia low", "tf": "session", "kind": "asia"},
             {"role": "buyside", "price": 102, "label": "1h high", "tf": "1h", "kind": "swing"},
             {"role": "area", "price": 99, "label": "FVG", "tf": "1h", "kind": "fvg"}]
    t = taken(items, b, b.index[0], 100, 5, False)
    assert [x["label"] for x in t] == ["Asia low", "PDL"] and t[0]["r"] == pytest.approx(0.7)


def test_swept_before_uses_only_bars_before_the_entry():
    b = bars([(100, 101, 99, 100), (100, 103, 100, 102), (102, 102, 98, 99), (99, 99, 90, 91)])
    items = [{"role": "buyside", "price": 102.5, "label": "London high"}, {"role": "sellside", "price": 92, "label": "Asia low"}]
    s = swept_before(items, b, b.index[0], b.index[3])                # the 09:33 drop to 90 is after the entry
    assert [x["label"] for x in s] == ["London high"] and s[0]["at"] == b.index[1]


def test_stop_and_tp_against_liquidity():
    items = [{"role": "buyside", "price": 104.95, "label": "EQH"}, {"role": "sellside", "price": 96, "label": "1h low"},
             {"role": "sellside", "price": 91, "label": "PDL"}]
    c = level_checks(items, False, 100, 105, [95], adr=10)
    assert c["stop"]["pool"] == "EQH" and c["stop"]["beyond_it"] and c["stop"]["at_liquidity"]
    assert c["tp1"]["pools_before"] == ["1h low 96.00"]
    c2 = level_checks(items, False, 100, 104, [91.5], adr=10)
    assert not c2["stop"]["beyond_it"]                                # stop under the EQH: the pool will take it
    assert c2["tp1"]["just_past_a_pool"] == []
    c3 = level_checks(items, False, 100, 106, [90.5], adr=10)
    assert c3["tp1"]["just_past_a_pool"] == ["PDL 91.00"]


def test_range_place_premium_for_a_short():
    pin = {"range": {"lo": 100, "hi": 200}}
    r = range_place(pin, False, 170)
    assert r["zone"] == "premium" and r["right_half"] and r["ote"]
    assert not range_place(pin, True, 170)["right_half"]
    assert range_place({"range": None}, False, 150) is None


def test_intraday_pools_use_only_the_session_before_the_entry():
    from trade_eval import intraday_pools
    b = pd.concat([bars([(100, 101, 99, 100)] * 3, "2024-01-08 17:30"),        # previous session (before 18:00)
                   bars([(100, 103, 98, 101), (101, 102, 97.5, 100)], "2024-01-08 18:05"),
                   bars([(100, 100, 90, 91)], "2024-01-09 09:31")])         # after the entry
    p = {x["label"]: x["price"] for x in intraday_pools(b, pd.Timestamp("2024-01-09 09:30", tz=NY))}
    assert p["session so far high"] == 103 and p["session so far low"] == 97.5


def test_activity_quiet_vs_busy_against_the_same_clock_window():
    from trade_eval import activity
    days = pd.bdate_range("2024-01-01", periods=12, tz=NY)
    parts = []
    for i, d in enumerate(days):
        idx = pd.date_range(d + pd.Timedelta(hours=9), periods=60, freq="1min")
        hi = 110 if i == len(days) - 1 else 102                       # the last day's 09:00–10:00 range is 10, before it 2
        parts.append(pd.DataFrame({"open": 100.0, "high": hi, "low": 100.0, "close": 101.0}, index=idx))
    b = pd.concat(parts)
    busy = activity(b, days[-1] + pd.Timedelta(hours=10), adr=20)
    assert busy["range_adr"] == 0.5 and busy["relative"] == 5.0 and busy["state"] == "busy"
    normal = activity(b, days[-2] + pd.Timedelta(hours=10), adr=20)   # uses only the days before it
    assert normal["relative"] == 1.0 and normal["state"] == "normal"
    quiet = activity(b.assign(high=lambda x: x.high.where(x.index.normalize() != days[-1], 100.5)),
                     days[-1] + pd.Timedelta(hours=10), adr=20)
    assert quiet["state"] == "quiet"


def test_turn_point_names_the_known_level_where_price_turned():
    from trade_eval import turn_point
    # a short from 100, stop 105: price runs to 107 (beyond the stop) first, then falls to 90
    b = bars([(100, 101, 99, 100), (100, 107, 100, 106), (106, 106, 95, 96), (96, 96, 90, 91)])
    items = [{"role": "area", "top": 108.0, "bottom": 106.5, "label": "4h bearish FVG", "kind": "fvg"},
             {"role": "buyside", "price": 107.2, "label": "PDH", "kind": "pdh"},
             {"role": "sellside", "price": 80.0, "label": "PWL", "kind": "pwl"}]
    t = turn_point(b, False, 100, 105, b.index[0], items, adr=10)
    assert t["price"] == 107 and t["beyond_stop"] and t["beyond_stop_adr"] == 0.2 and t["depth_r"] == 1.4
    assert t["at_known_level"] and t["levels"] == ["4h bearish FVG 106.50–108.00", "PDH 107.20"]
    assert t["run_after_r"] == pytest.approx(17 / 5)
    inside = turn_point(bars(SHORT), False, 100, 105, bars(SHORT).index[0], [], adr=10)
    assert not inside["beyond_stop"] and not inside["at_known_level"]


def test_pick_balanced_is_half_winners_half_losers():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
    from review_sample import pick_balanced
    mk = lambda k: pd.DataFrame({"r": [1.5] * 20 + [-1.0] * 30,
                                 "filled_at": pd.date_range(f"2023-0{k}-01", periods=50, freq="D", tz=NY)})
    p = pick_balanced([mk(1), mk(2), mk(3)], 15)
    assert len(p) == 30 and (p.r > 0).sum() == 15


def test_order_flow_imbalance_is_aligned_with_the_trade_and_uses_only_the_past():
    from trade_eval import order_flow
    at = pd.Timestamp("2024-03-05 10:00", tz=NY)
    idx = pd.date_range(at - pd.Timedelta(minutes=60), periods=90, freq="1min")     # 60 min before + 30 after
    f = pd.DataFrame({"buy": 30.0, "sell": 10.0}, index=idx)
    f.loc[f.index >= at - pd.Timedelta(minutes=5), ["buy", "sell"]] = [10.0, 30.0]    # the last 5 min: sellers
    f.loc[f.index >= at, ["buy", "sell"]] = [1000.0, 0.0]                             # the future: must be ignored
    f["volume"], f["delta"] = f.buy + f.sell, f.buy - f.sell
    long = order_flow("US100", at, True, flow=f)
    assert long["imb_5m"] == -0.5 and long["imb_60m"] == pytest.approx((55 * 20 - 5 * 20) / (60 * 40), abs=0.001)
    assert long["with_trade_60m"] and not long["with_trade_5m"]
    short = order_flow("US100", at, False, flow=f)
    assert short["imb_5m"] == 0.5 and not short["with_trade_60m"]
    assert order_flow("XAUUSD", at, True) is None                                      # no futures flow on disk


def test_turn_uses_only_the_trades_own_day():
    """Trade reviews 2026-11-16: the 2-day turn line picked a later swing on about a third of the sheets. The turn
    is now read from the fill's trading day only (to 16:55 NY)."""
    from trade_eval import flat_time, turn_point
    day1 = bars([(100, 101, 99, 100), (100, 103, 100, 102), (102, 102, 96, 97)], "2024-01-09 10:00")     # short: high 103
    day2 = bars([(97, 120, 97, 119), (119, 119, 80, 81)], "2024-01-10 10:00")                             # next day: 120, then 80
    both = pd.concat([day1, day2])
    fill = day1.index[0]
    own = turn_point(both[both.index < flat_time(fill)], False, 100, 105, fill, [], adr=10)
    assert own["price"] == 103 and not own["beyond_stop"]
    wide = turn_point(both, False, 100, 105, fill, [], adr=10)
    assert wide["price"] == 120                                                                           # the old 2-day reading
