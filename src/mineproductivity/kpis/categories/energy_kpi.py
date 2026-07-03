"""``EnergyKPI``: the ``ENERGY``/``CARBON``/``WATER`` namespaces."""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["EnergyKPI"]


class EnergyKPI(BaseKPI, ABC):
    """``ENERGY``/``CARBON``/``WATER`` namespaces: consumption, emissions,
    and water-use indicators."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "ENERGY", "CARBON", "WATER")
