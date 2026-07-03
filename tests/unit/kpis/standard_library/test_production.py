"""Tests for mineproductivity.kpis.standard_library.production."""

from __future__ import annotations

from mineproductivity.kpis.metadata import Aggregation, Direction
from mineproductivity.kpis.standard_library.production import TonnesPerHour


class TestMetadata:
    def test_code_and_namespace(self) -> None:
        assert TonnesPerHour.meta.code == "PROD.TPH"

    def test_aggregation_is_ratio(self) -> None:
        assert TonnesPerHour.meta.aggregation is Aggregation.RATIO

    def test_direction_is_higher_is_better(self) -> None:
        assert TonnesPerHour.meta.direction is Direction.HIGHER_IS_BETTER

    def test_required_events_is_cycle(self) -> None:
        assert TonnesPerHour.meta.required_events == ("CYCLE",)


class TestRequiredColumns:
    def test_requires_payload_t_and_operating_h(self) -> None:
        assert TonnesPerHour()._required_columns() == ("payload_t", "operating_h")


class TestCompute:
    def test_worked_example_matches_the_design_specification(self) -> None:
        kpi = TonnesPerHour()
        result = kpi.compute([{"payload_t": 14545.2, "operating_h": 12.0}])
        assert result.value == 14545.2 / 12.0

    def test_multiple_rows_sum_before_dividing_not_averaged_per_row(self) -> None:
        kpi = TonnesPerHour()
        result = kpi.compute(
            [
                {"payload_t": 100.0, "operating_h": 1.0},
                {"payload_t": 200.0, "operating_h": 1.0},
            ]
        )
        assert result.value == 150.0

    def test_zero_operating_hours_returns_none_not_a_zero_division_error(self) -> None:
        kpi = TonnesPerHour()
        result = kpi.compute([{"payload_t": 0.0, "operating_h": 0.0}])
        assert result.value is None

    def test_empty_rows_returns_none(self) -> None:
        kpi = TonnesPerHour()
        result = kpi.compute([])
        assert result.value is None
