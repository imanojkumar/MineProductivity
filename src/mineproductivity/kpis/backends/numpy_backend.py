"""``NumPyBackend``: the leanest execution backend -- no DataFrame
dependency at all.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.kpis.backends.base_backend import ExecutionBackend
from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation

__all__ = ["NumPyBackend"]

#: A NumPyBackend "table" is a structure-of-arrays: one 1-D ``numpy``
#: array per column, all the same length. Suited to the platform's
#: lean-core, opt-in-extras philosophy (design spec §10.9) -- the only
#: third-party dependency this backend needs is ``numpy`` itself, no
#: DataFrame library.
NumPyTable = dict[str, Any]


class NumPyBackend(ExecutionBackend):
    """The leanest backend: a plain ``dict[str, numpy.ndarray]`` "table,"
    with no DataFrame dependency at all."""

    def assemble(self, rows: Sequence[Mapping[str, Any]], columns: tuple[str, ...]) -> NumPyTable:
        import numpy as np

        return {
            column: np.array([row.get(column) for row in rows], dtype=object) for column in columns
        }

    def to_rows(self, table: NumPyTable) -> Sequence[Mapping[str, Any]]:
        if not table:
            return []
        columns = list(table.keys())
        length = len(next(iter(table.values())))
        return [{column: table[column][i] for column in columns} for i in range(length)]

    def group_and_aggregate(
        self, table: NumPyTable, by: tuple[str, ...], aggregation: Aggregation
    ) -> NumPyTable:
        import numpy as np

        if aggregation is Aggregation.DERIVED:
            raise KPIAggregationError(
                "DERIVED aggregation has no raw-row grouping; use CompositeKPI"
            )

        row_count = len(next(iter(table.values()))) if table else 0
        keys = list(zip(*(table[column] for column in by), strict=True)) if by else [()] * row_count
        unique_keys = sorted(set(keys))
        numeric_columns = [
            column for column in table if column not in by and _is_numeric_column(table[column])
        ]

        result: dict[str, list[Any]] = {column: [] for column in (*by, *numeric_columns)}
        for unique_key in unique_keys:
            mask = np.array([key == unique_key for key in keys])
            for index, column in enumerate(by):
                result[column].append(unique_key[index])
            for column in numeric_columns:
                values = table[column][mask].astype(float)
                if aggregation in (Aggregation.AVERAGE, Aggregation.WEIGHTED_AVERAGE):
                    result[column].append(float(np.mean(values)) if len(values) else None)
                else:
                    result[column].append(float(np.sum(values)) if len(values) else 0.0)
        return {column: np.array(values, dtype=object) for column, values in result.items()}

    def to_pandas(self, table: NumPyTable) -> Any:
        import pandas as pd

        return pd.DataFrame(table)


def _is_numeric_column(column: Any) -> bool:
    for value in column:
        if value is None:
            continue
        return isinstance(value, int | float) and not isinstance(value, bool)
    return False
