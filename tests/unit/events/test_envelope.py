"""Tests for mineproductivity.events.envelope."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.exceptions import EventValidationError
from mineproductivity.events.identifier import EventID
from mineproductivity.events.versioning import EventVersion

NOW = datetime(2026, 6, 25, 6, tzinfo=timezone.utc)


def make_cycle() -> CycleEvent:
    return CycleEvent(
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


class TestEventMetadata:
    def test_defaults(self) -> None:
        meta = EventMetadata(name="event")
        assert meta.confidence == 1.0
        assert meta.source_system == "unknown"
        assert meta.late_arrival is False

    def test_inherits_base_metadata_name_validation(self) -> None:
        with pytest.raises(Exception):  # noqa: B017 - core.ValidationError, exercised via inheritance
            EventMetadata(name="")

    def test_confidence_out_of_range_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            EventMetadata(name="event", confidence=1.5)

    def test_confidence_negative_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            EventMetadata(name="event", confidence=-0.1)

    def test_boundary_confidence_values_accepted(self) -> None:
        assert EventMetadata(name="event", confidence=0.0).confidence == 0.0
        assert EventMetadata(name="event", confidence=1.0).confidence == 1.0

    def test_super_validate_actually_runs(self) -> None:
        # Regression test for the @dataclass(slots=True) + bare super()
        # gotcha: confirms BaseMetadata's own name-emptiness check still
        # fires from within EventMetadata's overridden validate().
        with pytest.raises(Exception):  # noqa: B017
            EventMetadata(name="   ")


class TestEventEnvelope:
    def test_construction(self) -> None:
        envelope = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=make_cycle(),
            event_time_utc=NOW,
            processing_time_utc=NOW,
            ingestion_time_utc=NOW,
        )
        assert envelope.payload.payload_t == 220.0

    def test_default_metadata(self) -> None:
        envelope = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=make_cycle(),
            event_time_utc=NOW,
            processing_time_utc=NOW,
            ingestion_time_utc=NOW,
        )
        assert envelope.metadata.name == "event"

    def test_valid_timestamp_ordering_accepted(self) -> None:
        envelope = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=make_cycle(),
            event_time_utc=NOW,
            processing_time_utc=NOW + timedelta(seconds=1),
            ingestion_time_utc=NOW + timedelta(seconds=2),
        )
        assert envelope.event_time_utc < envelope.ingestion_time_utc

    def test_equal_timestamps_accepted(self) -> None:
        EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=make_cycle(),
            event_time_utc=NOW,
            processing_time_utc=NOW,
            ingestion_time_utc=NOW,
        )

    def test_processing_before_event_time_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            EventEnvelope(
                event_id=EventID.generate(),
                version=EventVersion(),
                payload=make_cycle(),
                event_time_utc=NOW,
                processing_time_utc=NOW - timedelta(seconds=1),
                ingestion_time_utc=NOW,
            )

    def test_ingestion_before_processing_time_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            EventEnvelope(
                event_id=EventID.generate(),
                version=EventVersion(),
                payload=make_cycle(),
                event_time_utc=NOW,
                processing_time_utc=NOW,
                ingestion_time_utc=NOW - timedelta(seconds=1),
            )

    def test_equality_by_value(self) -> None:
        eid = EventID.generate()
        version = EventVersion()
        a = EventEnvelope(
            event_id=eid,
            version=version,
            payload=make_cycle(),
            event_time_utc=NOW,
            processing_time_utc=NOW,
            ingestion_time_utc=NOW,
        )
        b = EventEnvelope(
            event_id=eid,
            version=version,
            payload=make_cycle(),
            event_time_utc=NOW,
            processing_time_utc=NOW,
            ingestion_time_utc=NOW,
        )
        assert a == b

    def test_is_frozen(self) -> None:
        envelope = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=make_cycle(),
            event_time_utc=NOW,
            processing_time_utc=NOW,
            ingestion_time_utc=NOW,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            envelope.payload = make_cycle()  # type: ignore[misc]
