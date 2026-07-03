"""Tests for mineproductivity.kpis.standard_library.utilization."""

from __future__ import annotations

from mineproductivity.kpis.composite import CompositeKPI
from mineproductivity.kpis.metadata import Aggregation
from mineproductivity.kpis.result import KPIResult
from mineproductivity.kpis.standard_library.utilization import (
    OverallEquipmentEffectiveness,
    PerformanceRatio,
    PhysicalAvailability,
    UseOfAvailability,
)


class TestPhysicalAvailability:
    def test_code(self) -> None:
        assert PhysicalAvailability.meta.code == "UTIL.PA"

    def test_no_downtime_means_full_availability(self) -> None:
        result = PhysicalAvailability().compute([{"scheduled_h": 12.0, "duration_h": 0.0}])
        assert result.value == 1.0

    def test_downtime_reduces_availability(self) -> None:
        result = PhysicalAvailability().compute([{"scheduled_h": 12.0, "duration_h": 3.0}])
        assert result.value == 0.75

    def test_zero_maintenance_rows_in_the_window_returns_none_not_a_crash(self) -> None:
        """Regression test: an earlier implementation indexed ``rows[0]``
        unconditionally, which raised ``IndexError`` for a shift with
        genuinely zero ``MaintenanceEvent`` rows (caught via
        ``KPIEngine.execute("UTIL.OEE", ...)`` against an empty store in
        the engine test suite). ``scheduled_h`` is only carried on rows
        that exist, so with none, it cannot be recovered here."""
        result = PhysicalAvailability().compute([])
        assert result.value is None

    def test_multiple_downtime_events_sum(self) -> None:
        result = PhysicalAvailability().compute(
            [
                {"scheduled_h": 12.0, "duration_h": 1.0},
                {"scheduled_h": 12.0, "duration_h": 2.0},
            ]
        )
        assert result.value == 0.75

    def test_zero_scheduled_hours_returns_none(self) -> None:
        result = PhysicalAvailability().compute([{"scheduled_h": 0.0, "duration_h": 0.0}])
        assert result.value is None


class TestUseOfAvailability:
    def test_code(self) -> None:
        assert UseOfAvailability.meta.code == "UTIL.UA"

    def test_operating_over_available(self) -> None:
        rows = [
            {"event_type_code": "MAINTENANCE", "scheduled_h": 12.0, "duration_h": 1.0},
            {"event_type_code": "PRODUCTION", "scheduled_h": 12.0, "operating_h": 9.0},
        ]
        result = UseOfAvailability().compute(rows)
        assert result.value == 9.0 / 11.0

    def test_no_production_rows_returns_none(self) -> None:
        rows = [{"event_type_code": "MAINTENANCE", "scheduled_h": 12.0, "duration_h": 1.0}]
        result = UseOfAvailability().compute(rows)
        assert result.value is None

    def test_zero_scheduled_hours_returns_none(self) -> None:
        rows = [{"event_type_code": "PRODUCTION", "scheduled_h": 0.0, "operating_h": 5.0}]
        result = UseOfAvailability().compute(rows)
        assert result.value is None

    def test_available_hours_at_or_below_zero_returns_none(self) -> None:
        rows = [
            {"event_type_code": "MAINTENANCE", "scheduled_h": 12.0, "duration_h": 12.0},
            {"event_type_code": "PRODUCTION", "scheduled_h": 12.0, "operating_h": 1.0},
        ]
        result = UseOfAvailability().compute(rows)
        assert result.value is None


class TestPerformanceRatio:
    def test_code(self) -> None:
        assert PerformanceRatio.meta.code == "UTIL.Performance"

    def test_ratio_of_actual_to_planned(self) -> None:
        result = PerformanceRatio().compute([{"tonnes_moved": 9000.0, "planned_tonnes": 10000.0}])
        assert result.value == 0.9

    def test_zero_planned_tonnes_returns_none(self) -> None:
        result = PerformanceRatio().compute([{"tonnes_moved": 0.0, "planned_tonnes": 0.0}])
        assert result.value is None


class TestOverallEquipmentEffectiveness:
    def test_code(self) -> None:
        assert OverallEquipmentEffectiveness.meta.code == "UTIL.OEE"

    def test_is_a_composite_kpi(self) -> None:
        assert issubclass(OverallEquipmentEffectiveness, CompositeKPI)

    def test_aggregation_is_derived(self) -> None:
        assert OverallEquipmentEffectiveness.meta.aggregation is Aggregation.DERIVED

    def test_declares_pa_ua_performance_as_dependencies(self) -> None:
        assert OverallEquipmentEffectiveness.meta.dependencies == (
            "UTIL.PA",
            "UTIL.UA",
            "UTIL.Performance",
        )

    def test_multiplies_the_three_components(self) -> None:
        component_results = {
            "UTIL.PA": KPIResult(code="UTIL.PA", value=0.9, unit="ratio"),
            "UTIL.UA": KPIResult(code="UTIL.UA", value=0.85, unit="ratio"),
            "UTIL.Performance": KPIResult(code="UTIL.Performance", value=0.95, unit="ratio"),
        }
        result = OverallEquipmentEffectiveness().combine(component_results)
        assert result.value == 0.9 * 0.85 * 0.95

    def test_any_none_component_propagates_none(self) -> None:
        component_results = {
            "UTIL.PA": KPIResult(code="UTIL.PA", value=0.9, unit="ratio"),
            "UTIL.UA": KPIResult(code="UTIL.UA", value=None, unit="ratio"),
            "UTIL.Performance": KPIResult(code="UTIL.Performance", value=0.95, unit="ratio"),
        }
        result = OverallEquipmentEffectiveness().combine(component_results)
        assert result.value is None

    def test_combine_itself_has_a_defensive_none_guard_below_the_base_class_check(self) -> None:
        """``CompositeKPI.combine()`` already intercepts any ``None``
        -valued dependency before ever calling ``_combine()`` -- this
        belt-and-suspenders guard inside ``_combine`` itself is normally
        unreachable through that path, so it is exercised directly here."""
        component_results = {
            "UTIL.PA": KPIResult(code="UTIL.PA", value=0.9, unit="ratio"),
            "UTIL.UA": KPIResult(code="UTIL.UA", value=None, unit="ratio"),
            "UTIL.Performance": KPIResult(code="UTIL.Performance", value=0.95, unit="ratio"),
        }
        assert OverallEquipmentEffectiveness()._combine(component_results) is None
