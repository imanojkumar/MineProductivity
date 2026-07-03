"""``ExecutionBackend``: one pluggable strategy for the bulk, vectorized
parts of KPI computation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.kpis.metadata import Aggregation
from mineproductivity.kpis.result import KPIResult

__all__ = ["ExecutionBackend"]


class ExecutionBackend(ABC):
    """One pluggable strategy for the bulk, vectorized parts of KPI
    computation (row assembly, grouping, windowing) --
    :meth:`~mineproductivity.kpis.base_kpi.BaseKPI._compute` itself stays
    backend-agnostic (plain Python over ``rows``), but
    ``KPIEngine.rows_for`` and :meth:`~mineproductivity.kpis.result.KPIResult.to_frame`
    delegate here for scale.

    :meth:`assemble`/:meth:`to_rows` are a deliberate refinement of the
    design specification's illustrative ``assemble(query, columns)``
    signature: since store-querying is an ``events``-specific concern
    already owned by ``KPIEngine`` (which holds the ``EventStore``),
    backends operate on already-flattened row dicts rather than
    duplicating query execution once per backend implementation --
    backends stay focused on tabular manipulation, their own specialty.
    """

    @abstractmethod
    def assemble(self, rows: Sequence[Mapping[str, Any]], columns: tuple[str, ...]) -> Any:
        """Convert ``rows`` into a backend-native tabular object
        containing exactly ``columns`` (column-pruned, design spec §22)."""

    @abstractmethod
    def to_rows(self, table: Any) -> Sequence[Mapping[str, Any]]:
        """Convert a backend-native table back into the neutral
        ``Sequence[Mapping[str, Any]]`` shape
        :meth:`~mineproductivity.kpis.base_kpi.BaseKPI._compute` expects."""

    @abstractmethod
    def group_and_aggregate(self, table: Any, by: tuple[str, ...], aggregation: Aggregation) -> Any:
        """Group ``table`` by ``by`` and aggregate its numeric columns
        per ``aggregation`` -- summed for ``ADDITIVE``/``RATIO`` (a
        ``RATIO`` KPI's own ``_compute`` divides the summed numerator
        and denominator columns itself; this method never pre-divides),
        averaged for ``AVERAGE``/``WEIGHTED_AVERAGE``."""

    @abstractmethod
    def to_pandas(self, table: Any) -> Any:
        """Universal escape hatch -- "Export to a DataFrame for your own
        analysis" (Developer Documentation SDK section)."""

    def result_to_frame(self, result: KPIResult) -> Any:
        """The hook :meth:`~mineproductivity.kpis.result.KPIResult.to_frame`
        delegates to: a one-row backend-native table."""
        row = {"code": result.code, "value": result.value, "unit": result.unit, "n": result.n}
        return self.assemble([row], ("code", "value", "unit", "n"))

    def plot_result(self, result: KPIResult) -> Any:
        """Delegates to visualization-metadata hooks -- rendering itself
        belongs to a future ``visualization`` package (design spec §4),
        which is expected to override this hook; the base implementation
        raises to make that boundary explicit rather than silently doing
        nothing."""
        raise NotImplementedError(
            "chart rendering belongs to a future visualization package, not kpis itself"
        )

    def pareto_result(self, result: KPIResult) -> Any:
        """See :meth:`plot_result`."""
        raise NotImplementedError(
            "chart rendering belongs to a future visualization package, not kpis itself"
        )
