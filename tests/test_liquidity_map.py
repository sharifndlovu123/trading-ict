"""Liquidity map (concept layer) on hand-built candles with known answers: an untaken daily swing high above price is
buyside liquidity, a taken one is not; every listed level is untaken and on the right side of price; areas are
unfilled; one item per price (confluence goes to ``also``); nothing after ``as_of`` is read."""

import pandas as pd
import pytest

from ict_engine.concepts.liquidity_map import build
from tests.test_model_2022 import path_bars

NY = "America/New_York"


def bars(retake=False):
    """Up to 120 on Jan 10, down to 100 by Jan 12, then 100–110 swings (to 121 on Jan 24 when ``retake``)."""
    pts = [("2024-01-02 00:00", 100), ("2024-01-10 12:00", 120), ("2024-01-12 12:00", 100)]
    t = pd.Timestamp("2024-01-13 12:00")
    hi = True
    while t < pd.Timestamp("2024-02-01"):
        pts.append((str(t), 110 if hi else 102))
        hi = not hi
        t += pd.Timedelta(hours=30)
    if retake:
        pts.insert(next(i for i, p in enumerate(pts) if pd.Timestamp(p[0]) > pd.Timestamp("2024-01-24")), ("2024-01-24 06:00", 121))
    return path_bars(sorted(pts), "2024-01-02 00:00", "2024-02-01 00:00")


AS_OF = pd.Timestamp("2024-01-30 08:30", tz=NY)


def test_untaken_daily_swing_high_is_buyside_above_and_a_taken_one_is_not():
    m = build(bars(), AS_OF, max_adr=50)
    top = [it for it in m["items"] if it["role"] == "buyside" and it["price"] > 119]
    assert top and top[0]["where"] == "above" and abs(top[0]["price"] - 120.02) < 0.05
    assert top[0]["tf"] == "1d" or any(a.startswith("1d ") for a in top[0]["also"])
    m2 = build(bars(retake=True), AS_OF, max_adr=50)
    assert not [it for it in m2["items"] if it["role"] == "buyside" and 119 < it["price"] < 120.1]


def test_every_item_is_untaken_on_its_side_and_areas_unfilled():
    b = bars()
    m = build(b, AS_OF, max_adr=50)
    seen = b[b.index < AS_OF]
    assert m["items"] and len({it["id"] for it in m["items"]}) == len(m["items"])
    for it in m["items"]:
        if it["role"] == "buyside":
            assert it["where"] == "above" and it["price"] > m["price"]
        elif it["role"] == "sellside":
            assert it["where"] == "below" and it["price"] < m["price"]
        else:
            assert it["top"] >= it["bottom"]
    prices = [(it["role"], round(it["price"], 1)) for it in m["items"] if it["role"] != "area"]
    assert len(prices) == len(set(prices))                       # confluent levels merged


def test_no_lookahead():
    b = bars()
    assert build(b, AS_OF) == build(b[b.index < AS_OF], AS_OF)


def test_key_points_name_existing_items():
    m = build(bars(), AS_OF, max_adr=50)
    ids = {it["id"] for it in m["items"]}
    for tf, d in m["key"]["nearest"].items():
        for v in d.values():
            assert v is None or v in ids
    with pytest.raises(ValueError):
        build(bars(), pd.Timestamp("2023-01-01 08:30", tz=NY))


def test_every_item_knows_when_it_formed_and_the_level_was_there():
    """The viewer draws each level from the candle that made it; context levels (PDH, PWH …) included."""
    b = bars()
    m = build(b, AS_OF, max_adr=50)
    for it in m["items"]:
        assert it["formed"], it["id"]
        t = pd.Timestamp(it["formed"])
        assert t < AS_OF, it["id"]
        if it["kind"] in ("pdh", "pdl", "pwh", "pwl", "pmh", "pml", "asia_high", "asia_low", "london_high", "london_low"):
            bar = b.loc[t]                                          # context levels: the 1m bar that made them
            assert (bar.high >= it["price"] - 0.01) if it["role"] == "buyside" else (bar.low <= it["price"] + 0.01), it["id"]


def _tf_bars(closes, start="2024-01-01"):
    idx = pd.date_range(start, periods=len(closes), freq="D", tz=NY)
    return pd.DataFrame({"close": closes, "close_ts": idx + pd.Timedelta(hours=17)}, index=idx)


def test_htf_gap_judged_on_its_own_closes_wick_keeps_it_close_through_inverts_close_back_retires():
    from ict_engine.concepts.events import Event
    from ict_engine.concepts.liquidity_map import _htf_gap
    t = pd.Timestamp("2024-01-01 17:00", tz=NY)
    g = Event("fvg", "1d", "bull", t, t, top=110.0, bottom=100.0)
    end = pd.Timestamp("2024-02-01", tz=NY)
    assert _htf_gap(g, _tf_bars([120, 115, 105, 112]), end) == "fvg"           # closes inside: partly filled, still there
    assert _htf_gap(g, _tf_bars([120, 105, 95, 98]), end) == "ifvg"            # a daily close below the bottom: IFVG
    assert _htf_gap(g, _tf_bars([120, 95, 105, 111]), end) is None             # ... then a close back above the top
    assert _htf_gap(g, _tf_bars([120, 95]), pd.Timestamp("2024-01-02 12:00", tz=NY)) == "fvg"   # no look-ahead
    vi = Event("vi", "1d", "bull", t, t, top=110.0, bottom=100.0)
    assert _htf_gap(vi, _tf_bars([120, 95]), end) is None


def test_topdown_names_existing_items_on_both_sides():
    m = build(bars(), AS_OF, max_adr=50)
    ids = {it["id"]: it for it in m["items"]}
    td = m["key"]["topdown"]
    assert set(td) == {"1w", "1d"}
    for tf, d in td.items():
        assert all(i in ids for v in d.values() for i in v)
        assert all(ids[i]["role"] == "buyside" and ids[i]["where"] == "above" for i in d["buyside"])
        assert all(ids[i]["role"] == "sellside" and ids[i]["where"] == "below" for i in d["sellside"])
        assert all(ids[i]["role"] == "area" for i in d["areas"])


def test_no_zero_width_areas_on_real_data():
    """PD-array audit 2026-11-16: 1h/4h volume imbalances a fraction of a point wide showed up as areas with
    top == bottom after rounding (slivers, not areas) and could take one of the 3 gap slots per side."""
    from datetime import date
    from ict_engine.data import dukascopy
    try:
        b = dukascopy.load("US500", date(2022, 4, 1), date(2022, 10, 1))
    except Exception:
        pytest.skip("US500 2022 data not fetched")
    for at in ("2022-05-28 00:30", "2022-09-29 04:14"):
        m = build(b, pd.Timestamp(at, tz=NY))
        assert not [it for it in m["items"] if it["role"] == "area" and it["top"] <= it["bottom"]], at


def test_no_area_from_a_candle_that_is_still_forming():
    """Trade review 2026-11-16: at 10:17 the map listed a 1h FVG whose third candle was the 10:00 hour, 17 minutes
    old, and a 4h FVG whose third candle had just started. An FVG exists only once its third candle has closed (a
    volume imbalance once its second has); a forming candle can still fill the gap."""
    from datetime import date
    from ict_engine.data import dukascopy
    try:
        b = dukascopy.load("US500", date(2021, 10, 1), date(2022, 2, 1))
    except Exception:
        pytest.skip("US500 2021-10 → 2022-01 data not fetched")
    at = pd.Timestamp("2022-01-03 10:17", tz=NY)
    span = {"1h": pd.Timedelta(hours=1), "4h": pd.Timedelta(hours=4)}
    areas = [it for it in build(b, at)["items"] if it["role"] == "area" and it["tf"] in span]
    assert areas
    for it in areas:
        formed = pd.Timestamp(it["formed"])
        candles_after = 1 if it["kind"] in ("fvg", "ifvg") else 0          # FVG: formed = its middle candle
        assert formed + (candles_after + 1) * span[it["tf"]] <= at, (it["label"], it["formed"])
    assert not [it for it in areas if it["tf"] == "1h" and it["kind"] == "fvg" and it["formed"].startswith("2022-01-03 09:00")]
    assert not [it for it in areas if it["top"] - it["bottom"] < 0.005]      # no zero-width slivers either
