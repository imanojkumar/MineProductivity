"""Tests for mineproductivity.kpis.backends.numpy_backend."""

from __future__ import annotations

import pandas as pd
import pytest

from mineproductivity.kpis.backends.numpy_backend import NumPyBackend
from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation

ROWS = [
    {"equipment_id": "HT-1", "payload_t": 100.0},
    {"equipment_id": "HT-1", "payload_t": 50.0},
    {"equipment_id": "HT-2", "payload_t": 200.0},
]


class TestAssemble:
    def test_produces_a_dict_of_arrays_with_exactly_the_requested_columns(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        assert set(table.keys()) == {"equipment_id", "payload_t"}
        assert len(table["equipment_id"]) == 3

    def test_missing_column_is_filled_with_none(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "missing_col"))
        assert all(value is None for value in table["missing_col"])


class TestToRows:
    def test_round_trips_back_to_the_original_row_shape(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        rows = backend.to_rows(table)
        assert len(rows) == 3
        assert rows[0]["equipment_id"] == "HT-1"

    def test_empty_table_produces_no_rows(self) -> None:
        backend = NumPyBackend()
        assert backend.to_rows({}) == []


class TestGroupAndAggregate:
    def test_additive_sums_grouped_numeric_columns(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.ADDITIVE)
        rows = {row["equipment_id"]: row["payload_t"] for row in backend.to_rows(grouped)}
        assert rows["HT-1"] == 150.0
        assert rows["HT-2"] == 200.0

    def test_average_means_grouped_numeric_columns(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.AVERAGE)
        rows = {row["equipment_id"]: row["payload_t"] for row in backend.to_rows(grouped)}
        assert rows["HT-1"] == 75.0

    def test_no_group_by_columns_aggregates_the_whole_table(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, (), Aggregation.ADDITIVE)
        rows = backend.to_rows(grouped)
        assert rows[0]["payload_t"] == 350.0

    def test_empty_table_produces_zero_groups(self) -> None:
        backend = NumPyBackend()
        grouped = backend.group_and_aggregate({}, (), Aggregation.ADDITIVE)
        assert backend.to_rows(grouped) == []

    def test_non_numeric_columns_are_excluded_from_aggregation(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.ADDITIVE)
        assert "equipment_id" in grouped
        assert "payload_t" in grouped

    def test_derived_aggregation_raises(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        with pytest.raises(KPIAggregationError):
            backend.group_and_aggregate(table, ("equipment_id",), Aggregation.DERIVED)

    def test_a_column_that_is_entirely_none_is_treated_as_non_numeric(self) -> None:
        backend = NumPyBackend()
        rows = [{"equipment_id": "HT-1", "note": None}, {"equipment_id": "HT-1", "note": None}]
        table = backend.assemble(rows, ("equipment_id", "note"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.ADDITIVE)
        assert "note" not in grouped

    def test_a_leading_none_in_a_numeric_column_does_not_prevent_detection(self) -> None:
        backend = NumPyBackend()
        rows = [
            {"equipment_id": "HT-1", "payload_t": None},
            {"equipment_id": "HT-1", "payload_t": 100.0},
        ]
        table = backend.assemble(rows, ("equipment_id", "payload_t"))
        grouped = backend.group_and_aggregate(table, ("equipment_id",), Aggregation.ADDITIVE)
        assert "payload_t" in grouped


class TestToPandas:
    def test_converts_to_a_dataframe(self) -> None:
        backend = NumPyBackend()
        table = backend.assemble(ROWS, ("equipment_id", "payload_t"))
        frame = backend.to_pandas(table)
        assert isinstance(frame, pd.DataFrame)
        assert len(frame) == 3
