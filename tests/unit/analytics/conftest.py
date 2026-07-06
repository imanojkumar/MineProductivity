"""Shared fixtures for ``mineproductivity.analytics`` unit tests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

import pytest

from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.identifier import EventID
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.events.versioning import EventVersion

NOW = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)


@pytest.fixture
def event_store() -> _InMemoryEventStore:
    return _InMemoryEventStore()


@pytest.fixture
def cycle_event_factory() -> Callable[..., CycleEvent]:
    def factory(
        *, equipment_id: str = "HT-214", shift_id: str = "A-2026-06-25", payload_t: float = 220.0
    ) -> CycleEvent:
        return CycleEvent(
            equipment_id=equipment_id,
            shift_id=shift_id,
            queue_min=1.5,
            spot_min=0.5,
            load_min=2.5,
            haul_min=8.0,
            dump_min=1.0,
            return_min=6.0,
            payload_t=payload_t,
        )

    return factory


@pytest.fixture
def cycle_envelope_factory(
    cycle_event_factory: Callable[..., CycleEvent],
) -> Callable[..., EventEnvelope[CycleEvent]]:
    def factory(
        *,
        payload: CycleEvent | None = None,
        event_time: datetime = NOW,
    ) -> EventEnvelope[CycleEvent]:
        return EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=payload or cycle_event_factory(),
            event_time_utc=event_time,
            processing_time_utc=event_time,
            ingestion_time_utc=event_time,
            metadata=EventMetadata(name="test-event", source_system="test"),
        )

    return factory
