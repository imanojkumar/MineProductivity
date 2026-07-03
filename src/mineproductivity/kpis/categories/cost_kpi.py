"""``CostKPI``: the ``COST`` namespace."""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["CostKPI"]


class CostKPI(BaseKPI, ABC):
    """``COST`` namespace: fuel per tonne, cost per tonne."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "COST")
