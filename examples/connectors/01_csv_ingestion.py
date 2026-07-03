"""End-to-end CSV ingestion: CSVConnector -> EventValidator -> EventStore
-> query, mirroring design spec §31's worked example.

Run: python examples/connectors/01_csv_ingestion.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from mineproductivity.connectors import CONNECTORS, CSVConnector, get_connector
from mineproductivity.events import EventEnvelope, EventID, EventQuery, EventValidator, EventVersion
from mineproductivity.events.store import _InMemoryEventStore

_FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "connectors"


def main() -> None:
    print("--- 1. Every reference connector is registered by default ---")
    print(f'"csv" in CONNECTORS: {"csv" in CONNECTORS}')
    print(f"registered connectors: {sorted(CONNECTORS)}")

    print()
    print("--- 2. Look up and construct a connector by name ---")
    # get_connector() returns type[FMSConnector] -- the generic contract
    # every connector shares. Constructing one requires knowing its
    # concrete constructor signature, which the caller supplies here by
    # name (mirroring design spec §31's example exactly).
    connector_cls = cast("type[CSVConnector]", get_connector("csv"))
    connector = connector_cls(
        path=_FIXTURES_DIR / "cycle_events.csv",
        shift_id="A-2026-06-25",
        delay_path=_FIXTURES_DIR / "delay_events.csv",
    )

    since = datetime(2026, 6, 25, tzinfo=timezone.utc)
    until = datetime(2026, 6, 26, tzinfo=timezone.utc)

    print()
    print("--- 3. Pull canonical events -- the connector never exposes raw CSV rows ---")
    cycles = list(connector.get_cycle_data(since, until))
    print(f"{len(cycles)} cycle events | first payload_t: {cycles[0].payload_t}")

    print()
    print("--- 4. health_check() reports HEALTHY after a successful pull ---")
    print(connector.health_check().status)

    print()
    print("--- 5. Contextually validate, envelope, and durably append each event ---")
    validator = EventValidator()
    store = _InMemoryEventStore()
    for i, cycle in enumerate(cycles):
        outcome = validator.validate_with_confidence(cycle)
        event_time = since.replace(hour=6, minute=i * 15)
        envelope = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=cycle,
            event_time_utc=event_time,
            processing_time_utc=event_time,
            ingestion_time_utc=event_time,
        )
        store.append(envelope)
    print(f"appended {len(cycles)} events, confidence of the last: {outcome.confidence.value}")

    print()
    print("--- 6. Query it back, scoped by equipment ---")
    ht214_events = list(store.query(EventQuery(equipment_ids=("HT-214",))))
    print(
        f"HT-214: {len(ht214_events)} event(s), payloads: {[e.payload.payload_t for e in ht214_events]}"
    )


if __name__ == "__main__":
    main()
