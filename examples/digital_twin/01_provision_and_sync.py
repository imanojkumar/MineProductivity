"""The design spec §15 worked example, end-to-end: provision a
``ConveyorTwin``, cold-start it from event history via
``EventStore.replay``, then keep it live via ``EventBus.subscribe`` --
the twin's state is always a projection of the immutable event log,
never a side channel.

Run: python examples/digital_twin/01_provision_and_sync.py
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

from mineproductivity.core import InMemoryRepository, PredicateSpecification
from mineproductivity.digital_twin import (
    ConveyorTwin,
    SyncPolicy,
    Twin,
    TwinContext,
    TwinMetadata,
    TwinCategory,
    TwinState,
    TwinStatus,
    TwinSynchronizer,
)
from mineproductivity.events import (
    AsOf,
    BaseEvent,
    EventEnvelope,
    EventID,
    EventMetadata,
    EventVersion,
    ProductionEvent,
)
from mineproductivity.events.bus import _InMemoryEventBus
from mineproductivity.events.store import _InMemoryEventStore

GENESIS = datetime(2026, 7, 8, 6, 0, tzinfo=timezone.utc)


class BeltConveyorTwin(ConveyorTwin):
    """A belt conveyor's live condition, projected from the
    ``ProductionEvent`` stream: cumulative tonnes carried and how many
    events have been folded in."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="CONVEYOR.Belt",
        category=TwinCategory.CONVEYOR,
        description="A belt conveyor twin projected from production events.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        if not events:
            return self.state
        tonnes = float(self.state.attributes.get("tonnes_carried", 0.0))
        seen = int(self.state.attributes.get("events_seen", 0))
        for event in events:
            if isinstance(event, ProductionEvent):
                tonnes += event.tonnes_moved
                seen += 1
        return TwinState(
            attributes={"tonnes_carried": tonnes, "events_seen": seen},
            captured_at=GENESIS + timedelta(minutes=seen),
        )


def _envelope(equipment_id: str, tonnes: float, minute: int) -> EventEnvelope[ProductionEvent]:
    moment = GENESIS + timedelta(minutes=minute)
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=ProductionEvent(
            equipment_id=equipment_id,
            shift_id="A",
            pit_code="north",
            material_type="ore",
            tonnes_moved=tonnes,
            planned_tonnes=tonnes,
            operating_h=0.2,
        ),
        event_time_utc=moment,
        processing_time_utc=moment,
        ingestion_time_utc=moment,
        metadata=EventMetadata(name="production", source_system="plant-historian"),
    )


def main() -> None:
    print("--- 1. The immutable event log already holds CONV-7's history ---")
    bus = _InMemoryEventBus()
    store = _InMemoryEventStore(bus=bus)  # appends publish to the bus, end to end
    for minute, tonnes in enumerate((410.0, 385.0, 402.0), start=1):
        assert store.append(_envelope("CONV-7", tonnes, minute)).is_ok
    assert store.append(_envelope("CONV-9", 500.0, 4)).is_ok  # a different conveyor
    print("4 production events appended (3 for CONV-7, 1 for CONV-9)")

    print()
    print("--- 2. A SyncPolicy narrows delivery to the events this twin reads ---")
    sync_policy = SyncPolicy(
        mode="realtime",
        event_filter=PredicateSpecification(
            lambda envelope: bool(envelope.payload.equipment_id == "CONV-7")
        ),
    )
    print(f"policy: {sync_policy.mode!r}, filter on equipment_id == 'CONV-7'")

    print()
    print("--- 3. Cold start: reconstruct the twin from genesis via replay ---")
    context = TwinContext(event_store=store)
    handle = store.replay(AsOf(utc=GENESIS + timedelta(hours=1)))
    relevant = [
        envelope.payload
        for envelope in handle.envelopes
        if sync_policy.event_filter.is_satisfied_by(envelope)
    ]
    twin: Twin = BeltConveyorTwin(
        id="CONV-7",
        scope={"equipment_id": "CONV-7", "pit": "north"},
        state=TwinState(attributes={"tonnes_carried": 0.0, "events_seen": 0}, captured_at=GENESIS),
    )
    twin = twin.with_state(twin._apply(relevant, context=context), status=TwinStatus.SYNCHRONIZED)
    print(
        f"replayed {len(relevant)} relevant event(s) -> "
        f"tonnes_carried={twin.state.attributes['tonnes_carried']}"
    )

    repository: InMemoryRepository[Twin, str] = InMemoryRepository()
    repository.add(twin)

    print()
    print("--- 4. Live: subscribe and let TwinSynchronizer take over ---")
    synchronizer = TwinSynchronizer(repository=repository)

    def on_event(envelope: EventEnvelope[Any]) -> None:
        result = synchronizer.synchronize("CONV-7", [envelope.payload], context=context)
        print(
            f"synchronized: {result.previous_status.value} -> {result.new_status.value},"
            f" events_applied={result.events_applied}"
        )

    subscription = bus.subscribe(sync_policy.event_filter, on_event)
    assert store.append(_envelope("CONV-7", 395.0, 90)).is_ok  # live event arrives
    assert store.append(_envelope("CONV-9", 512.0, 91)).is_ok  # filtered out

    current = repository.get("CONV-7")
    print(
        f"current state: tonnes_carried={current.state.attributes['tonnes_carried']}"
        f" events_seen={current.state.attributes['events_seen']}"
    )

    print()
    print("--- 5. The twin instance read before the live event is untouched ---")
    print(f"cold-start instance still says: {twin.state.attributes['tonnes_carried']}")
    print("(state changes produce new instances; identity-based equality holds:")
    print(f" cold-start twin == current twin -> {twin == current})")

    subscription.cancel()
    print()
    print("--- 6. Cancelled: later events no longer reach the twin ---")
    assert store.append(_envelope("CONV-7", 401.0, 95)).is_ok
    print(f"events_seen after cancel: {repository.get('CONV-7').state.attributes['events_seen']}")


if __name__ == "__main__":
    main()
