"""Append a correction to an existing event and compare the current and historical views.

Run: python examples/events/03_correction.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.events import CycleEvent, EventEnvelope, EventID, EventVersion
from mineproductivity.events.store import _InMemoryEventStore

SHIFT_START = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)


def main() -> None:
    store = _InMemoryEventStore()
    event_id = EventID.generate()

    print("--- Original ingestion (version 1) ---")
    original = CycleEvent(
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
    store.append(
        EventEnvelope(
            event_id=event_id,
            version=EventVersion(),
            payload=original,
            event_time_utc=SHIFT_START,
            processing_time_utc=SHIFT_START,
            ingestion_time_utc=SHIFT_START,
        )
    )
    print(f"stored payload_t: {store.get(event_id).payload.payload_t}")

    print()
    print("--- A weighbridge correction arrives an hour later ---")
    corrected = CycleEvent(
        equipment_id="HT-214",
        shift_id="A-2026-06-25",
        queue_min=1.5,
        spot_min=0.5,
        load_min=2.5,
        haul_min=8.0,
        dump_min=1.0,
        return_min=6.0,
        payload_t=214.5,  # the corrected reading
    )
    correction_time = SHIFT_START + timedelta(hours=1)
    store.append(
        EventEnvelope(
            event_id=event_id,  # SAME EventID -- this is a correction, not a new fact
            version=EventVersion().next_version(),  # incremented version
            payload=corrected,
            event_time_utc=SHIFT_START,  # the real-world event time is unchanged
            processing_time_utc=correction_time,
            ingestion_time_utc=correction_time,
        )
    )

    print()
    print("--- The current (latest) view resolves to the correction ---")
    print(f"store.get(event_id).payload.payload_t: {store.get(event_id).payload.payload_t}")

    print()
    print("--- The original is still retrievable for audit ---")
    original_version = store.get(event_id, as_of_version=EventVersion())
    print(
        f"store.get(event_id, as_of_version=EventVersion()).payload.payload_t: {original_version.payload.payload_t}"
    )

    print()
    print("--- Re-appending the exact same correction again is idempotent ---")
    result = store.append(
        EventEnvelope(
            event_id=event_id,
            version=EventVersion().next_version(),
            payload=corrected,
            event_time_utc=SHIFT_START,
            processing_time_utc=correction_time,
            ingestion_time_utc=correction_time,
        )
    )
    print(f"result.is_ok: {result.is_ok} (no duplicate created)")


if __name__ == "__main__":
    main()
