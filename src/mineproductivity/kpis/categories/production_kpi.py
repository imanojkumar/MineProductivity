"""``ProductionKPI``: the ``PROD`` namespace."""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["ProductionKPI"]


class ProductionKPI(BaseKPI, ABC):
    """``PROD`` namespace: throughput, cycle time, payload -- read
    directly from ``CycleEvent`` streams (Developer & Cookbook Guide
    Part III)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "PROD")
