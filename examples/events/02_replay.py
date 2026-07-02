"""Append events across a shift, then time-travel back with replay().

Run: python examples/events/02_replay.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.events import AsOf, CycleEvent, EventEnvelope, EventID, EventVersion
from mineproductivity.events.store import _InMemoryEventStore

SHIFT_START = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)


def cycle_at(minute: int, payload_t: float) -> CycleEvent:
    return CycleEvent(
        equipment_id="HT-214",
        shift_id="A-2026-06-25",
        queue_min=1.5,
        spot_min=0.5,
        load_min=2.5,
        haul_min=8.0,
        dump_min=1.0,
        return_min=6.0,
        payload_t=payload_t,
    )


def main() -> None:
    store = _InMemoryEventStore()

    print("--- Ingesting three cycles across a shift ---")
    for minute, payload_t in [(0, 220.0), (20, 218.0), (40, 225.0)]:
        event_time = SHIFT_START + timedelta(minutes=minute)
        envelope = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=cycle_at(minute, payload_t),
            event_time_utc=event_time,
            processing_time_utc=event_time,
            ingestion_time_utc=event_time,
        )
        store.append(envelope)
        print(f"appended cycle at t+{minute}min, payload_t={payload_t}")

    print()
    print("--- Replay at t+15min: only the first cycle had happened ---")
    checkpoint = store.replay(AsOf(utc=SHIFT_START + timedelta(minutes=15)))
    print(f"{len(checkpoint.envelopes)} event(s) visible")
    for envelope in checkpoint.envelopes:
        print(f"  payload_t={envelope.payload.payload_t}")

    print()
    print("--- Replay at t+60min: all three cycles had happened ---")
    end_of_shift = store.replay(AsOf(utc=SHIFT_START + timedelta(minutes=60)))
    print(f"{len(end_of_shift.envelopes)} event(s) visible")

    print()
    print("--- Snapshot: a materialized checkpoint for accelerating future replay ---")
    snapshot = store.snapshot(AsOf(utc=SHIFT_START + timedelta(minutes=45)))
    print(f"snapshot holds {len(snapshot.state)} event(s) as of its checkpoint")


if __name__ == "__main__":
    main()
