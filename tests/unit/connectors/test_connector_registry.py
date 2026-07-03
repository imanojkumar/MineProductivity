"""Tests for mineproductivity.connectors._registry."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.registry import UnregisteredLookupError

from mineproductivity.connectors._registry import CONNECTORS, get_connector, register_connector
from mineproductivity.connectors.base import FMSConnector

_SINCE = datetime(2026, 6, 25, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, tzinfo=timezone.utc)


class TestBuiltInConnectorsRegisteredByDefault:
    @pytest.mark.parametrize("name", ["csv", "excel", "rest", "graphql", "kafka", "mqtt"])
    def test_reference_connector_registered(self, name: str) -> None:
        assert name in CONNECTORS

    def test_get_connector_returns_the_registered_class(self) -> None:
        from mineproductivity.connectors.file import CSVConnector

        assert get_connector("csv") is CSVConnector


class TestGetConnector:
    def test_unknown_name_raises(self) -> None:
        with pytest.raises(UnregisteredLookupError):
            get_connector("not-a-real-connector")


class TestRegisterConnector:
    def test_decorator_registers_a_new_connector(self) -> None:
        @register_connector
        class _FixtureConnector(FMSConnector):
            name = "test-fixture-connector-registration"

            def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
                return iter(())

            def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
                return iter(())

        assert get_connector("test-fixture-connector-registration") is _FixtureConnector

    def test_decorator_returns_the_class_unchanged(self) -> None:
        class _Fixture(FMSConnector):
            name = "test-fixture-connector-unchanged"

            def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
                return iter(())

            def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
                return iter(())

        decorated = register_connector(_Fixture)
        assert decorated is _Fixture
