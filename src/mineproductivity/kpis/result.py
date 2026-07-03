"""``KPIResult``: the immutable, traceable outcome of one KPI computation."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

__all__ = ["KPIResult"]


@dataclasses.dataclass(frozen=True, slots=True)
class KPIResult(BaseValueObject):
    """The outcome of one :class:`~mineproductivity.kpis.base_kpi.BaseKPI`
    computation -- a scalar value (or ``None`` if legitimately
    uncomputable), plus enough provenance (unit, source-row count,
    scope) to trace it back to its inputs.

    Examples
    --------
    >>> result = KPIResult(code="PROD.TPH", value=1212.1, unit="t/h", n=48)
    >>> result.value
    1212.1
    >>> KPIResult(code="PROD.TPH", value=None, unit="t/h", warnings=("zero operating hours",)).warnings
    ('zero operating hours',)
    """

    code: str
    value: float | None
    unit: str
    n: int = dataclasses.field(default=0, kw_only=True)
    warnings: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    scope: Mapping[str, str] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        object.__setattr__(self, "scope", MappingProxyType(dict(self.scope)))

    def to_frame(self) -> Any:
        """Export to a DataFrame via the process's active
        :class:`~mineproductivity.kpis.backends.base_backend.ExecutionBackend`
        (design spec §9's ``kpis.backends._active_backend``) -- "Familiar
        by design": ``.kpi(code).by(grouping).to_frame()`` mirrors
        ``df.groupby(...).agg(...)``."""
        from mineproductivity.kpis.backends import get_active_backend

        return get_active_backend().result_to_frame(self)

    def plot(self) -> Any:
        """Delegates to the active backend's visualization-metadata hook."""
        from mineproductivity.kpis.backends import get_active_backend

        return get_active_backend().plot_result(self)

    def pareto(self) -> Any:
        """Delegates to the active backend's visualization-metadata hook."""
        from mineproductivity.kpis.backends import get_active_backend

        return get_active_backend().pareto_result(self)
