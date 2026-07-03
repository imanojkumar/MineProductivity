"""``IngestionMode``/``FMSConnector``: the one small contract every data
source -- a fleet-management system, a CSV export, a REST API, a Kafka
topic -- must satisfy to feed the platform.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from typing import ClassVar

from mineproductivity.events import (
    ConsumptionEvent,
    CycleEvent,
    DelayEvent,
    MaintenanceEvent,
    ProductionEvent,
    SafetyEvent,
)

from mineproductivity.connectors.health import ConnectorHealth, HealthStatus

__all__ = ["FMSConnector", "IngestionMode"]

_DEFAULT_METHOD_NAMES = (
    "get_cycle_data",
    "get_delay_data",
    "get_maintenance_data",
    "get_production_data",
    "get_consumption_data",
    "get_safety_data",
)


class IngestionMode(Enum):
    """The three ways a caller can drive an :class:`FMSConnector`."""

    BATCH = "batch"
    INCREMENTAL = "incremental"
    STREAMING = "streaming"


class FMSConnector(ABC):
    """Adapter from a fleet-management (or any other) source to canonical
    events. This is the entire contract every source-specific adapter
    implements -- deliberately small (Cookbook Part I, Ch. 7: "Every
    connector implements one small abstract base class").

    Only :meth:`get_cycle_data` and :meth:`get_delay_data` are abstract
    (design spec AD-CN-01); the remaining four ``get_*_data`` methods
    have no-op defaults so a source that only produces cycles is not
    forced to implement methods it has nothing to yield for.

    Every ``get_*_data`` implementation MUST be a generator or otherwise
    lazy ``Iterable`` -- never a materialized list (Cookbook Part I, Ch.
    7's Python Insight: "the same connector handles a 200-row test file
    or a 50-million-row shift export"). This is mechanically checked by
    :func:`~mineproductivity.connectors.contract_tests.run_fms_contract_suite`.
    """

    name: ClassVar[str] = "abstract"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (IngestionMode.BATCH,)

    @abstractmethod
    def get_cycle_data(self, since: datetime, until: datetime) -> Iterable[CycleEvent]:
        """Yield :class:`CycleEvent`\\ s whose source timestamp falls in
        ``[since, until)``."""

    @abstractmethod
    def get_delay_data(self, since: datetime, until: datetime) -> Iterable[DelayEvent]:
        """Yield :class:`DelayEvent`\\ s whose source timestamp falls in
        ``[since, until)``."""

    def get_maintenance_data(self, since: datetime, until: datetime) -> Iterable[MaintenanceEvent]:
        """Optional: default implementation yields nothing. Override for
        sources that carry maintenance telemetry."""
        return iter(())

    def get_production_data(self, since: datetime, until: datetime) -> Iterable[ProductionEvent]:
        """Optional: default implementation yields nothing."""
        return iter(())

    def get_consumption_data(self, since: datetime, until: datetime) -> Iterable[ConsumptionEvent]:
        """Optional: default implementation yields nothing."""
        return iter(())

    def get_safety_data(self, since: datetime, until: datetime) -> Iterable[SafetyEvent]:
        """Optional: default implementation yields nothing."""
        return iter(())

    def health_check(self) -> ConnectorHealth:
        """Default: assumes healthy state is unknown until a real pull
        happens. Override for sources with a real liveness/auth check."""
        return ConnectorHealth(status=HealthStatus.UNKNOWN)

    @classmethod
    def provided_event_types(cls) -> tuple[str, ...]:
        """Which of the six ``get_*_data`` methods this class actually
        overrides (as opposed to inheriting :class:`FMSConnector`'s
        no-op default), so discovery/documentation tooling can report
        what a connector is good for without instantiating it (design
        spec §18)."""
        provided = []
        for method_name in _DEFAULT_METHOD_NAMES:
            if getattr(cls, method_name) is not getattr(FMSConnector, method_name):
                provided.append(method_name.removeprefix("get_").removesuffix("_data"))
        return tuple(provided)
