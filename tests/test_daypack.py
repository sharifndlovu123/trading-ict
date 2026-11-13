"""Day-pack exporter: valid JSON, NY wall-clock times, setups with gates, HTML embedding."""

import json
import math
from datetime import date

import pandas as pd

from ict_engine.models.model_2022 import Params
from ict_engine.viz.daypack import build_daypack, wall, write_html
from tests.test_model_2022 import DAY, bars

NY = "America/New_York"


def test_wall_clock_seconds_show_new_york_time():
    for s in ("2024-01-09 08:47", "2024-07-09 08:47"):            # EST and EDT
        w = wall(pd.Timestamp(s, tz=NY))
        assert (w % 86400) == 8 * 3600 + 47 * 60


def test_pack_is_strict_json_and_complete():
    pack = build_daypack("US100", DAY, Params(), bars=bars())
    text = json.dumps(pack, allow_nan=False)                     # fails on NaN/inf
    back = json.loads(text)
    assert back["asset"] == "US100" and back["day"] == DAY.isoformat()
    assert back["context"]["bias"] == "bull"
    assert back["candles"]["1m"] and len(back["candles"]["1m"][0]) == 5
    assert {"swings", "fvgs", "sweeps", "structure"} <= set(back["events"])
    assert any(w["name"] == "ny_am_kz" for w in back["windows"])


def test_traded_setup_carries_gates_plan_and_result():
    pack = build_daypack("US100", DAY, Params(), bars=bars())
    traded = [s for s in pack["setups"] if s["status"] == "traded"]
    assert traded
    s = traded[0]
    assert [g["name"] for g in s["gates"]][:5] == ["time", "bias", "pricing", "poi", "trigger"]
    assert s["plan"]["stop"] < s["plan"]["entry"] < s["plan"]["tp1"]
    assert s["result"]["vote"] is True
    assert (s["decided"] % 86400) // 60 == 8 * 60 + 47           # 08:47 NY


def test_blocked_setups_keep_their_would_be_plan():
    pack = build_daypack("US100", DAY, Params(windows=("ny_pm_kz",)), bars=bars())
    blocked = [s for s in pack["setups"] if s["status"] == "blocked@time" and "fvg" in s["evidence"]]
    assert blocked and blocked[0]["plan"] is None and blocked[0]["would_plan"] is not None


def test_html_embeds_the_pack(tmp_path):
    pack = build_daypack("US100", DAY, Params(), bars=bars())
    html = write_html(pack, tmp_path / "x.html").read_text()
    assert "/*__DAYPACK__*/null" not in html and '"asset":"US100"' in html
    assert 'integrity="sha384-' in html                           # pinned CDN script
