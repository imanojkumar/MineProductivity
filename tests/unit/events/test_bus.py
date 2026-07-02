"""Tests for mineproductivity.events.bus."""

from __future__ import annotations

from typing import Any

import pytest

from mineproductivity.core import PredicateSpecification
from mineproductivity.events.bus import EventBus, Subscription, _InMemoryEventBus
from mineproductivity.events.envelope import EventEnvelope


class TestEventBusAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            EventBus()  # type: ignore[abstract]


class TestSubscriptionAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            Subscription()  # type: ignore[abstract]


ACCEPT_ALL: PredicateSpecification[EventEnvelope[Any]] = PredicateSpecification(lambda _env: True)


class TestInMemoryEventBus:
    def test_publish_with_no_subscribers_does_nothing(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        bus = _InMemoryEventBus()
        bus.publish(cycle_envelope_factory())  # should not raise

    def test_subscriber_receives_matching_envelope(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        bus = _InMemoryEventBus()
        received: list[EventEnvelope[Any]] = []
        bus.subscribe(ACCEPT_ALL, received.append)
        envelope = cycle_envelope_factory()
        bus.publish(envelope)
        assert received == [envelope]

    def test_subscriber_does_not_receive_non_matching_envelope(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory, cycle_event_factory
    ) -> None:
        bus = _InMemoryEventBus()
        received: list[EventEnvelope[Any]] = []
        heavy_only: PredicateSpecification[EventEnvelope[Any]] = PredicateSpecification(
            lambda env: env.payload.payload_t > 500.0
        )
        bus.subscribe(heavy_only, received.append)
        bus.publish(cycle_envelope_factory(payload=cycle_event_factory(payload_t=100.0)))
        assert received == []

    def test_multiple_subscribers_all_receive(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        bus = _InMemoryEventBus()
        received_a: list[EventEnvelope[Any]] = []
        received_b: list[EventEnvelope[Any]] = []
        bus.subscribe(ACCEPT_ALL, received_a.append)
        bus.subscribe(ACCEPT_ALL, received_b.append)
        envelope = cycle_envelope_factory()
        bus.publish(envelope)
        assert received_a == [envelope]
        assert received_b == [envelope]

    def test_cancel_stops_delivery(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        bus = _InMemoryEventBus()
        received: list[EventEnvelope[Any]] = []
        subscription = bus.subscribe(ACCEPT_ALL, received.append)
        bus.publish(cycle_envelope_factory())
        assert len(received) == 1
        subscription.cancel()
        bus.publish(cycle_envelope_factory())
        assert len(received) == 1

    def test_subscription_is_active_reflects_state(self) -> None:
        bus = _InMemoryEventBus()
        subscription = bus.subscribe(ACCEPT_ALL, lambda _env: None)
        assert subscription.is_active is True
        subscription.cancel()
        assert subscription.is_active is False

    def test_cancel_is_idempotent(self) -> None:
        bus = _InMemoryEventBus()
        subscription = bus.subscribe(ACCEPT_ALL, lambda _env: None)
        subscription.cancel()
        subscription.cancel()  # should not raise
        assert subscription.is_active is False
