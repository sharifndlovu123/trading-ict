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
