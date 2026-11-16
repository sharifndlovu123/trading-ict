"""Price-unit scale per asset (ict_engine.data.instruments.unit): thresholds written in index points (the 0.25 stop
buffer, the 2022 model's 10-point minimum target = ICT's "10 points or 40 ticks") keep their value on the indices and
gold, and scale by the futures tick elsewhere, so silver, the dollar index and EUR/USD can trade (new-dataset sweep
2026-11-16: 0 trades there)."""
import pytest

from ict_engine.data import instruments


def test_indices_and_gold_are_unchanged():
    for a in ("US100", "US500", "US30", "XAUUSD", "NQCME"):
        assert instruments.unit(a) == 1.0


def test_other_assets_scale_by_the_tick():
    assert instruments.unit("XAGUSD") == pytest.approx(0.02)          # 0.25 × 0.02 = 0.005 = 1 tick of SI
    assert instruments.unit("DXY") == pytest.approx(0.02)             # 1 tick of DX
    assert instruments.unit("EURUSD") == pytest.approx(0.0002)        # 0.25 × 0.0002 = 0.00005 = 1 tick of 6E
    assert 10 * instruments.unit("EURUSD") == pytest.approx(0.002)    # the 10-point minimum = 40 ticks = 20 pips


def test_futures_cost_exists_for_every_benchmark_asset():
    for a in ("US100", "US500", "US30", "XAUUSD", "XAGUSD", "DXY", "EURUSD"):
        assert instruments.futures_cost(a) > 0
    assert instruments.futures_cost("EURUSD") == pytest.approx(0.00005 + 4.5 / 125000)
    assert instruments.futures_cost("DXY") == pytest.approx(0.005 + 4.5 / 1000)


def test_scaled_params_are_untouched_on_indices_and_scaled_elsewhere():
    from ict_engine.models import model_2022, model_mmxm, model_sb
    p = model_2022.Params()
    assert instruments.scaled(p, "US100") is p and instruments.scaled(p, "XAUUSD") is p
    e = instruments.scaled(p, "EURUSD")
    assert e.stop_buffer == pytest.approx(0.00005) and e.min_potential == pytest.approx(0.002)
    assert e.variant == p.variant                                     # the label (and so the run id) does not change
    for m in (model_mmxm, model_sb):
        q = m.Params()
        s = instruments.scaled(q, "XAGUSD")
        assert s.stop_buffer == pytest.approx(0.005) and s.variant == q.variant
