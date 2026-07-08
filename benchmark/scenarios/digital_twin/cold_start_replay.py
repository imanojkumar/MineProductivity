"""Benchmark scenario: cold-start replay cost vs. event-history length,
with and without snapshot acceleration (Digital Twin implementation
checklist, Benchmarks).

Standalone by design -- the ``mineproductivity.benchmark`` harness
package is not yet implemented (see ``benchmark/README.md``), so this
scenario is a plain script, mirroring
``benchmark/scenarios/decision/``'s established posture. Results are
recorded in ``benchmark/reports/digital_twin/``.

Two paths are measured per history length (design spec §15, §33):

- **full replay** -- ``EventStore.replay(as_of)`` from genesis, folding
  every relevant envelope through ``Twin._apply``. The reference
  ``_InMemoryEventStore.replay`` performs no ``EventSnapshot``
  acceleration of its own (§33: ``digital_twin`` "inherits whatever
  replay-acceleration the ``EventStore`` implementation already
  provides" -- for the in-memory reference, that is none), so this is
  the honest un-accelerated bound.
- **snapshot-seeded catch-up** -- restore from a ``TwinSnapshot`` taken
  at the 90% point of history, then fold only the remaining 10% tail
  via ``EventStore.query`` -- the twin-level acceleration §13's
  simulation-forking/audit use case exists to enable.

Run: python benchmark/scenarios/digital_twin/cold_start_replay.py
"""

from __future__ import annotations

import platform
import time
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import ClassVar

from mineproductivity.digital_twin import (
    EquipmentTwin,
    Twin,
    TwinCategory,
    TwinContext,
    TwinMetadata,
    TwinSnapshot,
    TwinState,
    TwinStatus,
)
from mineproductivity.events import (
    AsOf,
    BaseEvent,
    CycleEvent,
    EventEnvelope,
    EventID,
    EventMetadata,
    EventQuery,
    EventVersion,
)
from mineproductivity.events.store import _InMemoryEventStore

_GENESIS = datetime(2026, 1, 1, tzinfo=timezone.utc)

HISTORY_LENGTHS = (1_000, 10_000, 50_000)


class _CycleCountTwin(EquipmentTwin):
    """Counts cycle events folded into it -- deterministic on the
    cumulative count, so every reconstruction path converges."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="EQUIPMENT.ReplayBench",
        category=TwinCategory.EQUIPMENT,
        description="Counts cycle events folded into it.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        if not events:
            return self.state
        seen = int(self.state.attributes.get("cycles_seen", 0)) + len(events)
        return TwinState(
            attributes={"cycles_seen": seen},
            captured_at=_GENESIS + timedelta(seconds=seen),
        )


def _envelope(index: int) -> EventEnvelope[CycleEvent]:
    moment = _GENESIS + timedelta(seconds=index)
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=CycleEvent(
            equipment_id="EQ-1",
            shift_id="A",
            queue_min=1.0,
            spot_min=0.5,
            load_min=2.0,
            haul_min=8.0,
            dump_min=1.0,
            return_min=6.0,
            payload_t=220.0,
        ),
        event_time_utc=moment,
        processing_time_utc=moment,
        ingestion_time_utc=moment,
        metadata=EventMetadata(name="cycle", source_system="bench"),
    )


def _fresh_twin() -> Twin:
    return _CycleCountTwin(
        id="EQ-1",
        scope={"equipment_id": "EQ-1"},
        state=TwinState(attributes={"cycles_seen": 0}, captured_at=_GENESIS),
    )


def main() -> None:
    print("Cold-start reconstruction cost vs. event-history length")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print()
    print(f"{'events':>7} {'full_replay_ms':>15} {'snapshot_seeded_ms':>19} {'speedup':>8}")

    for length in HISTORY_LENGTHS:
        store = _InMemoryEventStore()
        for index in range(length):
            assert store.append(_envelope(index)).is_ok
        as_of = AsOf(utc=_GENESIS + timedelta(seconds=length + 1))
        context = TwinContext(event_store=store, as_of=as_of)

        # Path 1: full replay from genesis.
        start = time.perf_counter()
        handle = store.replay(as_of)
        twin = _fresh_twin()
        twin = twin.with_state(
            twin._apply([envelope.payload for envelope in handle.envelopes], context=context),
            status=TwinStatus.SYNCHRONIZED,
        )
        full_seconds = time.perf_counter() - start
        assert twin.state.attributes["cycles_seen"] == length

        # Path 2: restore from a TwinSnapshot at the 90% point, then
        # fold only the tail via a bounded EventStore.query.
        cut = int(length * 0.9)
        snapshot = TwinSnapshot(
            twin_id="EQ-1",
            state=TwinState(
                attributes={"cycles_seen": cut},
                captured_at=_GENESIS + timedelta(seconds=cut),
            ),
            status=TwinStatus.SYNCHRONIZED,
            as_of=AsOf(utc=_GENESIS + timedelta(seconds=cut)),
        )
        start = time.perf_counter()
        restored = _fresh_twin().with_state(snapshot.state, status=snapshot.status)
        tail = [
            envelope.payload for envelope in store.query(EventQuery(since_utc=snapshot.as_of.utc))
        ]
        restored = restored.with_state(
            restored._apply(tail, context=context), status=TwinStatus.SYNCHRONIZED
        )
        seeded_seconds = time.perf_counter() - start
        assert restored.state.attributes["cycles_seen"] == length

        print(
            f"{length:>7} {full_seconds * 1e3:>15.2f} {seeded_seconds * 1e3:>19.2f}"
            f" {full_seconds / seeded_seconds:>7.1f}x"
        )


if __name__ == "__main__":
    main()
