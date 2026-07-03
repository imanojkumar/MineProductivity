"""``MaintenanceKPI``: the ``MAINT`` namespace."""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["MaintenanceKPI"]


class MaintenanceKPI(BaseKPI, ABC):
    """``MAINT`` namespace: MTBF, MTTR, Ai."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "MAINT")
