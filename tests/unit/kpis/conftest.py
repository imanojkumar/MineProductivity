"""Shared fixtures for ``mineproductivity.kpis`` unit tests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from mineproductivity.events import EventEnvelope, EventID, EventVersion
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.ontology import Shift

from mineproductivity.kpis import REGISTRY, KPIEngine, ResultCache
from mineproductivity.kpis.backends import PandasBackend

SHIFT_START = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)
SHIFT_END = datetime(2026, 6, 25, 18, 0, tzinfo=timezone.utc)
SHIFT_ID = "A-2026-06-25"


def make_shift(shift_id: str = SHIFT_ID, *, scheduled_h: float = 12.0) -> Shift:
    return Shift(
        id=shift_id,
        mine_id="bingham-west",
        pattern="2x12",
        start_utc=SHIFT_START,
        end_utc=SHIFT_END,
        scheduled_h=scheduled_h,
    )


def append_event(
    store: _InMemoryEventStore, payload: Any, *, event_time: datetime = SHIFT_START
) -> None:
    envelope = EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=payload,
        event_time_utc=event_time,
        processing_time_utc=event_time,
        ingestion_time_utc=event_time,
    )
    result = store.append(envelope)
    assert result.is_ok


@pytest.fixture
def event_store() -> _InMemoryEventStore:
    return _InMemoryEventStore()


@pytest.fixture
def shift() -> Shift:
    return make_shift()


@pytest.fixture
def engine(event_store: _InMemoryEventStore, shift: Shift) -> KPIEngine:
    return KPIEngine(
        store=event_store,
        registry=REGISTRY,
        backend=PandasBackend(),
        cache=ResultCache(),
        shifts={shift.id: shift},
    )
