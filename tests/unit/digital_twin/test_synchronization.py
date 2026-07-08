"""Tests for mineproductivity.digital_twin.synchronization."""

from __future__ import annotations

import threading
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

import pytest

from mineproductivity.core import (
    DuplicateError,
    InMemoryRepository,
    Maybe,
    NotFoundError,
    PredicateSpecification,
)
from mineproductivity.digital_twin.abstractions import Twin, TwinContext
from mineproductivity.digital_twin.caching import TwinStateCache
from mineproductivity.digital_twin.exceptions import (
    TwinNotFoundError,
    TwinStateConflictError,
    TwinSyncError,
)
from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.metadata import TwinCategory, TwinMetadata
from mineproductivity.digital_twin.state import TwinState
from mineproductivity.digital_twin.synchronization import SyncPolicy, TwinSynchronizer
from mineproductivity.events import AsOf, BaseEvent, CycleEvent
from mineproductivity.events.bus import _InMemoryEventBus
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.identifier import EventID
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.events.versioning import EventVersion

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _CounterTwin(Twin):
    """Deterministic on the cumulative event count: folding N events --
    in one batch or one at a time -- always converges on the identical
    ``TwinState`` (design spec §32's replay-consistency proof)."""

    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="TEST.SyncCounter",
        category=TwinCategory.EQUIPMENT,
        description="Counts events folded into it.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        if not events:
            return self.state
        seen = int(self.state.attributes.get("events_seen", 0)) + len(events)
        return TwinState(
            attributes={"events_seen": seen},
            captured_at=_EPOCH + timedelta(seconds=seen),
        )


class _AlwaysRaisingTwin(Twin):
    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="TEST.SyncRaises",
        category=TwinCategory.EQUIPMENT,
        description="Raises from _apply for any non-empty batch.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        if not events:
            return self.state
        raise RuntimeError("malformed batch reached _apply")


class _NoChangeTwin(Twin):
    meta: ClassVar[TwinMetadata] = TwinMetadata(
        code="TEST.SyncNoChange",
        category=TwinCategory.EQUIPMENT,
        description="Folds every batch into a value-identical state.",
    )

    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        return TwinState(
            attributes=dict(self.state.attributes),
            captured_at=self.state.captured_at,
            schema_version=self.state.schema_version,
        )


class _FakeStore:
    """Duck-typed ``EventStore`` stand-in for contexts that never touch
    the store."""


def _payload(equipment_id: str = "EQ-1") -> CycleEvent:
    return CycleEvent(
        equipment_id=equipment_id,
        shift_id="A",
        queue_min=1.0,
        spot_min=0.5,
        load_min=2.0,
        haul_min=8.0,
        dump_min=1.0,
        return_min=6.0,
        payload_t=220.0,
    )


def _envelope(
    equipment_id: str = "EQ-1", *, event_time_utc: datetime | None = None
) -> EventEnvelope[CycleEvent]:
    moment = event_time_utc or _EPOCH
    return EventEnvelope(
        event_id=EventID.generate(),
        version=EventVersion(),
        payload=_payload(equipment_id),
        event_time_utc=moment,
        processing_time_utc=moment,
        ingestion_time_utc=moment,
        metadata=EventMetadata(name="cycle", source_system="test"),
    )


def _state(events_seen: int = 0) -> TwinState:
    return TwinState(
        attributes={"events_seen": events_seen},
        captured_at=_EPOCH + timedelta(seconds=events_seen),
    )


def _provisioned(
    twin_id: str = "EQ-1",
    *,
    twin_type: type[Twin] = _CounterTwin,
    status: TwinStatus = TwinStatus.PROVISIONED,
) -> tuple[InMemoryRepository[Twin, str], TwinSynchronizer]:
    repository: InMemoryRepository[Twin, str] = InMemoryRepository()
    repository.add(
        twin_type(id=twin_id, scope={"equipment_id": twin_id}, state=_state(), status=status)
    )
    return repository, TwinSynchronizer(repository=repository)


def _context(**kwargs: Any) -> TwinContext:
    return TwinContext(event_store=_FakeStore(), **kwargs)


class TestSyncPolicy:
    def test_carries_mode_filter_and_optional_interval(self) -> None:
        event_filter = PredicateSpecification(lambda envelope: True)
        policy = SyncPolicy(
            mode="scheduled", event_filter=event_filter, poll_interval=timedelta(minutes=5)
        )
        assert policy.mode == "scheduled"
        assert policy.event_filter is event_filter
        assert policy.poll_interval == timedelta(minutes=5)

    def test_poll_interval_defaults_to_none(self) -> None:
        policy = SyncPolicy(
            mode="realtime", event_filter=PredicateSpecification(lambda envelope: True)
        )
        assert policy.poll_interval is None

    def test_repr_names_the_mode(self) -> None:
        policy = SyncPolicy(
            mode="realtime", event_filter=PredicateSpecification(lambda envelope: True)
        )
        assert "realtime" in repr(policy)


class TestSynchronizeHappyPath:
    def test_folds_events_and_stores_the_replacement(self) -> None:
        repository, synchronizer = _provisioned()
        result = synchronizer.synchronize("EQ-1", [_payload(), _payload()], context=_context())
        assert result.events_applied == 2
        assert repository.get("EQ-1").state.attributes["events_seen"] == 2

    def test_first_successful_sync_transitions_provisioned_to_synchronized(self) -> None:
        repository, synchronizer = _provisioned()
        result = synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert result.previous_status is TwinStatus.PROVISIONED
        assert result.new_status is TwinStatus.SYNCHRONIZED
        assert repository.get("EQ-1").status is TwinStatus.SYNCHRONIZED

    def test_stale_twin_returns_to_synchronized_when_sync_resumes(self) -> None:
        """Design spec §10's Stale -> Synchronized transition."""
        repository, synchronizer = _provisioned(status=TwinStatus.STALE)
        result = synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert result.previous_status is TwinStatus.STALE
        assert result.new_status is TwinStatus.SYNCHRONIZED

    def test_never_mutates_the_twin_instance_it_read(self) -> None:
        """Design spec §11: synchronize computes a replacement via
        ``with_state()``; the instance it read is untouched."""
        repository, synchronizer = _provisioned()
        original = repository.get("EQ-1")
        synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert original.state.attributes["events_seen"] == 0
        assert original.status is TwinStatus.PROVISIONED
        assert repository.get("EQ-1") is not original

    def test_result_carries_the_twin_id(self) -> None:
        _, synchronizer = _provisioned()
        assert synchronizer.synchronize("EQ-1", [_payload()], context=_context()).twin_id == "EQ-1"


class TestSynchronizeQualifyDontCoerce:
    def test_unknown_twin_id_raises_twin_not_found(self) -> None:
        _, synchronizer = _provisioned()
        with pytest.raises(TwinNotFoundError):
            synchronizer.synchronize("NO-SUCH-TWIN", [_payload()], context=_context())

    def test_empty_batch_returns_warning_not_a_raise(self) -> None:
        repository, synchronizer = _provisioned()
        result = synchronizer.synchronize("EQ-1", [], context=_context())
        assert result.events_applied == 0
        assert result.warnings == ("no events to apply; state unchanged",)
        assert result.previous_status is result.new_status is TwinStatus.PROVISIONED

    def test_empty_batch_leaves_the_repository_untouched(self) -> None:
        repository, synchronizer = _provisioned()
        original = repository.get("EQ-1")
        synchronizer.synchronize("EQ-1", [], context=_context())
        assert repository.get("EQ-1") is original

    def test_value_unchanged_fold_carries_a_warning(self) -> None:
        _, synchronizer = _provisioned(twin_type=_NoChangeTwin)
        result = synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert result.warnings == ("events applied left the state value-unchanged",)
        assert result.new_status is TwinStatus.SYNCHRONIZED


class TestRetiredIsTerminal:
    """Design spec §10: no transition out of ``Retired``; a retired id
    is never reusable for a different real-world thing."""

    def test_synchronize_skips_a_retired_twin(self) -> None:
        repository, synchronizer = _provisioned(status=TwinStatus.RETIRED)
        result = synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert result.previous_status is result.new_status is TwinStatus.RETIRED
        assert result.events_applied == 0
        assert "retired" in result.warnings[0]
        assert repository.get("EQ-1").state.attributes["events_seen"] == 0

    def test_a_retired_id_stays_occupied_and_is_never_reusable(self) -> None:
        repository, _ = _provisioned(status=TwinStatus.RETIRED)
        with pytest.raises(DuplicateError):
            repository.add(_CounterTwin(id="EQ-1", scope={"equipment_id": "OTHER"}, state=_state()))


class TestApplyFailuresAndDegraded:
    def test_apply_failure_raises_twin_sync_error(self) -> None:
        _, synchronizer = _provisioned(twin_type=_AlwaysRaisingTwin)
        with pytest.raises(TwinSyncError):
            synchronizer.synchronize("EQ-1", [_payload()], context=_context())

    def test_a_single_failure_does_not_yet_degrade(self) -> None:
        repository, synchronizer = _provisioned(twin_type=_AlwaysRaisingTwin)
        with pytest.raises(TwinSyncError):
            synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert repository.get("EQ-1").status is TwinStatus.PROVISIONED

    def test_repeated_failures_mark_the_twin_degraded(self) -> None:
        """Design spec §10's Synchronized/Stale -> Degraded transition
        on repeated ``_apply`` failures."""
        repository, synchronizer = _provisioned(twin_type=_AlwaysRaisingTwin)
        for _ in range(2):
            with pytest.raises(TwinSyncError):
                synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert repository.get("EQ-1").status is TwinStatus.DEGRADED

    def test_degraded_recovers_on_next_successful_sync(self) -> None:
        """Design spec §10's Degraded -> Synchronized transition."""
        repository, synchronizer = _provisioned(status=TwinStatus.DEGRADED)
        result = synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert result.previous_status is TwinStatus.DEGRADED
        assert result.new_status is TwinStatus.SYNCHRONIZED

    def test_a_success_resets_the_consecutive_failure_count(self) -> None:
        repository: InMemoryRepository[Twin, str] = InMemoryRepository()

        class _FlakyTwin(Twin):
            meta: ClassVar[TwinMetadata] = TwinMetadata(
                code="TEST.SyncFlaky",
                category=TwinCategory.EQUIPMENT,
                description="Raises only when told to.",
            )

            def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
                if self.state.attributes.get("raise_next"):
                    raise RuntimeError("flaky")
                return TwinState(attributes={"raise_next": True}, captured_at=_EPOCH)

        repository.add(
            _FlakyTwin(
                id="EQ-1",
                scope={"equipment_id": "EQ-1"},
                state=TwinState(attributes={"raise_next": False}, captured_at=_EPOCH),
            )
        )
        synchronizer = TwinSynchronizer(repository=repository)
        # failure, then success (via fresh state), then failure again:
        # the intervening success must reset the counter, so the second
        # failure is a *first* consecutive failure -- not yet Degraded.
        repository.remove("EQ-1")
        repository.add(
            _FlakyTwin(
                id="EQ-1",
                scope={"equipment_id": "EQ-1"},
                state=TwinState(attributes={"raise_next": True}, captured_at=_EPOCH),
            )
        )
        with pytest.raises(TwinSyncError):
            synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        repository.remove("EQ-1")
        repository.add(
            _FlakyTwin(
                id="EQ-1",
                scope={"equipment_id": "EQ-1"},
                state=TwinState(attributes={"raise_next": False}, captured_at=_EPOCH),
            )
        )
        synchronizer.synchronize("EQ-1", [_payload()], context=_context())  # success, resets
        with pytest.raises(TwinSyncError):
            synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert repository.get("EQ-1").status is not TwinStatus.DEGRADED


class TestCacheWiring:
    def test_successful_sync_caches_the_supplied_evidence(self) -> None:
        repository, _ = _provisioned()
        cache = TwinStateCache()
        synchronizer = TwinSynchronizer(repository=repository, cache=cache)
        as_of = AsOf(utc=_EPOCH)
        context = _context(as_of=as_of)
        synchronizer.synchronize("EQ-1", [_payload()], context=context)
        assert cache.get("EQ-1", as_of) is context

    def test_no_as_of_means_nothing_is_cached(self) -> None:
        repository, _ = _provisioned()
        cache = TwinStateCache()
        synchronizer = TwinSynchronizer(repository=repository, cache=cache)
        synchronizer.synchronize("EQ-1", [_payload()], context=_context())
        assert repr(cache).endswith("(entries=0)")

    def test_cache_is_never_read_as_the_authority_for_current_state(self) -> None:
        """Design spec §22, §31: the cache holds evidence *inputs*; the
        repository, not the cache, is always the source of truth --
        proven by synchronize never calling ``get()`` at all."""

        class _SpyCache(TwinStateCache):
            def __init__(self) -> None:
                super().__init__()
                self.get_calls = 0

            def get(self, twin_id: str, as_of: AsOf) -> TwinContext | None:
                self.get_calls += 1
                return super().get(twin_id, as_of)

        repository, _ = _provisioned()
        spy = _SpyCache()
        synchronizer = TwinSynchronizer(repository=repository, cache=spy)
        synchronizer.synchronize("EQ-1", [_payload()], context=_context(as_of=AsOf(utc=_EPOCH)))
        assert spy.get_calls == 0


class TestLiveSynchronization:
    def test_event_bus_subscription_drives_synchronize(self) -> None:
        """Design spec §15's live mode: ``EventBus.subscribe(policy.event_filter, handler)``
        where the handler folds each delivered envelope's payload."""
        repository, synchronizer = _provisioned()
        policy = SyncPolicy(
            mode="realtime",
            event_filter=PredicateSpecification(
                lambda envelope: bool(envelope.payload.equipment_id == "EQ-1")
            ),
        )
        bus = _InMemoryEventBus()
        store = _InMemoryEventStore()

        def _handler(envelope: EventEnvelope[Any]) -> None:
            synchronizer.synchronize(
                "EQ-1", [envelope.payload], context=TwinContext(event_store=store)
            )

        subscription = bus.subscribe(policy.event_filter, _handler)
        bus.publish(_envelope("EQ-1"))
        bus.publish(_envelope("EQ-2"))  # filtered out by the policy
        assert repository.get("EQ-1").state.attributes["events_seen"] == 1

        subscription.cancel()
        bus.publish(_envelope("EQ-1"))
        assert repository.get("EQ-1").state.attributes["events_seen"] == 1


class TestReplayConsistency:
    """Design spec §32 proof 5: cold-start reconstruction via
    ``EventStore.replay(as_of)`` and incremental synchronization
    converge on the identical ``TwinState`` for the same event
    history."""

    def test_cold_start_replay_equals_incremental_synchronization(self) -> None:
        store = _InMemoryEventStore()
        envelopes = [
            _envelope("EQ-1", event_time_utc=_EPOCH + timedelta(minutes=index))
            for index in range(5)
        ]
        for envelope in envelopes:
            assert store.append(envelope).is_ok

        as_of = AsOf(utc=_EPOCH + timedelta(hours=1))
        context = TwinContext(event_store=store, as_of=as_of)

        # Cold start: fold the full replayed history from genesis.
        cold = _CounterTwin(id="EQ-1", scope={"equipment_id": "EQ-1"}, state=_state())
        handle = store.replay(as_of)
        cold = cold.with_state(
            cold._apply([envelope.payload for envelope in handle.envelopes], context=context),
            status=TwinStatus.SYNCHRONIZED,
        )

        # Incremental: one synchronize() call per envelope, in order.
        repository, synchronizer = _provisioned()
        for envelope in envelopes:
            synchronizer.synchronize("EQ-1", [envelope.payload], context=context)
        incremental = repository.get("EQ-1")

        assert cold.state == incremental.state
        assert cold.status is incremental.status


class TestConcurrency:
    def test_independent_twins_synchronize_fully_in_parallel(self) -> None:
        """Design spec §30: different ids never contend."""
        repository: InMemoryRepository[Twin, str] = InMemoryRepository()
        twin_ids = [f"EQ-{index}" for index in range(8)]
        for twin_id in twin_ids:
            repository.add(
                _CounterTwin(id=twin_id, scope={"equipment_id": twin_id}, state=_state())
            )
        synchronizer = TwinSynchronizer(repository=repository)

        def _sync_many(twin_id: str) -> None:
            for _ in range(25):
                synchronizer.synchronize(twin_id, [_payload(twin_id)], context=_context())

        threads = [threading.Thread(target=_sync_many, args=(twin_id,)) for twin_id in twin_ids]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        for twin_id in twin_ids:
            assert repository.get(twin_id).state.attributes["events_seen"] == 25

    def test_same_twin_id_serializes_without_lost_updates_under_an_external_lock(self) -> None:
        """Design spec §29: the bare in-memory reference repository
        provides no locking of its own; a caller running concurrent
        ``synchronize()`` calls for the same id adds external
        synchronization -- exactly what a conforming production
        ``TwinRepository`` would provide internally. With it, no update
        is lost."""
        repository, synchronizer = _provisioned()
        lock = threading.Lock()

        def _sync_many() -> None:
            for _ in range(25):
                with lock:
                    synchronizer.synchronize("EQ-1", [_payload()], context=_context())

        threads = [threading.Thread(target=_sync_many) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert repository.get("EQ-1").state.attributes["events_seen"] == 100


class TestStateConflictDetection:
    """Design spec §29: ``TwinStateConflictError`` is reserved for a
    ``TwinRepository`` implementation that violates the per-id write
    serialization contract -- simulated here by non-conforming stub
    repositories, never triggered by the reference implementation under
    normal operation."""

    class _VanishingRepository(InMemoryRepository[Twin, str]):
        """Simulates a racing writer removing the twin mid-swap."""

        def remove(self, entity_id: str) -> None:
            raise NotFoundError(f"{entity_id!r} vanished mid-swap")

    class _ReappearingRepository(InMemoryRepository[Twin, str]):
        """Simulates a racing writer re-adding the twin mid-swap. (The
        arrange step below bypasses this override via
        ``InMemoryRepository.add`` directly.)"""

        def add(self, entity: Twin) -> None:
            raise DuplicateError(f"{entity.id!r} reappeared mid-swap")

    def test_remove_racing_not_found_becomes_state_conflict(self) -> None:
        repository = self._VanishingRepository()
        InMemoryRepository.add(
            repository, _CounterTwin(id="EQ-1", scope={"equipment_id": "EQ-1"}, state=_state())
        )
        synchronizer = TwinSynchronizer(repository=repository)
        with pytest.raises(TwinStateConflictError):
            synchronizer.synchronize("EQ-1", [_payload()], context=_context())

    def test_add_racing_duplicate_becomes_state_conflict(self) -> None:
        repository = self._ReappearingRepository()
        InMemoryRepository.add(
            repository, _CounterTwin(id="EQ-1", scope={"equipment_id": "EQ-1"}, state=_state())
        )
        synchronizer = TwinSynchronizer(repository=repository)
        with pytest.raises(TwinStateConflictError):
            synchronizer.synchronize("EQ-1", [_payload()], context=_context())

    def test_find_is_used_for_the_lookup_so_maybe_contract_holds(self) -> None:
        """The not-found path goes through ``find()``/``Maybe`` (design
        spec §20's contract), translated into ``TwinNotFoundError``."""
        repository: InMemoryRepository[Twin, str] = InMemoryRepository()
        assert isinstance(repository.find("EQ-1"), Maybe)
        synchronizer = TwinSynchronizer(repository=repository)
        with pytest.raises(TwinNotFoundError):
            synchronizer.synchronize("EQ-1", [], context=_context())


class TestRepr:
    def test_repr_names_the_collaborators(self) -> None:
        _, synchronizer = _provisioned()
        assert "TwinSynchronizer" in repr(synchronizer)
