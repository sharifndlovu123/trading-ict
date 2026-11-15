"""2022 model stop types (2022 Content p.5, framework §8): swing point / order block / imbalance end, on hand-built
1m candles with known answers. Default stays ``swing`` (unchanged results)."""
import pandas as pd
import pytest

from ict_engine.concepts.events import fvgs
from ict_engine.models.model_2022 import Params, stop_anchor

NY = "America/New_York"
#        open high low close
ROWS = [(105, 106, 100, 101),   # 0 grab: the swept low 100 (manipulation extreme)
        (101, 104, 101.5, 103),   # 1 up
        (103, 103.5, 102, 102.2), # 2 last down-close before the displacement: the OB, low 102
        (102.2, 110, 102.1, 109), # 3 displacement candle
        (109, 112, 106, 111)]     # 4 bull FVG 103.5–106 (bar2 high → bar4 low)


def frame():
    idx = pd.date_range("2024-01-09 09:30", periods=len(ROWS), freq="1min", tz=NY)
    df = pd.DataFrame(ROWS, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    df["close_ts"] = idx + pd.Timedelta(minutes=1)
    return df


def test_three_stop_types_for_a_long():
    df = frame()
    g = [x for x in fvgs(df, "1m") if x.direction == "bull"][-1]
    assert (g.bottom, g.top) == (103.5, 106) and g.origin_ts == df.index[3]
    since = df.index[0]
    assert stop_anchor(df, g, True, "swing", 100.0, since) == 100.0
    assert stop_anchor(df, g, True, "ob", 100.0, since) == 102.0          # the last down-close candle's low
    assert stop_anchor(df, g, True, "imbalance", 100.0, since) == 103.5   # the FVG's far edge


def test_ob_stop_falls_back_to_the_swing_without_an_opposite_candle():
    df = frame()
    g = [x for x in fvgs(df, "1m") if x.direction == "bull"][-1]
    assert stop_anchor(df, g, True, "ob", 100.0, df.index[3]) == 100.0   # nothing between the grab and the FVG


def test_short_mirrors_and_bad_type_raises():
    df = frame()
    inv = df.copy()
    inv[["open", "high", "low", "close"]] = 300 - df[["open", "low", "high", "close"]].to_numpy()
    g = [x for x in fvgs(inv, "1m") if x.direction == "bear"][-1]
    assert stop_anchor(inv, g, False, "ob", 200.0, inv.index[0]) == 198.0
    assert stop_anchor(inv, g, False, "imbalance", 200.0, inv.index[0]) == 196.5
    with pytest.raises(ValueError):
        stop_anchor(df, g, True, "nope", 100.0, df.index[0])


def test_default_is_swing_and_label_marks_other_types():
    assert Params().stop_type == "swing"
    assert "stop_ob" in Params(stop_type="ob").variant and "stop_" not in Params().variant
