"""Tests for mineproductivity.kpis.backends.duckdb_backend."""

from __future__ import annotations

import pandas as pd
import pytest

from mineproductivity.kpis.backends.duckdb_backend import DuckDBBackend
from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation

ROWS = [
    {"equipment_id": "HT-1", "payload_t": 100.0},
    {"equipment_id": "HT-1", "payload_t": 50.0},
    {"equipment_id": "HT-2", "payload_t": 200.0},
]


class TestAssemble:
    def test_produces_a_relation_with_exactly_the_requested_columns(self) -> None:
        backend = DuckDBBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        assert list(table.columns) == ["equipment_id", "payload_t"]
        assert table.shape[0] == 3

    def test_missing_column_is_filled_with_null(self) -> None:
        backend = DuckDBBackend()
        table = backend.assemble(ROWS, ("equipment_id", "missing_col"))
        assert table.df()["missing_col"].isna().all()


class TestToRows:
    def test_round_trips_back_to_the_original_row_shape(self) -> None:
        backend = DuckDBBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        rows = backend.to_rows(table)
        assert len(rows) == 3
        assert rows[0]["equipment_id"] == "HT-1"


class TestGroupAndAggregate:
    def test_additive_sums_grouped_numeric_columns_and_keeps_the_group_column(self) -> None:
        """Regression test: an earlier implementation passed only the
        aggregate expressions to DuckDB's ``relation.aggregate()``,
        silently dropping the group-by column from the projected output
        (caught by the kpis smoke test -- design spec §29 backend parity)."""
        backend = DuckDBBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.ADDITIVE)
        rows = backend.to_rows(grouped)
        assert all("equipment_id" in row for row in rows)
        totals = {row["equipment_id"]: row["payload_t"] for row in rows}
        assert totals["HT-1"] == 150.0
        assert totals["HT-2"] == 200.0

    def test_average_means_grouped_numeric_columns(self) -> None:
        backend = DuckDBBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.AVERAGE)
        rows = {row["equipment_id"]: row["payload_t"] for row in backend.to_rows(grouped)}
        assert rows["HT-1"] == 75.0

    def test_no_group_by_columns_aggregates_the_whole_table(self) -> None:
        backend = DuckDBBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, (), Aggregation.ADDITIVE)
        rows = backend.to_rows(grouped)
        assert rows[0]["payload_t"] == 350.0

    def test_derived_aggregation_raises(self) -> None:
        backend = DuckDBBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        with pytest.raises(KPIAggregationError):
            backend.group_and_aggregate(table, ("equipment_id",), Aggregation.DERIVED)


class TestToPandas:
    def test_converts_to_a_pandas_dataframe(self) -> None:
        backend = DuckDBBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        frame = backend.to_pandas(table)
        assert isinstance(frame, pd.DataFrame)
        assert len(frame) == 3
