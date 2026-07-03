"""``run_fms_contract_suite``: the shared, parameterizable structural
contract every :class:`~mineproductivity.connectors.base.FMSConnector`
implementation -- built-in or plugin -- is expected to pass before it is
trusted with a live source (design spec §9, §19, §29).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from mineproductivity.connectors.base import FMSConnector
from mineproductivity.connectors.exceptions import ContractViolationError
from mineproductivity.connectors.health import ConnectorHealth

__all__ = ["run_fms_contract_suite"]


def run_fms_contract_suite(
    connector_factory: Callable[[], FMSConnector],
    *,
    since: datetime,
    until: datetime,
    expected_cycle_count: int | None = None,
    expected_delay_count: int | None = None,
) -> None:
    """Run one connector through the shared structural contract: a
    non-empty ``name``, a lazy ``Iterable`` (never a materialized list)
    from every ``get_*_data`` call, the requested ``[since, until)``
    window respected (when the caller supplies ``expected_*_count``
    against fixture data arranged to make that count meaningful), and
    ``health_check()`` returning a well-formed :class:`ConnectorHealth`.

    Malformed-record degradation (one bad record must not abort the
    generator) is proven by arranging fixture data with a known-bad
    record alongside the well-formed ones counted in
    ``expected_*_count`` -- if the connector under test crashes instead
    of skipping the bad record, this function's own iteration raises,
    failing the caller's test naturally without any special-casing here.

    Raises
    ------
    ContractViolationError
        If the connector under test violates any part of the contract.
    """
    connector = connector_factory()

    if not connector.name or not isinstance(connector.name, str):
        raise ContractViolationError(f"{type(connector).__name__}.name must be a non-empty string")

    _check_lazy_and_count(
        connector.get_cycle_data(since, until),
        type(connector).__name__,
        "get_cycle_data",
        expected_cycle_count,
    )
    _check_lazy_and_count(
        connector.get_delay_data(since, until),
        type(connector).__name__,
        "get_delay_data",
        expected_delay_count,
    )

    health = connector.health_check()
    if not isinstance(health, ConnectorHealth):
        raise ContractViolationError(
            f"{type(connector).__name__}.health_check() must return a ConnectorHealth, "
            f"got {type(health).__name__}"
        )


def _check_lazy_and_count(
    result: Iterable[Any], connector_name: str, method_name: str, expected_count: int | None
) -> None:
    if isinstance(result, (list, tuple)):
        raise ContractViolationError(
            f"{connector_name}.{method_name}() must return a lazy Iterable, not a "
            f"materialized {type(result).__name__}"
        )
    if not hasattr(result, "__iter__"):
        raise ContractViolationError(f"{connector_name}.{method_name}() must return an Iterable")

    events = list(result)
    if expected_count is not None and len(events) != expected_count:
        raise ContractViolationError(
            f"{connector_name}.{method_name}() yielded {len(events)} event(s) within the "
            f"requested window, expected {expected_count}"
        )
