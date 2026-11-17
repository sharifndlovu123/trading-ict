"""Post-analysis on hand-built backtest tables with known answers."""

import numpy as np
import pandas as pd

from ict_engine.eval.review import causes, diagnose, gate_value, prepare, report, tips


def table(n_am=120, n_pm=120, am_r=(2.0, -1.0), pm_r=(-1.0, -1.0, 2.0), seed=0):
    """Traded rows: ny_am wins 1 in 2 (+0.5R avg); ny_pm wins 1 in 3 (0R avg)."""
    days = pd.bdate_range("2023-01-02", periods=max(n_am, n_pm))
    rows = []
    for win, n, rs in (("ny_am_kz", n_am, am_r), ("ny_pm_kz", n_pm, pm_r)):
        for i in range(n):
            r = rs[i % len(rs)]
            rows.append(dict(model="2022_model", variant="v", asset="US100", day=days[i], side="long",
                             window=win, weekday=days[i].strftime("%a"), hour=9 if win == "ny_am_kz" else 14,
                             quarter="Q1", bias="bull", outcome="bull_hit" if r > 0 else "bear_hit",
                             status="traded", failed_gate=None, r=r, vote=r > 0, exit="tp1" if r > 0 else "stop",
                             ambiguous=False, tp1_name="5m swing high", poi="swept pdl", liquidity="pdl",
                             liquidity_kind="sweep", shadow_r=r, shadow_vote=r > 0,
                             cf_flip_vote=None, cf_wide_stop_vote=False, cf_tp1_1r_vote=False))
    return pd.DataFrame(rows)


def test_causes_tag_each_counterfactual_and_hindsight():
    row = pd.Series(dict(vote=False, r=-1.0, exit="stop", side="long", outcome="bear_hit", ambiguous=np.bool_(True),
                         cf_flip_vote=np.bool_(True), cf_wide_stop_vote=None, cf_tp1_1r_vote=float("nan")))
    assert causes(row) == ["bias_wrong", "wrong_side", "ambiguous"]
    win = row.copy(); win["vote"], win["r"] = True, 2.0
    assert causes(win) == []
    plain = pd.Series(dict(vote=False, r=-1.0, exit="stop", side="long", outcome="bull_hit", ambiguous=False))
    assert causes(plain) == ["unexplained"]


def test_tip_found_for_stronger_window_and_not_for_noise():
    df = prepare(table())
    found = tips(df, dims=("window",))
    assert {(t["bucket"], round(t["exp_r"], 2)) for t in found} >= {("ny_am_kz", 0.5)}
    assert all(t["z"] > 0 for t in found if t["bucket"] == "ny_am_kz")
    assert tips(prepare(table(n_am=40, n_pm=40)), dims=("window",)) == []          # z≈1.5: not enough evidence


def test_tip_rejected_when_it_flips_between_halves():
    df = table(am_r=(2.0, -1.0), pm_r=(-1.0, -1.0, 2.0))
    late = df.day > df.day.min() + (df.day.max() - df.day.min()) / 2
    df.loc[late & (df.window == "ny_am_kz"), ["r", "vote"]] = [-1.0, False]    # AM edge vanishes late
    df.loc[late & (df.window == "ny_pm_kz"), ["r", "vote"]] = [2.0, True]
    assert tips(prepare(df), dims=("window",)) == []


def test_diagnose_shares_and_gate_value():
    df = table()
    blocked = df.iloc[:5].assign(status="blocked@bias", failed_gate="bias", r=np.nan, vote=None,
                                 shadow_r=2.0, shadow_vote=True)
    df = prepare(pd.concat([df, blocked], ignore_index=True))
    d = diagnose(df, None)
    assert d.losses.iloc[0] == (df.status == "traded").sum() - df[df.status == "traded"].vote.astype(bool).sum()
    assert d.bias_wrong.iloc[0] == 1.0                       # every loser's day ran the other side
    g = gate_value(df).set_index("bucket")
    assert g.loc["blocked@bias (shadow)", "exp_r"] == 2.0 and g.loc["blocked@bias (shadow)", "vs_traded_r"] > 0


def test_report_renders_markdown():
    text = report(table(), "test")
    assert text.startswith("# Review test") and "## Tips" in text and "ny_am_kz" in text


def test_hour_buckets_print_as_plain_labels():
    text = report(table(), "t")
    section = text.split("## By hour")[1]
    assert "| 9 |" in section and "+9.000" not in section


def test_cross_model_names_the_best_family_per_bucket():
    from ict_engine.eval.review import cross_model
    a = table(n_am=60, n_pm=60)                                   # 2022 model: AM +0.5R, PM 0R
    b = table(n_am=60, n_pm=60, am_r=(-1.0,), pm_r=(2.0, -1.0)).assign(model="mmbm")   # MMxM: AM -1R, PM +0.5R
    df = prepare(pd.concat([a, b], ignore_index=True))
    c = cross_model(df, "window", min_n=30).set_index("bucket")
    assert c.loc["ny_am_kz", "best"] == "2022_model" and c.loc["ny_pm_kz", "best"] == "mmxm"
    assert c.loc["ny_pm_kz", "mmxm n"] == 60
    assert cross_model(df, "window", min_n=1000).best.eq("—").all()
    assert "## Cross-model" in report(pd.concat([a, b], ignore_index=True), "x")


def test_invalidated_exit_is_its_own_cause():
    import pandas as pd
    from ict_engine.eval.review import causes
    row = pd.Series({"vote": False, "r": -0.4, "exit": "invalidated", "side": "long", "outcome": "bull_hit",
                     "ambiguous": False})
    assert causes(row) == ["invalidated"]


def test_true_handles_store_nullable_booleans():
    """The trade store keeps votes as pandas nullable booleans: pd.NA must read as 'not true', not crash."""
    import pandas as pd
    from ict_engine.eval.review import _true
    s = pd.Series([True, False, None], dtype="boolean")
    assert [_true(v) for v in s] == [True, False, False]
    assert _true(pd.NA) is False and _true(float("nan")) is False and _true(None) is False
