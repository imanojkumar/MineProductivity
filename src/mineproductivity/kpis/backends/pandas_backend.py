"""``PandasBackend``: the default execution backend (design spec §28)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.kpis.backends.base_backend import ExecutionBackend
from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation

__all__ = ["PandasBackend"]


class PandasBackend(ExecutionBackend):
    """The default backend -- "pandas... will feel immediately familiar"
    (Developer Documentation)."""

    def assemble(self, rows: Sequence[Mapping[str, Any]], columns: tuple[str, ...]) -> Any:
        import pandas as pd

        frame = pd.DataFrame(list(rows))
        for column in columns:
            if column not in frame.columns:
                frame[column] = None
        return frame[list(columns)] if columns else frame

    def to_rows(self, table: Any) -> Sequence[Mapping[str, Any]]:
        result: list[Mapping[str, Any]] = table.to_dict("records")
        return result

    def group_and_aggregate(self, table: Any, by: tuple[str, ...], aggregation: Aggregation) -> Any:
        if aggregation is Aggregation.DERIVED:
            raise KPIAggregationError(
                "DERIVED aggregation has no raw-row grouping; use CompositeKPI"
            )
        if not by:
            numeric = table.select_dtypes("number")
            if aggregation in (Aggregation.AVERAGE, Aggregation.WEIGHTED_AVERAGE):
                return numeric.mean().to_frame().T
            return numeric.sum().to_frame().T
        grouped = table.groupby(list(by), as_index=False)
        if aggregation in (Aggregation.AVERAGE, Aggregation.WEIGHTED_AVERAGE):
            return grouped.mean(numeric_only=True)
        return grouped.sum(numeric_only=True)

    def to_pandas(self, table: Any) -> Any:
        return table
