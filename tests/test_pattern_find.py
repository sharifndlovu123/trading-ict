"""Pattern finder (research/scripts/pattern_find.py) on hand-built trade tables with known answers: a real edge is
labelled DO MORE / DO LESS, noise and a one-outlier effect are not, outcome columns are never traits, and the
false-discovery correction and Wilson range behave."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from pattern_find import bh, compare, traits, wilson  # noqa: E402


def table(n=600, seed=1):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"asset": rng.choice(["US100", "US500", "US30"], n),
                      "poi": rng.choice(["ob", "fvg"], n),
                      "window": rng.choice(["london", "ny_am", "ny_pm"], n),
                      "noise": rng.choice(["a", "b"], n),
                      "when": pd.date_range("2022-01-03", periods=n, freq="D")})
    # OB wins 60 %, FVG 35 %: +1.5 R or −1 R
    p = np.where(d.poi == "ob", 0.60, 0.35)
    d["win"] = rng.random(n) < p
    d["R"] = np.where(d.win, 1.5, -1.0)
    d["r"] = d["R"]                                            # an outcome column: must never become a trait
    return d


def test_a_real_edge_is_do_more_and_its_mirror_do_less():
    d = table()
    out = compare(d, traits(d))
    lab = dict(zip(out.trait, out.label))
    assert lab["poi=ob"] == "DO MORE" and lab["poi=fvg"] == "DO LESS"
    assert lab.get("noise=a", "") == "" and lab.get("noise=b", "") == ""


def test_outcome_columns_are_never_traits():
    d = table()
    assert set(traits(d).columns) == {"asset", "poi", "window", "noise"}


def test_one_outlier_is_not_a_pattern():
    d = table(seed=3)
    d.loc[(d.noise == "a").idxmax(), "R"] = 400.0             # one +400 R trade in noise=a
    out = compare(d, traits(d))
    row = out[out.trait == "noise=a"].iloc[0]
    assert row.label not in ("DO MORE", "LEAN MORE")           # capped at 10 R, the effect is gone


def test_pairs_and_min_n():
    d = table()
    out = compare(d, traits(d), pairs=True, min_n=30)
    assert (out.k == 2).any() and out.n.min() >= 30


def test_wilson_and_bh():
    lo, hi = wilson(50, 100)
    assert lo == pytest.approx(0.404, abs=0.002) and hi == pytest.approx(0.596, abs=0.002)
    assert bh([0.001, 0.02, 0.04, 0.5], q=0.10) == [True, True, True, False]
    assert bh([0.2, 0.5], q=0.10) == [False, False]


def test_win_target_uses_the_win_rate():
    d = table()
    out = compare(d, traits(d), target="win")
    row = out[out.trait == "poi=ob"].iloc[0]
    assert row.label == "DO MORE" and row.diff_r == pytest.approx(row.win - row.rest_win)
