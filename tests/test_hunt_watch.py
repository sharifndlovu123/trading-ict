"""The model-free watcher (research/scripts/hunt_watch.py): events fire once, only at what was marked."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
import hunt_watch as hw  # noqa: E402


def doc(last, bars, adr=100.0):
    c = [{"time": 300 * i, "open": o, "high": h, "low": lo, "close": cl} for i, (o, h, lo, cl) in enumerate(bars)]
    return {"assets": {"US100": {"last": last, "adr": adr, "candles": {"5m": c}}}}


OV = {"at": "prep 1", "US100": {"marks": [
    {"kind": "Asia high", "price": 110.0}, {"kind": "FVG", "tf": "1h", "top": 108.0, "bottom": 106.0},
    {"kind": "displacement", "p0": 120.0, "p1": 100.0}]}}


def test_a_level_fires_once_when_price_trades_through_it_and_a_zone_when_entered():
    st = {}
    assert hw.events(doc(104.0, [(103, 104.5, 103, 104), (104, 104.5, 103.5, 104)]), OV, st) == []     # below both
    e = hw.events(doc(106.5, [(104, 104.5, 103.5, 104), (104, 106.8, 104, 106.5)]), OV, st)
    assert len(e) == 1 and "entered 1h FVG 106.0–108.0" in e[0]
    assert hw.events(doc(107.0, [(104, 106.8, 104, 106.5), (106.5, 107.2, 106.4, 107)]), OV, st) == []  # the zone fires once
    e = hw.events(doc(109.5, [(106.5, 107.2, 106.4, 107), (107, 110.2, 107, 109.5)]), OV, st)           # a wick through 110
    assert len(e) == 1 and "traded through Asia high 110.0 (from below)" in e[0]
    assert hw.events(doc(111.0, [(107, 110.2, 107, 109.5), (109.5, 111.2, 109.4, 111)]), OV, st) == []


def test_a_hard_push_is_reported_once_and_a_new_prep_resets_everything():
    st = {}
    bars = [(100, 100.5, 91, 91.5), (91.5, 92, 91, 91.8)]                    # the closed candle fell 8.5 = 0.085 ADR
    e = hw.events(doc(91.8, bars), {"at": "p", "US100": {"marks": []}}, st)
    assert len(e) == 1 and "hard 5m push down" in e[0]
    assert hw.events(doc(91.9, bars), {"at": "p", "US100": {"marks": []}}, st) == []
    quiet = [(100, 100.5, 99, 99.5), (99.5, 100, 99.2, 99.8)]                # 0.5 = 0.005 ADR: nothing
    assert hw.events(doc(99.8, quiet), {"at": "p", "US100": {"marks": []}}, st) == []
    st2 = {}
    hw.events(doc(109.5, [(107, 110.2, 107, 109.5), (109.5, 109.8, 109.2, 109.5)]), OV, st2)             # starts below 110
    hw.events(doc(110.5, [(109.5, 109.8, 109.2, 109.5), (109.5, 110.6, 109.4, 110.5)]), OV, st2)
    again = hw.events(doc(109.0, [(109.5, 110.6, 109.4, 110.5), (110.5, 110.6, 108.9, 109)]), {**OV, "at": "prep 2"}, st2)
    assert any("Asia high" in x for x in again) is False and any("FVG" in x for x in again) is False     # new prep, 109 is between them
    back = hw.events(doc(110.4, [(110.5, 110.6, 108.9, 109), (109, 110.5, 108.9, 110.4)]), {**OV, "at": "prep 2"}, st2)
    assert any("traded through Asia high" in x for x in back)                                           # fires again after the reset
