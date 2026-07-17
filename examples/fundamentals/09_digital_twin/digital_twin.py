"""Lesson 09 -- Digital Twin: live state that is always a projection.

A "digital twin" in most vendor decks is a dashboard with a 3D model. In
MineProductivity it is something stricter and more useful: an entity whose
state is *always a projection of the immutable event log*, never a side
channel someone can write to directly.

That constraint buys two things a mine actually needs. Cold start: a twin
lost to a restart is rebuilt exactly by replaying history. Auditability:
every tonne on the stockpile traces to an event that says where it came
from. If state could be poked directly, neither would hold.

This lesson builds a ROM stockpile twin fed by the crusher's production
events.

Run: python examples/fundamentals/09_digital_twin/digital_twin.py
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

from mineproductivity.core import InMemoryRepository, PredicateSpecification
from mineproductivity.digital_twin import (
    StockpileTwin,
    Twin,
    TwinCategory,
    TwinContext,
    TwinMetadata,
    TwinSnapshot,
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

GENESIS = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)
STOCKPILE_ID = "ROM-01"


class RomStockpileTwin(StockpileTwin):
    """A run-of-mine stockpile's live condition, projected from the
    production events that tip onto it: tonnes on the pad and how many
    tips have been folded in.

    Note there is no `add_tonnes()` method. The ONLY way this twin's state
    changes is by applying events. That is the whole point.
    """

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="STOCKPILE.RunOfMine",
        category=TwinCategory.STOCKPILE,
        description="A ROM stockpile twin projected from production events.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        if not events:
            return self.state
        tonnes = float(self.state.attributes.get("tonnes_on_pad", 0.0))
        tips = int(self.state.attributes.get("tips", 0))
        for event in events:
            if isinstance(event, ProductionEvent):
                tonnes += event.tonnes_moved
                tips += 1
        return TwinState(
            attributes={"tonnes_on_pad": tonnes, "tips": tips},
            captured_at=GENESIS + timedelta(minutes=tips),
        )


def _tip(equipment_id: str, tonnes: float, minute: int) -> EventEnvelope[ProductionEvent]:
    """One truck tipping its load onto the ROM pad."""
    moment = GENESIS + timedelta(minutes=minute)
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=ProductionEvent(
            equipment_id=equipment_id,
            shift_id="A-2026-06-25",
            pit_code="pit-west",
            material_type="ore",
            tonnes_moved=tonnes,
            planned_tonnes=tonnes,
            operating_h=0.25,
        ),
        event_time_utc=moment,
        processing_time_utc=moment,
        ingestion_time_utc=moment,
        metadata=EventMetadata(name="rom-tip", source_system="fms"),
    )


def main() -> None:
    print("--- 1. The event log already holds this shift's tips ---")
    bus = _InMemoryEventBus()
    store = _InMemoryEventStore(bus=bus)  # appends publish to the bus
    for minute, (truck, tonnes) in enumerate(
        [("HT-214", 220.0), ("HT-215", 218.0), ("HT-214", 225.0)], start=10
    ):
        assert store.append(_tip(truck, tonnes, minute)).is_ok
    assert store.append(_tip("HT-9", 198.0, 15)).is_ok  # tips on a DIFFERENT pad
    print("4 production events appended (3 to ROM-01's trucks, 1 elsewhere)")

    print()
    print("--- 2. Cold start: rebuild the twin from history via replay ---")
    context = TwinContext(event_store=store)
    only_our_trucks: PredicateSpecification[EventEnvelope[Any]] = PredicateSpecification(
        lambda envelope: bool(envelope.payload.equipment_id in {"HT-214", "HT-215"})
    )
    handle = store.replay(AsOf(utc=GENESIS + timedelta(hours=1)))
    relevant = [env.payload for env in handle.envelopes if only_our_trucks.is_satisfied_by(env)]

    # Provision the twin at genesis (empty pad), then let the PUBLIC
    # TwinSynchronizer fold the replayed history into it. The synchronizer is
    # the public contract for applying events -- _apply() is the extension
    # point you implement, not the API you call.
    repository: InMemoryRepository[Twin, str] = InMemoryRepository()
    repository.add(
        RomStockpileTwin(
            id=STOCKPILE_ID,
            scope={"stockpile": STOCKPILE_ID, "pit": "pit-west"},
            state=TwinState(attributes={"tonnes_on_pad": 0.0, "tips": 0}, captured_at=GENESIS),
        )
    )
    synchronizer = TwinSynchronizer(repository=repository)
    cold_start = synchronizer.synchronize(STOCKPILE_ID, relevant, context=context)
    twin: Twin = repository.get(STOCKPILE_ID)
    print(
        f"replayed {len(relevant)} relevant events"
        f" (applied={cold_start.events_applied}) -> {twin.state.attributes}"
    )
    print(f"status: {cold_start.previous_status.value} -> {cold_start.new_status.value}")
    print("(a twin lost to a restart is reconstructed EXACTLY -- no state was")
    print(" stored anywhere but the event log)")

    print()
    print("--- 3. Go live: the synchronizer folds in new events as they land ---")

    def on_event(envelope: EventEnvelope[Any]) -> None:
        result = synchronizer.synchronize(STOCKPILE_ID, [envelope.payload], context=context)
        print(
            f"  synced: {result.previous_status.value} -> {result.new_status.value},"
            f" events_applied={result.events_applied}"
        )

    subscription = bus.subscribe(only_our_trucks, on_event)
    assert store.append(_tip("HT-215", 231.0, 40)).is_ok  # lands on ROM-01
    assert store.append(_tip("HT-9", 205.0, 41)).is_ok  # filtered out

    current = repository.get(STOCKPILE_ID)
    print(f"live state: {current.state.attributes}")

    print()
    print("--- 4. Immutability: the cold-start instance never changed ---")
    print(f"cold-start instance still reads: {twin.state.attributes['tonnes_on_pad']:,.0f} t")
    print(f"repository instance now reads  : {current.state.attributes['tonnes_on_pad']:,.0f} t")
    print(f"but they are the SAME twin: twin == current -> {twin == current}")
    print("(identity-based equality again -- ROM-01 is ROM-01; state changes")
    print(" produce new instances, exactly like the entity in lesson 02)")

    print()
    print("--- 5. A snapshot freezes 'what was true' at a point in time ---")
    snapshot = TwinSnapshot(
        twin_id=STOCKPILE_ID,
        state=current.state,
        status=TwinStatus.SYNCHRONIZED,
        as_of=AsOf(utc=GENESIS + timedelta(hours=2)),
    )
    as_of_utc = snapshot.as_of.utc
    assert as_of_utc is not None  # AsOf.utc is optional; this snapshot pins a moment
    print(f"snapshot of {snapshot.twin_id} as_of {as_of_utc.isoformat()}")
    print(f"  {dict(snapshot.state.attributes)}")
    print("(this is what simulation and optimization seed from -- a real")
    print(" starting condition, not a hand-typed guess)")

    subscription.cancel()
    assert store.append(_tip("HT-214", 219.0, 90)).is_ok
    print()
    print("--- 6. Cancelled: later events no longer reach the twin ---")
    print(f"tips after cancel: {repository.get(STOCKPILE_ID).state.attributes['tips']}")
    print("(the event is still in the log forever -- the twin simply stopped")
    print(" listening. History and projection are separate concerns.)")


if __name__ == "__main__":
    main()
