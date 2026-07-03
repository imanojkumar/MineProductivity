"""Tests for mineproductivity.connectors.base."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.health import ConnectorHealth, HealthStatus

_SINCE = datetime(2026, 6, 25, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, tzinfo=timezone.utc)


class _MinimalConnector(FMSConnector):
    name = "minimal"

    def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())

    def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())


class _CycleAndMaintenanceConnector(FMSConnector):
    name = "cycle-and-maintenance"

    def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())

    def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())

    def get_maintenance_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())


class TestIngestionMode:
    def test_has_three_modes(self) -> None:
        assert len(list(IngestionMode)) == 3

    def test_values(self) -> None:
        assert IngestionMode.BATCH.value == "batch"
        assert IngestionMode.INCREMENTAL.value == "incremental"
        assert IngestionMode.STREAMING.value == "streaming"


class TestFMSConnectorAbstractContract:
    def test_cannot_instantiate_abstract_base(self) -> None:
        with pytest.raises(TypeError):
            FMSConnector()  # type: ignore[abstract]

    def test_name_defaults_to_abstract(self) -> None:
        assert FMSConnector.name == "abstract"

    def test_default_supported_modes_is_batch(self) -> None:
        assert _MinimalConnector.supported_modes == (IngestionMode.BATCH,)


class TestDefaultMethodBodies:
    def test_get_maintenance_data_default_yields_nothing(self) -> None:
        conn = _MinimalConnector()
        assert list(conn.get_maintenance_data(_SINCE, _UNTIL)) == []

    def test_get_production_data_default_yields_nothing(self) -> None:
        conn = _MinimalConnector()
        assert list(conn.get_production_data(_SINCE, _UNTIL)) == []

    def test_get_consumption_data_default_yields_nothing(self) -> None:
        conn = _MinimalConnector()
        assert list(conn.get_consumption_data(_SINCE, _UNTIL)) == []

    def test_get_safety_data_default_yields_nothing(self) -> None:
        conn = _MinimalConnector()
        assert list(conn.get_safety_data(_SINCE, _UNTIL)) == []

    def test_health_check_default_is_unknown(self) -> None:
        conn = _MinimalConnector()
        health = conn.health_check()
        assert isinstance(health, ConnectorHealth)
        assert health.status is HealthStatus.UNKNOWN


class TestProvidedEventTypes:
    def test_minimal_connector_provides_only_cycle_and_delay(self) -> None:
        assert _MinimalConnector.provided_event_types() == ("cycle", "delay")

    def test_connector_overriding_maintenance_reports_it(self) -> None:
        provided = _CycleAndMaintenanceConnector.provided_event_types()
        assert "cycle" in provided
        assert "delay" in provided
        assert "maintenance" in provided
        assert "production" not in provided
