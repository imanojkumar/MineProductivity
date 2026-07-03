"""``PolarsBackend``: a fast, multi-threaded execution backend."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.kpis.backends.base_backend import ExecutionBackend
from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation

__all__ = ["PolarsBackend"]


class PolarsBackend(ExecutionBackend):
    """A fast, multi-threaded backend built on Polars."""

    def assemble(self, rows: Sequence[Mapping[str, Any]], columns: tuple[str, ...]) -> Any:
        import polars as pl

        frame = pl.DataFrame(list(rows))
        for column in columns:
            if column not in frame.columns:
                frame = frame.with_columns(pl.lit(None).alias(column))
        return frame.select(list(columns)) if columns else frame

    def to_rows(self, table: Any) -> Sequence[Mapping[str, Any]]:
        result: list[Mapping[str, Any]] = table.to_dicts()
        return result

    def group_and_aggregate(self, table: Any, by: tuple[str, ...], aggregation: Aggregation) -> Any:
        import polars as pl

        if aggregation is Aggregation.DERIVED:
            raise KPIAggregationError(
                "DERIVED aggregation has no raw-row grouping; use CompositeKPI"
            )

        numeric_columns = [
            name
            for name, dtype in zip(table.columns, table.dtypes, strict=True)
            if dtype.is_numeric() and name not in by
        ]
        agg_fn = (
            pl.mean
            if aggregation in (Aggregation.AVERAGE, Aggregation.WEIGHTED_AVERAGE)
            else pl.sum
        )
        exprs = [agg_fn(column).alias(column) for column in numeric_columns]
        if not by:
            return table.select(exprs) if exprs else table.head(0)
        return table.group_by(list(by), maintain_order=True).agg(exprs)

    def to_pandas(self, table: Any) -> Any:
        return table.to_pandas()
