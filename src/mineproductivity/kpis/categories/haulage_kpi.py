"""``HaulageKPI``: the ``HAUL`` namespace."""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["HaulageKPI"]


class HaulageKPI(BaseKPI, ABC):
    """``HAUL`` namespace: cycle time context, match factor, TonKm."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "HAUL")
