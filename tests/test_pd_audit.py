"""PD-array audit (research/scripts/pd_audit.py) on hand-built inputs with known answers: the review moment is read
from the save, a drawn zone matches only an engine array of the same kind that formed near where it was anchored (the
same price from a much older candle is "same price, other candle"), and the map check flags zero-width slivers and
areas from the future."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from pd_audit import check_map, iou, judge, moment_of  # noqa: E402

NY = "America/New_York"
T0 = pd.Timestamp("2023-03-10 10:00", tz=NY)


def arr(kind="fvg", tf="4h", top=110, bottom=100, origin=T0):
    return {"tf": tf, "kind": kind, "dir": "bull", "top": top, "bottom": bottom, "origin": origin, "known": origin}


def mark(kind="fvg", tf="4h", top=110, bottom=100, t0=T0):
    return {"kind": kind, "tf": tf, "top": top, "bottom": bottom, "t0": t0}


def test_iou():
    assert iou(110, 100, 110, 100) == 1.0 and iou(110, 100, 120, 110) == 0.0
    assert iou(110, 100, 115, 105) == pytest.approx(5 / 15)


def test_moment_from_watch_point_or_id():
    assert moment_of({"id": "plan-US500-20220610-0830"}) == pd.Timestamp("2022-06-10 08:30", tz=NY)
    assert moment_of({"id": "re-mmxm-US500-20230215-0339"}) == pd.Timestamp("2023-02-15 03:39", tz=NY)
    w = int(pd.Timestamp("2022-06-10 11:00").timestamp())          # wall seconds (NY wall time as UTC epoch)
    assert moment_of({"id": "plan-US500-20220610-0830", "watched_to": w}) == pd.Timestamp("2022-06-10 11:00", tz=NY)


def test_match_partial_other_tf_other_kind():
    assert judge(mark(), [arr()], [])["verdict"] == "match"
    assert judge(mark(), [arr(top=118, bottom=104)], [])["verdict"] == "partial"           # IoU 6/18 = 0.33
    assert judge(mark(), [arr(tf="1h")], [])["verdict"] == "other TF"
    assert judge(mark(kind="breaker"), [arr(kind="ob")], [])["verdict"] == "other kind"
    assert judge(mark(), [], [])["verdict"] == "missing"


def test_same_price_from_an_old_candle_is_not_a_match():
    old = arr(origin=T0 - pd.Timedelta(days=200))
    assert judge(mark(), [old], [])["verdict"] == "same price, other candle"
    assert judge(mark(t0=None), [old], [])["verdict"] == "match"                            # no anchor: price only


def test_on_map_flag():
    assert judge(mark(), [arr()], [{"top": 109, "bottom": 101}])["on_map"]
    assert not judge(mark(), [arr()], [{"top": 130, "bottom": 120}])["on_map"]


def test_map_check_flags_slivers_and_the_future():
    at = pd.Timestamp("2023-03-10 12:00", tz=NY)
    items = [{"role": "area", "kind": "vi", "tf": "1h", "top": 5.0, "bottom": 5.0, "label": "1h VI", "formed": "2023-03-10 09:00"},
             {"role": "area", "kind": "nwog", "tf": "1d", "top": 9.0, "bottom": 8.0, "label": "NWOG", "formed": "2023-03-10 13:00"}]
    p = check_map(None, at, items, {})
    assert any("zero width" in x for x in p) and any("after the moment" in x for x in p)
