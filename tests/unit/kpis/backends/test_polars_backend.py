"""Tests for mineproductivity.kpis.backends.polars_backend."""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from mineproductivity.kpis.backends.polars_backend import PolarsBackend
from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation

ROWS = [
    {"equipment_id": "HT-1", "payload_t": 100.0},
    {"equipment_id": "HT-1", "payload_t": 50.0},
    {"equipment_id": "HT-2", "payload_t": 200.0},
]


class TestAssemble:
    def test_produces_a_polars_dataframe_with_exactly_the_requested_columns(self) -> None:
        backend = PolarsBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        assert isinstance(table, pl.DataFrame)
        assert table.columns == ["equipment_id", "payload_t"]
        assert len(table) == 3

    def test_missing_column_is_filled_with_null(self) -> None:
        backend = PolarsBackend()
        table = backend.assemble(ROWS, ("equipment_id", "missing_col"))
        assert table["missing_col"].null_count() == 3


class TestToRows:
    def test_round_trips_back_to_the_original_row_shape(self) -> None:
        backend = PolarsBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        rows = backend.to_rows(table)
        assert len(rows) == 3
        assert rows[0]["equipment_id"] == "HT-1"


class TestGroupAndAggregate:
    def test_additive_sums_grouped_numeric_columns(self) -> None:
        backend = PolarsBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.ADDITIVE)
        rows = {row["equipment_id"]: row["payload_t"] for row in backend.to_rows(grouped)}
        assert rows["HT-1"] == 150.0
        assert rows["HT-2"] == 200.0

    def test_average_means_grouped_numeric_columns(self) -> None:
        backend = PolarsBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.AVERAGE)
        rows = {row["equipment_id"]: row["payload_t"] for row in backend.to_rows(grouped)}
        assert rows["HT-1"] == 75.0

    def test_no_group_by_columns_aggregates_the_whole_table(self) -> None:
        backend = PolarsBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, (), Aggregation.ADDITIVE)
        rows = backend.to_rows(grouped)
        assert rows[0]["payload_t"] == 350.0

    def test_derived_aggregation_raises(self) -> None:
        backend = PolarsBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        with pytest.raises(KPIAggregationError):
            backend.group_and_aggregate(table, ("equipment_id",), Aggregation.DERIVED)


class TestToPandas:
    def test_converts_to_a_pandas_dataframe(self) -> None:
        backend = PolarsBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        frame = backend.to_pandas(table)
        assert isinstance(frame, pd.DataFrame)
        assert len(frame) == 3
