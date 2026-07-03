"""``UtilizationKPI``: the ``UTIL`` namespace."""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["UtilizationKPI"]


class UtilizationKPI(BaseKPI, ABC):
    """``UTIL`` namespace: PA, UA, EU, OEE -- built on the canonical time
    model (design spec §19): ``calendar >= scheduled >= available >=
    operating``."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "UTIL")
