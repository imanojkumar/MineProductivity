"""``DuckDBBackend``: an in-process, SQL-native execution backend."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.kpis.backends.base_backend import ExecutionBackend
from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation

__all__ = ["DuckDBBackend"]


class DuckDBBackend(ExecutionBackend):
    """An in-process, SQL-native backend built on DuckDB."""

    def assemble(self, rows: Sequence[Mapping[str, Any]], columns: tuple[str, ...]) -> Any:
        import duckdb
        import pandas as pd

        frame = pd.DataFrame(list(rows))
        for column in columns:
            if column not in frame.columns:
                frame[column] = None
        projected = frame[list(columns)] if columns else frame
        return duckdb.from_df(projected)

    def to_rows(self, table: Any) -> Sequence[Mapping[str, Any]]:
        result: list[Mapping[str, Any]] = table.df().to_dict("records")
        return result

    def group_and_aggregate(self, table: Any, by: tuple[str, ...], aggregation: Aggregation) -> Any:
        import pandas as pd

        if aggregation is Aggregation.DERIVED:
            raise KPIAggregationError(
                "DERIVED aggregation has no raw-row grouping; use CompositeKPI"
            )

        frame = table.df()
        numeric_columns = [
            column
            for column in frame.columns
            if column not in by and pd.api.types.is_numeric_dtype(frame[column])
        ]
        sql_fn = (
            "AVG" if aggregation in (Aggregation.AVERAGE, Aggregation.WEIGHTED_AVERAGE) else "SUM"
        )
        group_columns = ", ".join(f'"{column}"' for column in by)
        aggr_columns = ", ".join(
            f'{sql_fn}("{column}") AS "{column}"' for column in numeric_columns
        )
        aggr_expr = ", ".join(part for part in (group_columns, aggr_columns) if part) or "1"
        return table.aggregate(aggr_expr, group_columns)

    def to_pandas(self, table: Any) -> Any:
        result = table.df()
        return result
