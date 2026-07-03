"""Tests for mineproductivity.connectors.contract_tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.connectors.base import FMSConnector
from mineproductivity.connectors.contract_tests import run_fms_contract_suite
from mineproductivity.connectors.exceptions import ContractViolationError
from mineproductivity.connectors.health import ConnectorHealth, HealthStatus

_SINCE = datetime(2026, 6, 25, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, tzinfo=timezone.utc)


class _GoodConnector(FMSConnector):
    name = "good"

    def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
        yield from ()

    def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
        yield from ()


class _EmptyNameConnector(FMSConnector):
    name = ""

    def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())

    def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())


class _ListReturningConnector(FMSConnector):
    name = "list-returning"

    def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
        return []

    def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())


class _ListReturningDelayConnector(FMSConnector):
    name = "list-returning-delay"

    def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())

    def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
        return []


class _NonIterableConnector(FMSConnector):
    name = "non-iterable"

    def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
        return object()

    def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())


class _BadHealthCheckConnector(FMSConnector):
    name = "bad-health"

    def get_cycle_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())

    def get_delay_data(self, since, until):  # type: ignore[no-untyped-def]
        return iter(())

    def health_check(self):  # type: ignore[no-untyped-def]
        return "not a ConnectorHealth"


class TestRunFmsContractSuite:
    def test_passes_for_a_well_behaved_connector(self) -> None:
        run_fms_contract_suite(
            _GoodConnector,
            since=_SINCE,
            until=_UNTIL,
            expected_cycle_count=0,
            expected_delay_count=0,
        )

    def test_rejects_empty_name(self) -> None:
        with pytest.raises(ContractViolationError, match="name"):
            run_fms_contract_suite(_EmptyNameConnector, since=_SINCE, until=_UNTIL)

    def test_rejects_non_iterable_returned_from_get_cycle_data(self) -> None:
        with pytest.raises(ContractViolationError, match="must return an Iterable"):
            run_fms_contract_suite(_NonIterableConnector, since=_SINCE, until=_UNTIL)

    def test_rejects_list_returned_from_get_cycle_data(self) -> None:
        with pytest.raises(ContractViolationError, match="get_cycle_data"):
            run_fms_contract_suite(_ListReturningConnector, since=_SINCE, until=_UNTIL)

    def test_rejects_list_returned_from_get_delay_data(self) -> None:
        with pytest.raises(ContractViolationError, match="get_delay_data"):
            run_fms_contract_suite(_ListReturningDelayConnector, since=_SINCE, until=_UNTIL)

    def test_rejects_unexpected_cycle_count(self) -> None:
        with pytest.raises(ContractViolationError, match="expected 5"):
            run_fms_contract_suite(
                _GoodConnector, since=_SINCE, until=_UNTIL, expected_cycle_count=5
            )

    def test_rejects_unexpected_delay_count(self) -> None:
        with pytest.raises(ContractViolationError, match="expected 5"):
            run_fms_contract_suite(
                _GoodConnector, since=_SINCE, until=_UNTIL, expected_delay_count=5
            )

    def test_no_expected_count_skips_count_assertion(self) -> None:
        run_fms_contract_suite(_GoodConnector, since=_SINCE, until=_UNTIL)

    def test_rejects_malformed_health_check_return(self) -> None:
        with pytest.raises(ContractViolationError, match="health_check"):
            run_fms_contract_suite(_BadHealthCheckConnector, since=_SINCE, until=_UNTIL)

    def test_connector_health_still_a_valid_shape(self) -> None:
        conn = _GoodConnector()
        assert isinstance(conn.health_check(), ConnectorHealth)
        assert conn.health_check().status is HealthStatus.UNKNOWN
