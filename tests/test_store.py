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
