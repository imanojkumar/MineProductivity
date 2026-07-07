"""Tests for mineproductivity.analytics.streaming."""

from __future__ import annotations

import inspect
import threading
from collections.abc import Callable

import pytest

from mineproductivity.events.bus import _InMemoryEventBus
from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.envelope import EventEnvelope

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.incremental import IncrementalAccumulator
from mineproductivity.analytics.streaming import StreamingAnalyticsSession

from .conftest import assert_no_import_from


def _envelope(
    cycle_event_factory: Callable[..., CycleEvent],
    cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    *,
    payload_t: float,
) -> EventEnvelope[CycleEvent]:
    return cycle_envelope_factory(payload=cycle_event_factory(payload_t=payload_t))


class TestStreamingAnalyticsSessionLifecycle:
    def test_start_returns_the_bus_subscription_handle(self) -> None:
        """No new subscription concept is introduced -- start() returns
        exactly the Subscription EventBus.subscribe() already returns."""
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus, accumulators={"payload_t": IncrementalAccumulator()}
        )
        subscription = session.start()
        assert subscription.is_active
        subscription.cancel()
        assert not subscription.is_active

    def test_cancel_is_idempotent(self) -> None:
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus, accumulators={"payload_t": IncrementalAccumulator()}
        )
        subscription = session.start()
        subscription.cancel()
        subscription.cancel()  # must not raise
        assert not subscription.is_active

    def test_a_new_session_is_restartable_from_cold(self) -> None:
        """A fresh session's accumulators start from zero -- no implicit
        history replay through the bus."""
        session = StreamingAnalyticsSession(
            bus=_InMemoryEventBus(), accumulators={"payload_t": IncrementalAccumulator()}
        )
        with pytest.raises(AnalyticsValidationError):
            session.snapshot("payload_t")


class TestStreamingAnalyticsSessionRouting:
    def test_publishing_an_envelope_updates_the_matching_accumulator(
        self,
        cycle_event_factory: Callable[..., CycleEvent],
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus, accumulators={"payload_t": IncrementalAccumulator()}
        )
        session.start()
        bus.publish(_envelope(cycle_event_factory, cycle_envelope_factory, payload_t=220.0))
        assert session.snapshot("payload_t").mean == 220.0

    def test_snapshot_reflects_every_published_envelope_in_order(
        self,
        cycle_event_factory: Callable[..., CycleEvent],
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus, accumulators={"payload_t": IncrementalAccumulator()}
        )
        session.start()
        for value in (100.0, 200.0, 300.0):
            bus.publish(_envelope(cycle_event_factory, cycle_envelope_factory, payload_t=value))
        summary = session.snapshot("payload_t")
        assert summary.n == 3
        assert summary.mean == pytest.approx(200.0)

    def test_multiple_tracked_keys_are_updated_independently(
        self,
        cycle_event_factory: Callable[..., CycleEvent],
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        """A single envelope updates *every* accumulator whose key names
        an attribute present on that payload -- ``CycleEvent`` has both
        ``payload_t`` and ``haul_min``."""
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus,
            accumulators={
                "payload_t": IncrementalAccumulator(),
                "haul_min": IncrementalAccumulator(),
            },
        )
        session.start()
        bus.publish(_envelope(cycle_event_factory, cycle_envelope_factory, payload_t=220.0))
        assert session.snapshot("payload_t").n == 1
        assert session.snapshot("haul_min").n == 1
        assert session.snapshot("haul_min").mean == 8.0  # cycle_event_factory's own fixed default

    def test_an_envelope_missing_a_tracked_field_is_silently_skipped(
        self,
        cycle_event_factory: Callable[..., CycleEvent],
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        """'qualify, don't coerce' -- a payload naturally only has some
        of the tracked fields; this must never raise AttributeError."""
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus, accumulators={"nonexistent_field": IncrementalAccumulator()}
        )
        session.start()
        bus.publish(cycle_envelope_factory())  # must not raise
        with pytest.raises(AnalyticsValidationError):
            session.snapshot("nonexistent_field")

    def test_a_tracked_field_that_is_not_numeric_is_silently_skipped(
        self, cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]]
    ) -> None:
        """'qualify, don't coerce' -- ``equipment_id`` is a string field;
        this must never raise ``ValueError``/``TypeError``."""
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus, accumulators={"equipment_id": IncrementalAccumulator()}
        )
        session.start()
        bus.publish(cycle_envelope_factory())  # must not raise
        with pytest.raises(AnalyticsValidationError):
            session.snapshot("equipment_id")

    def test_snapshot_of_an_unknown_key_raises_keyerror(self) -> None:
        session = StreamingAnalyticsSession(
            bus=_InMemoryEventBus(), accumulators={"payload_t": IncrementalAccumulator()}
        )
        with pytest.raises(KeyError):
            session.snapshot("not_a_tracked_key")

    def test_snapshot_never_touches_the_eventstore(self) -> None:
        """StreamingAnalyticsSession's constructor takes no EventStore
        at all -- snapshot() can only ever read from its own
        IncrementalAccumulator state, mechanically proving this (checked
        via bytecode ``co_names``, not raw source text, since the
        method's own docstring mentions "EventStore" in prose)."""
        assert "store" not in inspect.signature(StreamingAnalyticsSession.__init__).parameters
        assert "store" not in StreamingAnalyticsSession.snapshot.__code__.co_names


class TestStreamingAnalyticsSessionConcurrency:
    """Mandatory per the Implementation Checklist (§29): per-key
    serialization stress-tested under concurrent update() calls for the
    same key, and independent accumulators (different keys) proven
    non-interfering under concurrent updates."""

    def test_concurrent_updates_to_the_same_key_lose_no_observations(
        self,
        cycle_event_factory: Callable[..., CycleEvent],
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus, accumulators={"payload_t": IncrementalAccumulator()}
        )
        session.start()

        thread_count = 8
        updates_per_thread = 200
        values_per_thread = list(range(updates_per_thread))

        def publish_from_one_thread() -> None:
            for value in values_per_thread:
                bus.publish(
                    _envelope(cycle_event_factory, cycle_envelope_factory, payload_t=float(value))
                )

        threads = [threading.Thread(target=publish_from_one_thread) for _ in range(thread_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        summary = session.snapshot("payload_t")
        assert summary.n == thread_count * updates_per_thread
        expected_mean = sum(values_per_thread) * thread_count / (thread_count * updates_per_thread)
        assert summary.mean == pytest.approx(expected_mean)

    def test_concurrent_updates_to_independent_keys_do_not_corrupt_each_other(
        self,
        cycle_event_factory: Callable[..., CycleEvent],
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        """Two threads publish concurrently, one varying ``payload_t``
        while ``haul_min`` stays fixed at ``cycle_event_factory``'s own
        default (8.0) on every envelope. If the two accumulators shared
        any state, concurrent publishing would corrupt ``haul_min``'s
        otherwise-guaranteed-constant statistics; it does not."""
        bus = _InMemoryEventBus()
        session = StreamingAnalyticsSession(
            bus=bus,
            accumulators={
                "payload_t": IncrementalAccumulator(),
                "haul_min": IncrementalAccumulator(),
            },
        )
        session.start()

        updates_per_thread = 300

        def publish(offset: float) -> None:
            for value in range(updates_per_thread):
                bus.publish(
                    _envelope(
                        cycle_event_factory,
                        cycle_envelope_factory,
                        payload_t=float(value) + offset,
                    )
                )

        thread_a = threading.Thread(target=publish, args=(0.0,))
        thread_b = threading.Thread(target=publish, args=(1000.0,))
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        payload_summary = session.snapshot("payload_t")
        haul_summary = session.snapshot("haul_min")
        assert payload_summary.n == updates_per_thread * 2
        assert haul_summary.n == updates_per_thread * 2
        assert haul_summary.mean == pytest.approx(8.0)
        assert haul_summary.std == pytest.approx(0.0)


class TestStreamingAnalyticsSessionMetadata:
    def test_repr_includes_tracked_keys(self) -> None:
        session = StreamingAnalyticsSession(
            bus=_InMemoryEventBus(),
            accumulators={
                "payload_t": IncrementalAccumulator(),
                "haul_min": IncrementalAccumulator(),
            },
        )
        text = repr(session)
        assert "payload_t" in text
        assert "haul_min" in text


class TestPublicApiValidation:
    def test_streaminganalyticssession_is_exported(self) -> None:
        import mineproductivity.analytics as analytics

        assert "StreamingAnalyticsSession" in analytics.__all__
        assert analytics.StreamingAnalyticsSession is StreamingAnalyticsSession

    def test_streaming_module_public_api_matches_spec_exactly(self) -> None:
        import mineproductivity.analytics.streaming as streaming_module

        assert streaming_module.__all__ == ["StreamingAnalyticsSession"]

    def test_does_not_import_business_logic_modules(self) -> None:
        """Execution modules coordinate existing components rather than
        reimplement statistics/rolling/trend/baseline/benchmarking/
        quality logic -- mechanically verified, not merely asserted.
        ``streaming.py`` only ever delegates statistics computation to
        ``IncrementalAccumulator`` (§29)."""
        import mineproductivity.analytics.streaming as streaming_module

        assert_no_import_from(
            streaming_module,
            "statistics",
            "rolling",
            "trend",
            "baseline",
            "benchmarking",
            "quality",
        )
