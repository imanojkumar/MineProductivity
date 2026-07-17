"""Lesson 04 -- Events: the immutable record everything else is derived from.

A shift report is an opinion. A haul cycle that happened at 06:14 is a
fact. MineProductivity keeps the facts -- an append-only stream of
canonical events -- and treats every KPI, twin, and dashboard as a
*projection* of that stream. Nothing is edited in place; a correction is
a new event, not a rewrite of history.

This is what makes results reproducible: you can always replay the store
"as of" a moment and get exactly the numbers that were true then.

Run: python examples/fundamentals/04_events/events.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.events import (
    AsOf,
    CycleEvent,
    EventEnvelope,
    EventID,
    EventMetadata,
    EventQuery,
    EventValidator,
    EventVersion,
)
from mineproductivity.events.store import _InMemoryEventStore

SHIFT_START = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)


def _haul_cycle(equipment_id: str, payload_t: float, haul_min: float) -> CycleEvent:
    """One truck's round trip: queue, spot, load, haul, dump, return."""
    return CycleEvent(
        equipment_id=equipment_id,
        shift_id="A-2026-06-25",
        queue_min=1.5,
        spot_min=0.5,
        load_min=2.5,
        haul_min=haul_min,
        dump_min=1.0,
        return_min=6.0,
        payload_t=payload_t,
        material_type="ore",
    )


def _envelope(cycle: CycleEvent, minute: int) -> EventEnvelope[CycleEvent]:
    """Wrap a fact in identity, version, and the mandatory three timestamps."""
    moment = SHIFT_START + timedelta(minutes=minute)
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=cycle,
        event_time_utc=moment,  # when it happened in the pit
        processing_time_utc=moment,  # when we computed on it
        ingestion_time_utc=moment,  # when it reached us
        metadata=EventMetadata(name="haul-cycle", source_system="fms"),
    )


def main() -> None:
    print("--- 1. A canonical event is a typed fact, with domain behaviour ---")
    cycle = _haul_cycle("HT-214", payload_t=220.0, haul_min=8.0)
    print(f"cycle_min : {cycle.cycle_min} (the six legs, summed by the event itself)")
    print(f"duration_h: {cycle.duration_h():.3f}")

    print()
    print("--- 2. Validation scores confidence; it does not silently drop data ---")
    outcome = EventValidator().validate_with_confidence(cycle)
    print(f"is_valid={outcome.is_valid} confidence={outcome.confidence.value}")

    print()
    print("--- 3. Append-only: the store accepts facts, it never updates them ---")
    store = _InMemoryEventStore()
    for minute, (payload, haul) in enumerate(
        [(220.0, 8.0), (218.0, 8.4), (225.0, 7.6), (212.0, 9.1)], start=14
    ):
        assert store.append(_envelope(_haul_cycle("HT-214", payload, haul), minute)).is_ok
    assert store.append(_envelope(_haul_cycle("HT-9", 198.0, 11.0), 20)).is_ok
    print("5 cycle events appended (4 for HT-214, 1 for HT-9)")

    print()
    print("--- 4. Query the facts back by scope ---")
    ht214 = list(store.query(EventQuery(equipment_ids=("HT-214",))))
    tonnes = sum(envelope.payload.payload_t for envelope in ht214)
    print(f"HT-214 moved {tonnes:.0f}t across {len(ht214)} cycles")

    print()
    print("--- 5. Time travel: what was true as of 06:18? ---")
    early = store.replay(AsOf(utc=SHIFT_START + timedelta(minutes=18)))
    early_tonnes = sum(
        envelope.payload.payload_t
        for envelope in early.envelopes
        if envelope.payload.equipment_id == "HT-214"
    )
    print(
        f"as of 06:18 HT-214 had moved {early_tonnes:.0f}t ({len(early.envelopes)} events visible)"
    )
    print("(the same query, run later, still reproduces this number exactly)")

    print()
    print("--- 6. A correction is a NEW event, never an edit ---")
    corrected = _haul_cycle("HT-214", payload_t=228.0, haul_min=8.0)
    assert store.append(_envelope(corrected, 60)).is_ok
    final = list(store.query(EventQuery(equipment_ids=("HT-214",))))
    final_tonnes = sum(envelope.payload.payload_t for envelope in final)
    print(f"HT-214 now has {len(final)} events totalling {final_tonnes:.0f}t")
    print("(the original 220.0t fact still exists -- nothing was overwritten)")

    print()
    print("--- 7. The proof: the past did not change when the present did ---")
    still_early = store.replay(AsOf(utc=SHIFT_START + timedelta(minutes=18)))
    still_early_tonnes = sum(
        envelope.payload.payload_t
        for envelope in still_early.envelopes
        if envelope.payload.equipment_id == "HT-214"
    )
    print(f"  as of 06:18 : {still_early_tonnes:.0f}t across 4 cycles  (unchanged)")
    print(f"  as of now   : {final_tonnes:.0f}t across {len(final)} cycles")
    print("Re-running the SAME as-of query after the correction returns the SAME")
    print("number. That is reproducibility: a report run today for last June")
    print("still reconciles with the report that was run last June.")


if __name__ == "__main__":
    main()
