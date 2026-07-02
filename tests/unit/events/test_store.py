"""Tests for mineproductivity.events.store."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from mineproductivity.core import PredicateSpecification
from mineproductivity.events.envelope import EventEnvelope
from mineproductivity.events.exceptions import EventNotFoundError, EventVersionConflictError
from mineproductivity.events.identifier import EventID
from mineproductivity.events.store import EventFilter, EventQuery, EventStore, _InMemoryEventStore
from mineproductivity.events.versioning import EventVersion

from .conftest import NOW


class TestEventStoreAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            EventStore()  # type: ignore[abstract]


class TestAppend:
    def test_append_then_get_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        envelope = cycle_envelope_factory()
        result = store.append(envelope)
        assert result.is_ok
        assert result.unwrap() == envelope.event_id
        assert store.get(envelope.event_id) == envelope

    def test_append_batch(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        envelopes = [cycle_envelope_factory() for _ in range(3)]
        result = store.append_batch(envelopes)
        assert result.is_ok
        assert len(result.unwrap()) == 3

    def test_append_batch_short_circuits_on_conflict(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        store = _InMemoryEventStore()
        eid = EventID.generate()
        v1 = cycle_envelope_factory(event_id=eid)
        conflicting = cycle_envelope_factory(
            event_id=eid, payload=cycle_event_factory(payload_t=999.0)
        )
        store.append(v1)
        result = store.append_batch([conflicting])
        assert result.is_err


class TestIdempotency:
    def test_reappending_identical_envelope_is_a_noop(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        envelope = cycle_envelope_factory()
        r1 = store.append(envelope)
        r2 = store.append(envelope)
        assert r1.is_ok and r2.is_ok
        assert len(list(store.query(EventQuery()))) == 1

    def test_conflicting_content_at_same_version_rejected(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        store = _InMemoryEventStore()
        eid = EventID.generate()
        version = EventVersion()
        original = cycle_envelope_factory(event_id=eid, version=version)
        different = cycle_envelope_factory(
            event_id=eid, version=version, payload=cycle_event_factory(payload_t=999.0)
        )
        store.append(original)
        result = store.append(different)
        assert result.is_err
        assert isinstance(result.error, EventVersionConflictError)
        # original remains the stored value
        assert store.get(eid).payload.payload_t == 220.0

    def test_repeated_reappend_three_times_stays_a_noop(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        envelope = cycle_envelope_factory()
        for _ in range(3):
            assert store.append(envelope).is_ok
        assert len(list(store.query(EventQuery()))) == 1


class TestGetAndFind:
    def test_get_missing_raises_not_found(self) -> None:
        store = _InMemoryEventStore()
        with pytest.raises(EventNotFoundError):
            store.get(EventID.generate())

    def test_find_missing_returns_nothing(self) -> None:
        store = _InMemoryEventStore()
        assert store.find(EventID.generate()).is_nothing

    def test_find_existing_returns_some(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        envelope = cycle_envelope_factory()
        store.append(envelope)
        found = store.find(envelope.event_id)
        assert found.is_some
        assert found.unwrap() == envelope

    def test_contains_operator(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        envelope = cycle_envelope_factory()
        store.append(envelope)
        assert envelope.event_id in store
        assert EventID.generate() not in store


class TestVersioning:
    def test_get_returns_highest_version_by_default(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        store = _InMemoryEventStore()
        eid = EventID.generate()
        v1 = cycle_envelope_factory(event_id=eid, version=EventVersion())
        v2 = cycle_envelope_factory(
            event_id=eid,
            version=EventVersion().next_version(),
            payload=cycle_event_factory(payload_t=250.0),
        )
        store.append(v1)
        store.append(v2)
        assert store.get(eid).payload.payload_t == 250.0

    def test_get_as_of_version_pins_earlier_version(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        store = _InMemoryEventStore()
        eid = EventID.generate()
        v1 = cycle_envelope_factory(event_id=eid, version=EventVersion())
        v2 = cycle_envelope_factory(
            event_id=eid,
            version=EventVersion().next_version(),
            payload=cycle_event_factory(payload_t=250.0),
        )
        store.append(v1)
        store.append(v2)
        pinned = store.get(eid, as_of_version=EventVersion())
        assert pinned.payload.payload_t == 220.0

    def test_get_as_of_missing_version_raises(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        eid = EventID.generate()
        store.append(cycle_envelope_factory(event_id=eid))
        with pytest.raises(EventNotFoundError):
            store.get(eid, as_of_version=EventVersion(version=99))


class TestQuery:
    def test_query_all(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        for _ in range(3):
            store.append(cycle_envelope_factory())
        assert len(list(store.query(EventQuery()))) == 3

    def test_query_is_lazy_generator(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        import inspect

        store = _InMemoryEventStore()
        store.append(cycle_envelope_factory())
        result = store.query(EventQuery())
        assert inspect.isgenerator(result)

    def test_query_filters_by_equipment_ids(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        store = _InMemoryEventStore()
        store.append(cycle_envelope_factory(payload=cycle_event_factory(equipment_id="HT-1")))
        store.append(cycle_envelope_factory(payload=cycle_event_factory(equipment_id="HT-2")))
        store.append(cycle_envelope_factory(payload=cycle_event_factory(equipment_id="HT-1")))
        results = list(store.query(EventQuery(equipment_ids=("HT-1",))))
        assert len(results) == 2

    def test_query_filters_by_event_types(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        store.append(cycle_envelope_factory())
        results = list(store.query(EventQuery(event_types=("CYCLE",))))
        assert len(results) == 1
        results_none = list(store.query(EventQuery(event_types=("DELAY",))))
        assert len(results_none) == 0

    def test_query_filters_by_shift_ids(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        store.append(cycle_envelope_factory())
        assert len(list(store.query(EventQuery(shift_ids=("A-2026-06-25",))))) == 1
        assert len(list(store.query(EventQuery(shift_ids=("OTHER",))))) == 0

    def test_query_filters_by_since_and_until(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        store.append(cycle_envelope_factory(event_time=NOW))
        store.append(cycle_envelope_factory(event_time=NOW + timedelta(hours=1)))
        store.append(cycle_envelope_factory(event_time=NOW + timedelta(hours=2)))
        results = list(store.query(EventQuery(since_utc=NOW + timedelta(hours=1))))
        assert len(results) == 2
        results2 = list(store.query(EventQuery(until_utc=NOW + timedelta(hours=1))))
        assert len(results2) == 1  # until is exclusive

    def test_query_results_sorted_by_event_time(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        e2 = cycle_envelope_factory(event_time=NOW + timedelta(hours=2))
        e1 = cycle_envelope_factory(event_time=NOW)
        store.append(e2)
        store.append(e1)
        results = list(store.query(EventQuery()))
        assert results == [e1, e2]

    def test_query_with_specification_filter(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        store = _InMemoryEventStore()
        store.append(cycle_envelope_factory(payload=cycle_event_factory(payload_t=100.0)))
        store.append(cycle_envelope_factory(payload=cycle_event_factory(payload_t=300.0)))
        heavy: EventFilter = PredicateSpecification(lambda env: env.payload.payload_t > 200.0)
        results = list(store.query(EventQuery(filters=(heavy,))))
        assert len(results) == 1
        assert results[0].payload.payload_t == 300.0

    def test_as_of_ingestion_policy_returns_every_version(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        store = _InMemoryEventStore()
        eid = EventID.generate()
        store.append(cycle_envelope_factory(event_id=eid, version=EventVersion()))
        store.append(
            cycle_envelope_factory(
                event_id=eid,
                version=EventVersion().next_version(),
                payload=cycle_event_factory(payload_t=999.0),
            )
        )
        latest_only = list(store.query(EventQuery(as_of_version_policy="latest")))
        all_versions = list(store.query(EventQuery(as_of_version_policy="as_of_ingestion")))
        assert len(latest_only) == 1
        assert len(all_versions) == 2


class TestBusWiring:
    def test_append_publishes_to_wired_bus(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        from mineproductivity.events.bus import _InMemoryEventBus
        from mineproductivity.core import PredicateSpecification

        bus = _InMemoryEventBus()
        store = _InMemoryEventStore(bus=bus)
        received: list[EventEnvelope[Any]] = []
        bus.subscribe(PredicateSpecification(lambda _env: True), received.append)

        envelope = cycle_envelope_factory()
        store.append(envelope)

        assert received == [envelope]

    def test_idempotent_reappend_does_not_republish(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        from mineproductivity.events.bus import _InMemoryEventBus
        from mineproductivity.core import PredicateSpecification

        bus = _InMemoryEventBus()
        store = _InMemoryEventStore(bus=bus)
        received: list[EventEnvelope[Any]] = []
        bus.subscribe(PredicateSpecification(lambda _env: True), received.append)

        envelope = cycle_envelope_factory()
        store.append(envelope)
        store.append(envelope)

        assert len(received) == 1

    def test_no_bus_wired_is_safe(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        store = _InMemoryEventStore()
        result = store.append(cycle_envelope_factory())
        assert result.is_ok


class TestReplayAndSnapshot:
    def test_replay_at_or_before_event_time_includes_it(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        from mineproductivity.events.replay import AsOf

        store = _InMemoryEventStore()
        envelope = cycle_envelope_factory(event_time=NOW)
        store.append(envelope)
        handle = store.replay(AsOf(utc=NOW))
        assert len(handle.envelopes) == 1

    def test_replay_before_all_events_returns_empty(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        from mineproductivity.events.replay import AsOf

        store = _InMemoryEventStore()
        store.append(cycle_envelope_factory(event_time=NOW))
        handle = store.replay(AsOf(utc=NOW - timedelta(hours=1)))
        assert handle.envelopes == ()

    def test_replay_collapses_to_latest_version_per_id(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        from mineproductivity.events.replay import AsOf

        store = _InMemoryEventStore()
        eid = EventID.generate()
        store.append(cycle_envelope_factory(event_id=eid, event_time=NOW, version=EventVersion()))
        store.append(
            cycle_envelope_factory(
                event_id=eid,
                event_time=NOW,
                version=EventVersion().next_version(),
                payload=cycle_event_factory(payload_t=999.0),
            )
        )
        handle = store.replay(AsOf(utc=NOW))
        assert len(handle.envelopes) == 1
        assert handle.envelopes[0].payload.payload_t == 999.0

    def test_replay_scenario_only_asof_raises(self) -> None:
        from mineproductivity.events.replay import AsOf

        store = _InMemoryEventStore()
        with pytest.raises(NotImplementedError):
            store.replay(AsOf(scenario="what-if"))

    def test_snapshot_state_matches_replay(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        from mineproductivity.events.replay import AsOf

        store = _InMemoryEventStore()
        e1 = cycle_envelope_factory(event_time=NOW)
        e2 = cycle_envelope_factory(event_time=NOW + timedelta(hours=1))
        store.append(e1)
        store.append(e2)
        as_of = AsOf(utc=NOW + timedelta(hours=2))
        snapshot = store.snapshot(as_of)
        handle = store.replay(as_of)
        assert set(snapshot.state.keys()) == {e.event_id.value for e in handle.envelopes}

    def test_replay_snapshot_equivalence_law(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        """replay(as_of) == fold(query(since=snapshot.as_of), initial=snapshot.state).

        The design specification's snapshot equivalence law (§17.1 of the
        Event Framework spec): a snapshot plus everything queried since it
        must reconstruct the same state as a direct replay to the same
        point in time.
        """
        from mineproductivity.events.replay import AsOf

        store = _InMemoryEventStore()
        checkpoint_time = NOW + timedelta(hours=1)
        for i in range(3):
            store.append(
                cycle_envelope_factory(
                    payload=cycle_event_factory(equipment_id=f"HT-{i}"),
                    event_time=NOW + timedelta(minutes=i),
                )
            )
        snapshot = store.snapshot(AsOf(utc=checkpoint_time))

        for i in range(3, 6):
            store.append(
                cycle_envelope_factory(
                    payload=cycle_event_factory(equipment_id=f"HT-{i}"),
                    event_time=checkpoint_time + timedelta(minutes=i),
                )
            )

        final_as_of = AsOf(utc=checkpoint_time + timedelta(hours=1))
        direct_replay = store.replay(final_as_of)

        folded: dict[str, EventEnvelope[Any]] = dict(snapshot.state)
        for envelope in store.query(EventQuery(since_utc=snapshot.as_of.utc)):
            folded[envelope.event_id.value] = envelope

        direct_ids = {e.event_id.value for e in direct_replay.envelopes}
        assert direct_ids == set(folded.keys())
        for envelope in direct_replay.envelopes:
            assert folded[envelope.event_id.value] == envelope
