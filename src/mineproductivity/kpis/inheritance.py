"""``specialize()``: KPI specialization/inheritance support -- the
mechanism behind ``PROD.TPH.Ore``/``PROD.TPH.Waste``.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.metadata import KPIMetadata

__all__ = ["specialize"]


def specialize(
    parent: type[BaseKPI],
    *,
    code: str,
    material_filter: str,
    official_name: str | None = None,
) -> type[BaseKPI]:
    """The inheritance mechanism behind ``PROD.TPH.Ore``/``PROD.TPH.Waste``
    (Part III, Introduction: "a generic ``PROD.TPH`` can be inherited...
    which reuse the parent's calculation with a material filter").

    Returns a new :class:`~mineproductivity.kpis.base_kpi.BaseKPI`
    subclass reusing ``parent``'s ``_compute``, pre-filtering rows by
    ``row["material_type"] == material_filter`` before delegating.

    The returned class's ``meta.code`` (``code``) still resolves against
    the same category base's namespace check as ``parent`` (design spec
    §10.4), since the specialized class is a genuine subclass of
    ``parent``, not a copy.
    """
    parent_meta = parent.meta
    specialized_meta = dataclasses.replace(
        parent_meta,
        code=code,
        official_name=official_name or f"{parent_meta.official_name} ({material_filter})",
    )

    class _Specialized(parent):  # type: ignore[misc, valid-type]
        meta: ClassVar[KPIMetadata] = specialized_meta

        def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
            filtered = [row for row in rows if row.get("material_type") == material_filter]
            result: float | None = super(_Specialized, self)._compute(filtered)
            return result

    _Specialized.__name__ = code.replace(".", "_")
    _Specialized.__qualname__ = _Specialized.__name__
    return _Specialized
