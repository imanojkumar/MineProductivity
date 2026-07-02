"""Construct, validate, and append your first event.

Run: python examples/events/01_first_event.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.events import (
    CycleEvent,
    EventEnvelope,
    EventID,
    EventMetadata,
    EventQuery,
    EventValidator,
    EventVersion,
)
from mineproductivity.events.store import _InMemoryEventStore


def main() -> None:
    print("--- Construct a CycleEvent ---")
    cycle = CycleEvent(
        equipment_id="HT-214",
        shift_id="A-2026-06-25",
        queue_min=1.5,
        spot_min=0.5,
        load_min=2.5,
        haul_min=8.0,
        dump_min=1.0,
        return_min=6.0,
        payload_t=220.0,
    )
    print(f"cycle_min: {cycle.cycle_min}")
    print(f"duration_h: {cycle.duration_h():.3f}")

    print()
    print("--- Contextual validation + confidence scoring ---")
    validator = EventValidator()
    outcome = validator.validate_with_confidence(cycle)
    print(f"is_valid: {outcome.is_valid}, confidence: {outcome.confidence.value}")

    print()
    print("--- Wrap in an EventEnvelope (identity, version, three timestamps) ---")
    now = datetime.now(timezone.utc)
    envelope = EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=cycle,
        event_time_utc=now,
        processing_time_utc=now,
        ingestion_time_utc=now,
        metadata=EventMetadata(
            name="cycle-ingest", source_system="csv", confidence=outcome.confidence.value
        ),
    )
    print(f"event_id: {envelope.event_id.value}")

    print()
    print("--- Append to an EventStore ---")
    store = _InMemoryEventStore()
    result = store.append(envelope)
    print(f"append result -> is_ok: {result.is_ok}")

    print()
    print("--- Query it back ---")
    results = list(store.query(EventQuery(equipment_ids=("HT-214",))))
    print(f"found {len(results)} event(s) for HT-214: payload_t={results[0].payload.payload_t}")


if __name__ == "__main__":
    main()
