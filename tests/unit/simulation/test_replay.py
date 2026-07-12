"""Tests for mineproductivity.simulation.replay."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.events import AsOf, CycleEvent, ProductionEvent, ReplayHandle
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.identifier import EventID
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.events.versioning import EventVersion
from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.replay import seed_from_replay

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _StubReplayStore:
    """Duck-typed store whose ``replay`` returns a prepared
    ``ReplayHandle`` -- stands in for a scenario-capable production
    ``EventStore`` (the reference in-memory store supports
    point-in-time replay only)."""

    def __init__(self, envelopes: tuple[EventEnvelope[CycleEvent], ...]) -> None:
        self._envelopes = envelopes

    def replay(self, as_of: AsOf) -> ReplayHandle[EventEnvelope[CycleEvent]]:
        return ReplayHandle(as_of=as_of, envelopes=self._envelopes)


def _cycle_envelope(minute: int) -> EventEnvelope[CycleEvent]:
    moment = _EPOCH + timedelta(minutes=minute)
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=CycleEvent(
            equipment_id="HT-1",
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
        metadata=EventMetadata(name="cycle", source_system="test"),
    )


def _production_envelope(minute: int) -> EventEnvelope[ProductionEvent]:
    moment = _EPOCH + timedelta(minutes=minute)
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=ProductionEvent(
            equipment_id="HT-1",
            shift_id="A",
            pit_code="north",
            material_type="ore",
            tonnes_moved=400.0,
            planned_tonnes=400.0,
            operating_h=0.2,
        ),
        event_time_utc=moment,
        processing_time_utc=moment,
        ingestion_time_utc=moment,
        metadata=EventMetadata(name="production", source_system="test"),
    )


class TestSeedFromReplay:
    def test_reconstructs_the_identical_state_a_hand_computed_fold_would(self) -> None:
        """Design spec §12, §35's event-replay seeding proof."""
        store = _InMemoryEventStore()
        for minute in (1, 2, 3):
            assert store.append(_cycle_envelope(minute)).is_ok
        assert store.append(_production_envelope(4)).is_ok
        as_of = AsOf(utc=_EPOCH + timedelta(hours=1))

        state = seed_from_replay(store, as_of)

        # Hand-computed fold over the same history:
        assert state.attributes["events_replayed"] == 4
        assert state.attributes["event_counts"] == {"CycleEvent": 3, "ProductionEvent": 1}
        assert state.attributes["last_event_time_utc"] == (
            (_EPOCH + timedelta(minutes=4)).isoformat()
        )
        assert state.simulated_time == as_of.utc

    def test_is_deterministic_for_the_same_history(self) -> None:
        store = _InMemoryEventStore()
        for minute in (1, 2):
            assert store.append(_cycle_envelope(minute)).is_ok
        as_of = AsOf(utc=_EPOCH + timedelta(hours=1))
        assert seed_from_replay(store, as_of) == seed_from_replay(store, as_of)

    def test_bounds_the_history_at_as_of(self) -> None:
        store = _InMemoryEventStore()
        assert store.append(_cycle_envelope(1)).is_ok
        assert store.append(_cycle_envelope(90)).is_ok  # after the as_of below
        state = seed_from_replay(store, AsOf(utc=_EPOCH + timedelta(minutes=30)))
        assert state.attributes["events_replayed"] == 1

    def test_empty_history_with_a_utc_anchor_is_a_valid_seed(self) -> None:
        state = seed_from_replay(_InMemoryEventStore(), AsOf(utc=_EPOCH))
        assert state.attributes["events_replayed"] == 0
        assert state.simulated_time == _EPOCH

    def test_scenario_only_as_of_falls_back_to_the_latest_event_time(self) -> None:
        """The reference in-memory store supports point-in-time replay
        only, so the scenario-``AsOf`` fallback is exercised against a
        duck-typed store returning a real ``ReplayHandle`` -- the exact
        shape a scenario-capable production store would return."""
        store = _StubReplayStore((_cycle_envelope(7),))
        state = seed_from_replay(store, AsOf(scenario="what-if"))
        assert state.simulated_time == _EPOCH + timedelta(minutes=7)

    def test_scenario_only_as_of_over_an_empty_history_raises(self) -> None:
        with pytest.raises(SimulationValidationError, match="cannot anchor simulated_time"):
            seed_from_replay(_StubReplayStore(()), AsOf(scenario="what-if"))
