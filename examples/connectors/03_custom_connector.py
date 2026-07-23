"""Extension point: implement the ``FMSConnector`` contract for a new source.

Every data source -- a vendor FMS, a CSV export, or (here) an in-memory
dispatch log -- becomes platform-ready by implementing one small abstract
base class and registering it with ``@register_connector``. It then appears
in the ``CONNECTORS`` registry and is constructible via ``get_connector()``,
exactly like the six built-in reference connectors, and yields the same
canonical ``events`` every other connector does.

Run: python examples/connectors/03_custom_connector.py
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar

from mineproductivity.connectors import (
    CONNECTORS,
    ConnectorHealth,
    FMSConnector,
    HealthStatus,
    IngestionMode,
    get_connector,
    register_connector,
)
from mineproductivity.events import CycleEvent, DelayEvent


@dataclass(frozen=True)
class _DispatchRecord:
    equipment_id: str
    event_time: datetime
    payload_t: float


# A tiny in-memory "dispatch log" standing in for a real source system.
_DISPATCH_LOG: tuple[_DispatchRecord, ...] = (
    _DispatchRecord("HT-214", datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc), 220.0),
    _DispatchRecord("HT-214", datetime(2026, 6, 25, 6, 20, tzinfo=timezone.utc), 218.0),
    _DispatchRecord("HT-215", datetime(2026, 6, 25, 7, 30, tzinfo=timezone.utc), 225.0),
)


@register_connector
class DispatchLogConnector(FMSConnector):
    """A minimal custom connector over an in-memory dispatch log."""

    name: ClassVar[str] = "dispatch_log"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (
        IngestionMode.BATCH,
        IngestionMode.INCREMENTAL,
    )

    def __init__(self, *, shift_id: str) -> None:
        self._shift_id = shift_id
        self._pulled = False

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterable[CycleEvent]:
        # A lazy generator honoring the half-open [since, until) window --
        # never a materialized list (the contract's one hard rule).
        for record in _DISPATCH_LOG:
            if since <= record.event_time < until:
                yield CycleEvent(
                    equipment_id=record.equipment_id,
                    shift_id=self._shift_id,
                    queue_min=1.5,
                    spot_min=0.5,
                    load_min=2.5,
                    haul_min=8.0,
                    dump_min=1.0,
                    return_min=6.0,
                    payload_t=record.payload_t,
                )
        self._pulled = True

    def get_delay_data(self, since: datetime, until: datetime) -> Iterable[DelayEvent]:
        return iter(())  # this source carries no delay telemetry

    def health_check(self) -> ConnectorHealth:
        status = HealthStatus.HEALTHY if self._pulled else HealthStatus.UNKNOWN
        return ConnectorHealth(status=status)


def main() -> None:
    print("--- 1. The custom connector registered itself alongside the built-ins ---")
    print(f'"dispatch_log" in CONNECTORS: {"dispatch_log" in CONNECTORS}')
    print(f"registered connectors: {sorted(CONNECTORS)}")

    print()
    print("--- 2. Discoverable by name via get_connector(), like any built-in ---")
    print(
        f"get_connector('dispatch_log') is DispatchLogConnector: {get_connector('dispatch_log') is DispatchLogConnector}"
    )
    print(f"provided_event_types(): {DispatchLogConnector.provided_event_types()}")

    print()
    print("--- 3. It yields the SAME canonical events every connector does ---")
    connector = DispatchLogConnector(shift_id="A-2026-06-25")
    since = datetime(2026, 6, 25, tzinfo=timezone.utc)
    until = datetime(2026, 6, 25, 7, 0, tzinfo=timezone.utc)  # excludes the 07:30 record
    cycles = list(connector.get_cycle_data(since, until))
    print(
        f"pulled {len(cycles)} cycle events in [06:00, 07:00): payloads={[c.payload_t for c in cycles]}"
    )
    print(f"health after pull: {connector.health_check().status}")


if __name__ == "__main__":
    main()
