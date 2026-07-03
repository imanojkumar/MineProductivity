"""``QualityKPI``: the ``QUAL``/``GRADE`` namespaces."""

from __future__ import annotations

from abc import ABC

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace

__all__ = ["QualityKPI"]


class QualityKPI(BaseKPI, ABC):
    """``QUAL``/``GRADE`` namespaces: recovery, head grade."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        enforce_namespace(cls, "QUAL", "GRADE")
