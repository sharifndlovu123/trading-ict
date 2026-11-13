"""Trade store: one clean, typed, labelled table of every setup from every run."""

import pandas as pd
import pytest

from ict_engine.eval import store

NY = "America/New_York"


def table(n=4, model="mmbm", asset="US100", r=(1.0, -1.0, 2.0, -1.0)):
    days = pd.date_range("2024-07-01", periods=n, freq="D")
    return pd.DataFrame({
        "model": model, "variant": "v1", "asset": asset, "style": "day", "day": days, "side": "long",
        "decided_at": [pd.Timestamp(d).tz_localize(NY) + pd.Timedelta(hours=8) for d in days],
        "weekday": [d.strftime("%a") for d in days], "hour": 8, "window": "ny_premarket",
        "status": ["traded"] * n, "r": list(r)[:n], "vote": [x > 0 for x in list(r)[:n]],
        "arm": [None] * n, "ambiguous": [False, None, False, None][:n], "news": "no high-impact news",
    })


@pytest.fixture
def root(tmp_path):
    return tmp_path / "trades"


def meta(**kw):
    return {"start": "2024-07-01", "end": "2024-07-04", "commit": "abc1234", "extras": True, **kw}


def test_add_and_load_round_trip_with_run_labels(root):
    rid = store.add_run(table(), root=root, **meta())
    df = store.load(root=root)
    assert len(df) == 4 and set(df.run_id) == {rid}
    assert (df.commit == "abc1234").all() and (df.period_start == pd.Timestamp("2024-07-01")).all()


def test_types_are_normalised(root):
    store.add_run(table(), root=root, **meta())
    df = store.load(root=root)
    assert str(df.vote.dtype) == "boolean" and str(df.ambiguous.dtype) == "boolean"
    assert df.arm.dtype == float and df.family.iloc[0] == "mmxm"


def test_same_run_twice_is_refused_unless_replaced(root):
    store.add_run(table(), root=root, **meta())
    with pytest.raises(FileExistsError):
        store.add_run(table(), root=root, **meta())
    store.add_run(table(r=(1, 1, 1, 1)), root=root, replace=True, **meta())
    assert store.load(root=root).r.sum() == 4


def test_missing_required_columns_are_refused(root):
    with pytest.raises(ValueError, match="missing"):
        store.add_run(table().drop(columns=["window"]), root=root, **meta())


def test_mixed_assets_or_models_in_one_run_are_refused(root):
    mixed = pd.concat([table(), table(asset="US500")])
    with pytest.raises(ValueError, match="one asset"):
        store.add_run(mixed, root=root, **meta())


def test_load_filters(root):
    store.add_run(table(), root=root, **meta())
    store.add_run(table(asset="XAUUSD"), root=root, **meta())
    assert set(store.load(root=root, asset="XAUUSD").asset) == {"XAUUSD"}
    assert len(store.load(root=root, traded_only=True)) == 8


def test_leaderboard_per_bucket_with_min_n(root):
    store.add_run(table(), root=root, **meta())
    store.add_run(table(asset="XAUUSD", r=(2.0, 2.0, -1.0, 2.0)), root=root, **meta())
    lb = store.leaderboard(store.load(root=root), by=["family", "asset"], min_n=1)
    gold = lb.set_index("asset").loc["XAUUSD"]
    assert gold.n == 4 and gold.exp_r == pytest.approx(1.25) and gold.win == pytest.approx(0.75)
    assert lb.iloc[0].asset == "XAUUSD"                                  # sorted best first
    assert store.leaderboard(store.load(root=root), by=["asset"], min_n=5).empty


def test_leaderboard_clustered_se_widens_when_same_day_trades_move_together():
    """Trades on the same day share the day's tape, so they are not independent. se_cl (clustered by day)
    must equal the naive se when every day has one trade, and be wider when same-day results are copies."""
    import math
    import pandas as pd
    from ict_engine.eval.store import clustered_se, leaderboard
    r = pd.Series([1.0, -1.0, 2.0, -1.0])
    one_per_day = pd.Series(pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]))
    assert clustered_se(r, one_per_day) == pytest.approx(r.std(ddof=1) / math.sqrt(4))
    # hand check, 2 days × 2 identical trades: mean 0.5, residual sums 2×0.5 and 2×(−0.5)... use (1,1) and (−1,−1)
    r2 = pd.Series([1.0, 1.0, -1.0, -1.0])
    two_days = pd.Series(pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"]))
    # S_g = 2, −2 → var = G/(G−1) · ΣS²/n² = 2 · 8/16 = 1 → se 1.0 (naive: 1.1547/2 = 0.577)
    assert clustered_se(r2, two_days) == pytest.approx(1.0)
    df = pd.DataFrame({"status": "traded", "r": r2, "vote": r2 > 0, "day": two_days, "family": "x"})
    row = leaderboard(df, ["family"], min_n=1).iloc[0]
    assert row.se_cl == pytest.approx(1.0) and row.se_cl > row.se and row.z_cl == pytest.approx(0.0)


def test_cost_basis_separates_runs(root):
    """A futures-costed run of the same model/asset/period/commit is a different run, not a duplicate."""
    import pandas as pd
    from ict_engine.eval import store as st
    base = pd.DataFrame({c: ["x"] for c in st.REQUIRED}).assign(model="2022_model", asset="US100", status="traded",
                                                                  r=0.5, vote=True, day="2024-01-02")
    a = st.add_run(base, "2024-01-01", "2024-01-31", commit="abc", root=root)
    b = st.add_run(base.assign(cost_basis="futures"), "2024-01-01", "2024-01-31", commit="abc", root=root)
    assert a != b
    got = st.load(root=root, cost_basis="futures")
    assert set(got.run_id) == {b}
    assert set(st.load(root=root, cost_basis="cfd").run_id) >= {a}
