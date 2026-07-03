"""Tests for mineproductivity.kpis.standard_library.cost."""

from __future__ import annotations

from mineproductivity.events import ResourceType

from mineproductivity.kpis.standard_library.cost import FuelPerTonne


class TestFuelPerTonne:
    def test_code(self) -> None:
        assert FuelPerTonne.meta.code == "COST.FuelPerTonne"

    def test_declares_prod_tph_as_a_thematic_dependency(self) -> None:
        assert FuelPerTonne.meta.dependencies == ("PROD.TPH",)

    def test_required_events_span_consumption_and_cycle(self) -> None:
        assert FuelPerTonne.meta.required_events == ("CONSUMPTION", "CYCLE")

    def test_cross_event_type_computation_matches_worked_example(self) -> None:
        rows = [
            {
                "event_type_code": "CONSUMPTION",
                "resource_type": ResourceType.FUEL,
                "quantity": 1000.0,
            },
            {"event_type_code": "CYCLE", "payload_t": 200.0},
            {"event_type_code": "CYCLE", "payload_t": 300.0},
        ]
        result = FuelPerTonne().compute(rows)
        assert result.value == 1000.0 / 500.0

    def test_ignores_non_fuel_consumption_rows(self) -> None:
        rows = [
            {
                "event_type_code": "CONSUMPTION",
                "resource_type": ResourceType.FUEL,
                "quantity": 100.0,
            },
            {
                "event_type_code": "CONSUMPTION",
                "resource_type": ResourceType.WATER,
                "quantity": 5000.0,
            },
            {"event_type_code": "CYCLE", "payload_t": 100.0},
        ]
        result = FuelPerTonne().compute(rows)
        assert result.value == 1.0

    def test_zero_payload_returns_none(self) -> None:
        rows = [
            {
                "event_type_code": "CONSUMPTION",
                "resource_type": ResourceType.FUEL,
                "quantity": 100.0,
            }
        ]
        result = FuelPerTonne().compute(rows)
        assert result.value is None

    def test_it_re_derives_from_raw_rows_never_from_a_dependency_result(self) -> None:
        """A non-composite KPI receives only raw rows from
        ``BaseKPI.compute`` -- it never sees ``PROD.TPH``'s already
        -computed value, even though it declares it as a dependency
        (design spec: dependencies are a DAG-ordering hint, not a data
        channel, for anything but a ``CompositeKPI``)."""
        kpi = FuelPerTonne()
        assert not hasattr(kpi, "_combine")
