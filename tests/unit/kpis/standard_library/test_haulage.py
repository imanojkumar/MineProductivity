"""Tests for mineproductivity.kpis.standard_library.haulage."""

from __future__ import annotations

from mineproductivity.kpis.standard_library.haulage import TruckCycleTime


class TestTruckCycleTime:
    def test_code(self) -> None:
        assert TruckCycleTime.meta.code == "HAUL.TruckCycleTime"

    def test_required_columns_are_the_six_cycle_legs(self) -> None:
        assert TruckCycleTime()._required_columns() == (
            "queue_min",
            "spot_min",
            "load_min",
            "haul_min",
            "dump_min",
            "return_min",
        )

    def test_sums_all_six_legs_for_a_single_cycle(self) -> None:
        row = {
            "queue_min": 1.5,
            "spot_min": 0.5,
            "load_min": 2.5,
            "haul_min": 8.0,
            "dump_min": 1.0,
            "return_min": 6.0,
        }
        result = TruckCycleTime().compute([row])
        assert result.value == 19.5

    def test_mean_across_multiple_cycles(self) -> None:
        legs = {
            "queue_min": 1.0,
            "spot_min": 1.0,
            "load_min": 1.0,
            "haul_min": 1.0,
            "dump_min": 1.0,
            "return_min": 1.0,
        }
        double_legs = {key: value * 2 for key, value in legs.items()}
        result = TruckCycleTime().compute([legs, double_legs])
        assert result.value == 9.0

    def test_zero_cycles_returns_none(self) -> None:
        result = TruckCycleTime().compute([])
        assert result.value is None
