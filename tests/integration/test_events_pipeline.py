"""Integration test for the Event Framework's full pipeline.

Exercises the path a future connector will drive: raw records in,
canonical events out, contextually validated, appended durably, published
to subscribers, and queryable/replayable afterward -- without any direct
function call bypassing a stage (Learning & Benchmark Suite v1.0, Part
VII, Category B: "Integration test datasets verify that the full
pipeline... produces the golden outputs without any direct function
call").

The `connectors` package does not exist yet, so this test plays the role
of a minimal CSV connector inline: it parses a small in-memory "CSV" of
haul cycles and delays, mirroring Developer & Cookbook Guide Part I,
Chapter 5's worked example.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from mineproductivity.core import PredicateSpecification
from mineproductivity.events import (
    AsOf,
    CycleEvent,
    DelayEvent,
    EventEnvelope,
    EventID,
    EventMetadata,
    EventQuery,
    EventValidator,
    EventVersion,
)
from mineproductivity.events.bus import _InMemoryEventBus
from mineproductivity.events.serialization import JSONEventCodec
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.ontology import DelayCategory

SHIFT_START = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)

CYCLE_CSV = """equipment_id,queue_min,spot_min,load_min,haul_min,dump_min,return_min,payload_t
HT-214,1.5,0.5,2.5,8.0,1.0,6.0,220.0
HT-214,1.2,0.4,2.6,8.1,1.1,5.9,218.0
HT-215,2.0,0.6,2.4,7.9,1.0,6.2,215.0
"""


def _parse_cycle_csv(shift_id: str) -> list[CycleEvent]:
    """Stand-in for a future FMSConnector.get_cycle_data(): parses a raw
    CSV export into canonical CycleEvent instances -- the rest of this
    test never touches CSV columns again, only canonical events."""
    reader = csv.DictReader(io.StringIO(CYCLE_CSV))
    return [
        CycleEvent(
            equipment_id=row["equipment_id"],
            shift_id=shift_id,
            queue_min=float(row["queue_min"]),
            spot_min=float(row["spot_min"]),
            load_min=float(row["load_min"]),
            haul_min=float(row["haul_min"]),
            dump_min=float(row["dump_min"]),
            return_min=float(row["return_min"]),
            payload_t=float(row["payload_t"]),
        )
        for row in reader
    ]


@pytest.fixture
def wired_store() -> tuple[_InMemoryEventStore, _InMemoryEventBus]:
    bus = _InMemoryEventBus()
    store = _InMemoryEventStore(bus=bus)
    return store, bus


class TestFullIngestionPipeline:
    """CSV -> canonical events -> validate -> envelope -> append -> publish -> query."""

    def test_end_to_end_ingestion_and_query(
        self, wired_store: tuple[_InMemoryEventStore, _InMemoryEventBus]
    ) -> None:
        store, bus = wired_store
        validator = EventValidator()
        published: list[EventEnvelope[Any]] = []
        bus.subscribe(PredicateSpecification(lambda _env: True), published.append)

        shift_id = "A-2026-06-25"
        cycles = _parse_cycle_csv(shift_id)
        assert len(cycles) == 3, "connector produced canonical events, not CSV rows"

        for i, cycle in enumerate(cycles):
            outcome = validator.validate_with_confidence(cycle)
            assert outcome.is_valid

            event_time = SHIFT_START + timedelta(minutes=i * 20)
            envelope = EventEnvelope(
                event_id=EventID.generate(),
                version=EventVersion(),
                payload=cycle,
                event_time_utc=event_time,
                processing_time_utc=event_time,
                ingestion_time_utc=event_time,
                metadata=EventMetadata(
                    name="cycle-ingest",
                    source_system="csv",
                    confidence=outcome.confidence.value,
                ),
            )
            result = store.append(envelope)
            assert result.is_ok

        # Published exactly once per appended envelope (durability-then-publish, spec §13.1).
        assert len(published) == 3

        # Queryable afterward, scoped by equipment.
        ht214_events = list(store.query(EventQuery(equipment_ids=("HT-214",))))
        assert len(ht214_events) == 2
        assert {e.payload.payload_t for e in ht214_events} == {220.0, 218.0}

        # The whole shift is queryable by shift_id too.
        shift_events = list(store.query(EventQuery(shift_ids=(shift_id,))))
        assert len(shift_events) == 3

    def test_mixed_event_types_coexist_in_one_store(
        self, wired_store: tuple[_InMemoryEventStore, _InMemoryEventBus]
    ) -> None:
        store, _bus = wired_store
        shift_id = "A-2026-06-25"

        cycle = _parse_cycle_csv(shift_id)[0]
        delay = DelayEvent(
            equipment_id="CR-01",
            shift_id=shift_id,
            delay_category=DelayCategory.EQUIPMENT,
            delay_reason="crusher_down",
            duration_min=252.0,
        )

        for i, payload in enumerate((cycle, delay)):
            event_time = SHIFT_START + timedelta(minutes=i * 10)
            store.append(
                EventEnvelope(
                    event_id=EventID.generate(),
                    version=EventVersion(),
                    payload=payload,
                    event_time_utc=event_time,
                    processing_time_utc=event_time,
                    ingestion_time_utc=event_time,
                )
            )

        assert len(list(store.query(EventQuery()))) == 2
        assert len(list(store.query(EventQuery(event_types=("CYCLE",))))) == 1
        assert len(list(store.query(EventQuery(event_types=("DELAY",))))) == 1


class TestFullPipelineWithReplay:
    """Ingest across two points in time, then time-travel back."""

    def test_replay_reconstructs_shift_progress_at_earlier_point(
        self, wired_store: tuple[_InMemoryEventStore, _InMemoryEventBus]
    ) -> None:
        store, _bus = wired_store
        shift_id = "A-2026-06-25"
        cycles = _parse_cycle_csv(shift_id)

        checkpoint = SHIFT_START + timedelta(minutes=15)
        for i, cycle in enumerate(cycles):
            event_time = SHIFT_START + timedelta(minutes=i * 20)
            store.append(
                EventEnvelope(
                    event_id=EventID.generate(),
                    version=EventVersion(),
                    payload=cycle,
                    event_time_utc=event_time,
                    processing_time_utc=event_time,
                    ingestion_time_utc=event_time,
                )
            )

        # Only the first cycle (t=0) happened by the checkpoint (t=15min);
        # the second (t=20min) and third (t=40min) had not happened yet.
        handle = store.replay(AsOf(utc=checkpoint))
        assert len(handle.envelopes) == 1
        assert handle.envelopes[0].payload.payload_t == 220.0

        # Full replay at shift end sees everything.
        full_handle = store.replay(AsOf(utc=SHIFT_START + timedelta(hours=2)))
        assert len(full_handle.envelopes) == 3

    def test_correction_is_visible_after_the_fact_but_not_before(
        self, wired_store: tuple[_InMemoryEventStore, _InMemoryEventBus]
    ) -> None:
        store, _bus = wired_store
        eid = EventID.generate()
        cycle = _parse_cycle_csv("A-2026-06-25")[0]
        corrected_cycle = CycleEvent(
            equipment_id=cycle.equipment_id,
            shift_id=cycle.shift_id,
            queue_min=cycle.queue_min,
            spot_min=cycle.spot_min,
            load_min=cycle.load_min,
            haul_min=cycle.haul_min,
            dump_min=cycle.dump_min,
            return_min=cycle.return_min,
            payload_t=210.0,  # a corrected payload reading
        )

        store.append(
            EventEnvelope(
                event_id=eid,
                version=EventVersion(),
                payload=cycle,
                event_time_utc=SHIFT_START,
                processing_time_utc=SHIFT_START,
                ingestion_time_utc=SHIFT_START,
            )
        )
        # get() sees the original until a correction is appended.
        assert store.get(eid).payload.payload_t == 220.0

        correction_ingested_at = SHIFT_START + timedelta(hours=1)
        store.append(
            EventEnvelope(
                event_id=eid,
                version=EventVersion().next_version(),
                payload=corrected_cycle,
                event_time_utc=SHIFT_START,  # same real-world event time
                processing_time_utc=correction_ingested_at,
                ingestion_time_utc=correction_ingested_at,
            )
        )

        # get() now resolves to the correction.
        assert store.get(eid).payload.payload_t == 210.0
        # But the original is still retrievable for audit.
        assert store.get(eid, as_of_version=EventVersion()).payload.payload_t == 220.0


class TestFullPipelineWithSerialization:
    """Ingest, then serialize the whole session and reload it losslessly."""

    def test_json_round_trip_of_an_entire_ingested_session(
        self, wired_store: tuple[_InMemoryEventStore, _InMemoryEventBus]
    ) -> None:
        store, _bus = wired_store
        shift_id = "A-2026-06-25"
        codec = JSONEventCodec()

        for i, cycle in enumerate(_parse_cycle_csv(shift_id)):
            event_time = SHIFT_START + timedelta(minutes=i * 20)
            store.append(
                EventEnvelope(
                    event_id=EventID.generate(),
                    version=EventVersion(),
                    payload=cycle,
                    event_time_utc=event_time,
                    processing_time_utc=event_time,
                    ingestion_time_utc=event_time,
                )
            )

        original = list(store.query(EventQuery()))
        serialized = [codec.serialize(envelope) for envelope in original]
        restored_store = _InMemoryEventStore()
        for data in serialized:
            envelope = codec.deserialize(data)
            restored_store.append(envelope)

        restored = list(restored_store.query(EventQuery()))
        assert restored == original
