"""Variant comparison: in-sample / out-of-sample split and deltas on hand-built trades."""

from datetime import date

import pandas as pd

from ict_engine.eval.variants import SETS, VARIANTS, compare, render, split_day


def trades(name, early_r, late_r, n=50):
    days = list(pd.date_range("2023-01-02", periods=n, freq="D"))
    rs = [early_r] * int(n * 0.7) + [late_r] * (n - int(n * 0.7))
    return pd.DataFrame({"variant_name": name, "day": days, "status": "traded",
                         "r": [r + (0.1 if i % 2 else -0.1) for i, r in enumerate(rs)],
                         "vote": [r > 0 for r in rs]})


def test_split_is_seventy_thirty_by_date():
    cut = split_day(date(2023, 1, 1), date(2023, 1, 11), 0.3)
    assert cut == pd.Timestamp("2023-01-08")


def test_oos_delta_judges_the_late_part_only():
    df = pd.concat([trades("baseline", 0.5, -0.5), trades("better", -0.5, 0.5),
                    pd.DataFrame({"variant_name": ["better"], "day": [pd.Timestamp("2023-01-03")],
                                  "status": ["blocked@time"], "r": [None], "vote": [None]})], ignore_index=True)
    cut = split_day(date(2023, 1, 2), date(2023, 2, 20), 0.3)
    c = compare(df, cut).set_index("variant")
    assert c.loc["better", "is_exp_r"] < c.loc["baseline", "is_exp_r"]         # looks worse in-sample
    assert c.loc["better", "oos_delta"] > 0.9 and c.loc["better", "oos_z"] > 2   # but wins out-of-sample
    assert c.loc["baseline", "oos_delta"] == 0
    assert c.loc["better", "is_n"] + c.loc["better", "oos_n"] == 50              # blocked rows not counted
    assert "| better |" in render(c.reset_index(), cut, "t")


def test_every_variant_set_has_baseline_and_distinct_labels():
    assert SETS["2022_model"] is VARIANTS
    for name, variants in SETS.items():
        assert "baseline" in variants, name
        labels = [p.variant for p in variants.values()]
        assert len(set(labels)) == len(labels), name


def test_pd_return_variant_set_has_a_default_baseline_and_documented_windows_only():
    from ict_engine.concepts.clock import WINDOWS
    from ict_engine.eval.variants import SETS
    from ict_engine.models import model_pd_return as pr
    s = SETS["pd_return"]
    assert s["baseline"] == pr.Params()
    names = {w.name for w in WINDOWS}
    assert all(set(p.windows) <= names for p in s.values())
