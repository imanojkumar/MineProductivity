"""Tests for mineproductivity.kpis.standard_library.energy."""

from __future__ import annotations

from mineproductivity.events import ResourceType

from mineproductivity.kpis.standard_library.energy import FuelConsumed


class TestFuelConsumed:
    def test_code(self) -> None:
        assert FuelConsumed.meta.code == "ENERGY.FuelConsumed"

    def test_sums_only_fuel_readings(self) -> None:
        rows = [
            {"resource_type": ResourceType.FUEL, "quantity": 100.0},
            {"resource_type": ResourceType.WATER, "quantity": 500.0},
            {"resource_type": ResourceType.FUEL, "quantity": 50.0},
        ]
        result = FuelConsumed().compute(rows)
        assert result.value == 150.0

    def test_no_fuel_readings_is_a_legitimate_zero(self) -> None:
        rows = [{"resource_type": ResourceType.WATER, "quantity": 500.0}]
        result = FuelConsumed().compute(rows)
        assert result.value == 0.0

    def test_empty_rows_is_zero(self) -> None:
        result = FuelConsumed().compute([])
        assert result.value == 0.0
