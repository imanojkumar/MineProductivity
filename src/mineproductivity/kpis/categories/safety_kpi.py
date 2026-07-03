"""``SafetyKPI``: the ``SAFE``/``AUTO`` namespaces."""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["SafetyKPI"]


class SafetyKPI(BaseKPI, ABC):
    """``SAFE``/``AUTO`` namespaces: exposure-normalized leading
    indicators."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "SAFE", "AUTO")
