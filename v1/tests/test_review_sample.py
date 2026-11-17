"""Trade-review facts at scale (research/scripts/review_sample.py): the flat k_* traits come only from the known
section, hindsight goes to cf_* (which the pattern finder never uses as a trait), and the written-review subset holds
the worst losers, typical losers and winners."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from pattern_find import traits as pf_traits  # noqa: E402
from review_sample import pick, traits  # noqa: E402

FACTS = {"side": "short",
         "known": {"side_matches_read": True, "read_kind": "aligned", "risk_adr": 0.2, "rr_tp1": 2.0, "news": None,
                   "momentum_adr_per_candle": 0.1, "range_tf": "4h",
                   "range": {"right_half": True, "ote": False, "fraction_from_low": 0.6},
                   "swept_before": [{"role": "buyside", "label": "Asia high"}],
                   "levels": {"stop": {"beyond_it": False, "at_liquidity": True, "gap_adr": 0.03},
                              "tp1": {"pools_before": ["a", "b"], "just_past_a_pool": []}}},
         "after": {"own": {"mfe_r": 0.4, "mae_r": -1.0, "overnight": False, "why": "stop"},
                   "day_only": {"r": -1.0}, "reach": {"best_r": 3.0}, "stopped_then_target": pd.Timestamp("2024-01-09")}}


def test_traits_split_known_from_hindsight():
    t = traits(FACTS)
    assert t["k_swept_before"] and t["k_swept_our_side"]          # a short wants buyside taken first
    assert t["k_stop_beyond_pool"] is False and t["k_pools_before_tp1"] == 2 and t["k_range_depth"] == 0.6
    assert t["cf_stopped_then_target"] is True and t["cf_best_r"] == 3.0
    long = traits({**FACTS, "side": "long"})
    assert not long["k_swept_our_side"] and long["k_range_depth"] == 0.4


def test_hindsight_columns_never_become_pattern_traits():
    d = pd.DataFrame([traits(FACTS) | {"k_read_kind": k} for k in ["aligned", "mixed"] * 20])
    d["cf_overnight"] = [True, False] * 20
    assert not [c for c in pf_traits(d).columns if c.startswith("cf_")]


def test_pick_has_worst_typical_and_winners():
    d = pd.DataFrame({"r": [-1.0] * 10 + [-3.0, -2.5] + [1.5] * 6,
                      "filled_at": pd.date_range("2023-01-02", periods=18, freq="D", tz="America/New_York")})
    p = pick(d, 6)
    assert len(p) == 6 and {-3.0, -2.5} <= set(p.r) and (p.r > 0).sum() == 2
