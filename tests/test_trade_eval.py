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
