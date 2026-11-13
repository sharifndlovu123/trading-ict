"""Model registry — every model module exposes ``MODEL`` (name), ``Params`` and
``find_setups(bars_1m, day, asset, params, ctx) -> list[Setup]``. The runner picks
the module from the params' type, so one pipeline runs any model."""

from __future__ import annotations

from types import ModuleType


def modules() -> dict[str, ModuleType]:
    from ict_engine.models import model_2022, model_cameron, model_mmxm, model_pd_return, model_sb
    return {m.MODEL: m for m in (model_2022, model_mmxm, model_sb, model_cameron, model_pd_return)}


def module_for(params) -> ModuleType:
    for m in modules().values():
        if isinstance(params, m.Params):
            return m
    raise TypeError(f"no model registered for {type(params).__name__}")


def labels(module: ModuleType) -> tuple[str, ...]:
    """Reference-case model labels a module answers for (mmxm → mmbm/mmsm)."""
    return getattr(module, "NAMES", (module.MODEL,))
