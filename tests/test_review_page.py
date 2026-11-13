"""Review page on hand-built backtest tables — no real data, no day-pack export."""

import json
import re

import pandas as pd

from ict_engine.viz import daypack, review_page as rp


def table(model="2022_model", n=60, rs=(2.0, -1.0, -1.0), asset="US100", window="ny_am_kz"):
    days = pd.bdate_range("2023-01-02", periods=n)
    rows = []
    for i, d in enumerate(days):
        r = rs[i % len(rs)]
        t = pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=40)
        rows.append(dict(model=model, variant="v", asset=asset, day=d, side="long" if i % 2 else "short",
                         decided_at=t, filled_at=t + pd.Timedelta(minutes=2), window=window,
                         weekday=d.strftime("%a"), hour=9, quarter="Q1", bias="bull",
                         outcome="bull_hit" if (r > 0) == bool(i % 2) else "bear_hit",
                         status="traded", failed_gate=None, r=r, vote=r > 0, exit="tp1" if r > 0 else "stop",
                         ambiguous=False, tp1_name="5m swing high", poi="swept pdl", liquidity="pdl",
                         liquidity_kind="sweep", shadow_r=r, shadow_vote=r > 0,
                         cf_flip_vote=i % 3 == 1, cf_wide_stop_vote=False, cf_tp1_1r_vote=None))
    df = pd.DataFrame(rows)
    blocked = df.iloc[:4].assign(status="blocked@bias", failed_gate="bias", r=float("nan"), vote=None,
                                 shadow_r=2.0, shadow_vote=True)
    return pd.concat([df, blocked], ignore_index=True)


def both():
    return pd.concat([table(), table("mmbm", rs=(-1.0, 2.0), asset="US500"),
                      table("mmsm", n=30, rs=(-1.0,), window="london_kz")], ignore_index=True)


def embedded(page: str):
    m = re.search(r'<script type="application/json" id="review-data">(.*?)</script>', page, re.S)
    return json.loads(m.group(1), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))


def test_page_renders_all_sections_and_valid_json():
    df = both()
    page = rp.render(rp.build(df))
    for sid in ("overview", "tips", "wrong", "gates", "cross", "buckets"):
        assert f'<section id="{sid}">' in page
    assert "2022 model" in page and "MMxM" in page and 'href="index.html"' in page
    d = embedded(page)
    assert set(d["families"]) == {"2022_model", "mmxm"}
    assert d["overview"]["2022_model"]["n"] == 60 and d["overview"]["mmxm"]["n"] == 90
    assert {r["bucket"] for r in d["gates"]["2022_model"]} >= {"traded (passed all)", "blocked@bias (shadow)"}
    assert d["cross"]["window"] and "<script" not in page.split("</main>")[0].lower()


def test_nan_becomes_null_and_json_is_strict():
    d = rp.build(table(n=1))                                    # one trade → exp_se is NaN
    assert d["overview"]["2022_model"]["exp_se"] is None
    json.dumps(d, allow_nan=False)


def test_examples_spread_capped_and_link_day_pack_names():
    ex = rp.examples(rv_prepare(both()))
    for fam in ex.values():
        for items in fam.values():
            assert 1 <= len(items) <= rp.MAX_EXAMPLES
            assert all(e["r"] < 0 and e["href"] == f"{e['asset']}-{e['day']}.html" for e in items)
            assert len({(e["asset"], e["day"]) for e in items}) == len(items)
    assert "wrong_side" in ex["2022_model"]


def rv_prepare(df):
    from ict_engine.eval.review import prepare
    return prepare(df)


def test_ensure_daypacks_exports_missing_skips_existing_and_respects_cap(tmp_path, monkeypatch):
    ex = rp.examples(rv_prepare(both()))
    names = [e["href"] for f in ex.values() for items in f.values() for e in items]
    existing = names[0]
    (tmp_path / existing).write_text("x")
    calls = []

    def fake_export(asset, day, relaxed):
        calls.append((asset, day, relaxed))
        (tmp_path / rp.pack_name(asset, day)).write_text("x")

    monkeypatch.setattr(daypack, "export", lambda *a: (_ for _ in ()).throw(AssertionError("real export")))
    rp.ensure_daypacks(ex, tmp_path, cap=3, export=fake_export)
    assert len(calls) == 3 and all(not c[2] for c in calls)
    assert rp.pack_name(*calls[0][:2]) != existing
    linked = [e["href"] for f in ex.values() for items in f.values() for e in items if e["href"]]
    assert existing in linked and all((tmp_path / h).exists() for h in linked)
    assert len(set(linked)) == 4                                 # 1 existing + 3 exported; the rest unlinked


def test_failed_export_drops_link(tmp_path):
    ex = rp.examples(rv_prepare(table()))

    def boom(*a):
        raise FileNotFoundError("no bars")

    rp.ensure_daypacks(ex, tmp_path, export=boom)
    assert all(e["href"] is None for f in ex.values() for items in f.values() for e in items)


def test_write_links_examples_to_created_packs(tmp_path):
    made = []

    def fake_export(asset, day, relaxed):
        made.append(rp.pack_name(asset, day))
        (tmp_path / made[-1]).write_text("x")

    path = rp.write(both(), tmp_path / "review.html", export=fake_export)
    page = path.read_text()
    hrefs = set(re.findall(r'href="([^"#]+\.html)"', page)) - {"index.html"}
    assert hrefs and hrefs <= set(made)


def test_malicious_bucket_name_is_escaped():
    bad = '<img src=x onerror=alert(1)>'
    df = table(window=bad)
    page = rp.render(rp.build(df))
    assert bad not in page
    assert html_escaped(bad) in page
    assert any(r["bucket"] == bad for r in embedded(page)["buckets"]["2022_model"]["window"])


def html_escaped(s):
    import html
    return html.escape(s)


def test_cross_model_best_only_at_min_n():
    d = rp.build(both())
    rows = {r["bucket"]: r for r in d["cross"]["window"]}
    assert rows["london_kz"]["best"] == "mmxm"                   # 30 mmsm trades → enough
    small = pd.concat([table(n=10), table("mmbm", n=10, asset="US500")], ignore_index=True)
    assert all(r["best"] == "—" for r in rp.build(small)["cross"]["window"])
    page = rp.render(rp.build(small))
    assert 'class="best"' not in page


def test_index_links_review_page(tmp_path, monkeypatch):
    monkeypatch.setattr(daypack, "OUT", tmp_path)
    page = daypack.write_index([]).read_text()
    assert 'href="review.html"' in page
