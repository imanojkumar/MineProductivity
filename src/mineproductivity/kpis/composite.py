"""``CompositeKPI``: a KPI whose value is derived from other KPIs'
already-computed results, not directly from raw event rows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.result import KPIResult

__all__ = ["CompositeKPI"]


class CompositeKPI(BaseKPI, ABC):
    """A KPI whose value is DERIVED from other KPIs' already-computed
    results, not directly from raw event rows -- e.g. ``UTIL.OEE =
    UTIL.PA x UTIL.Performance x UTIL.Quality`` (Part III, Canonical
    Semantics). Kept a distinct base class from leaf KPIs (design spec
    AD-KP-04) so "reads raw rows" and "reads other KPIs' results" are
    never conflated in one method signature.
    """

    @abstractmethod
    def _combine(self, component_results: Mapping[str, KPIResult]) -> float | None:
        """Pure function over already-computed dependency results.

        MUST NOT raise for a legitimately uncomputable input; if any
        required component's :attr:`KPIResult.value` is ``None``, the
        composite's own value MUST also be ``None`` (propagated, never
        fabricated as zero)."""

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        # CompositeKPI never reads rows directly; KPIEngine resolves
        # meta.dependencies first and calls _combine via combine().
        raise NotImplementedError("CompositeKPI uses _combine, not _compute")

    def combine(self, component_results: Mapping[str, KPIResult]) -> KPIResult:
        """The composite counterpart of :meth:`BaseKPI.compute`: if any
        declared dependency's result has a ``None`` value, propagate
        ``None`` with a warning rather than calling :meth:`_combine`
        (which would otherwise have to special-case every missing
        dependency itself)."""
        missing = [code for code, result in component_results.items() if result.value is None]
        if missing:
            return KPIResult(
                code=self.meta.code,
                value=None,
                unit=self.meta.unit,
                n=sum(result.n for result in component_results.values()),
                warnings=(f"upstream dependency has no value: {sorted(missing)}",),
            )
        value = self._combine(component_results)
        return KPIResult(
            code=self.meta.code,
            value=value,
            unit=self.meta.unit,
            n=sum(result.n for result in component_results.values()),
        )
