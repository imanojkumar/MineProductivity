"""``EventBus``: near-real-time publish/subscribe distribution of newly appended envelopes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from mineproductivity.core import BaseSpecification

from mineproductivity.events.envelope import EventEnvelope

__all__ = ["EventBus", "Subscription"]


class Subscription(ABC):
    """A handle to one active :meth:`EventBus.subscribe` registration."""

    @abstractmethod
    def cancel(self) -> None:
        """Unregister the associated handler. Idempotent: cancelling an
        already-cancelled subscription is a no-op."""

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Whether this subscription's handler is still registered."""


class EventBus(ABC):
    """Near-real-time publish/subscribe distribution of newly appended
    envelopes, for consumers that cannot wait for a query (streaming
    KPIs, a future Digital Twin's live-state sync).
    """

    @abstractmethod
    def publish(self, envelope: EventEnvelope[Any]) -> None:
        """Called by an :class:`~mineproductivity.events.store.EventStore`
        after a successful, durable write. Never called before durability
        is confirmed."""

    @abstractmethod
    def subscribe(
        self,
        filter: BaseSpecification[EventEnvelope[Any]],
        handler: Callable[[EventEnvelope[Any]], None],
    ) -> Subscription:
        """Register ``handler`` to be called for every published envelope
        matching ``filter``. Returns a :class:`Subscription` whose
        ``cancel()`` unregisters it."""


class _InMemorySubscription(Subscription):
    """Reference :class:`Subscription` implementation for :class:`_InMemoryEventBus`."""

    def __init__(self, bus: "_InMemoryEventBus", token: int) -> None:
        self._bus = bus
        self._token = token
        self._active = True

    def cancel(self) -> None:
        if self._active:
            self._bus._unsubscribe(self._token)
            self._active = False

    @property
    def is_active(self) -> bool:
        return self._active


class _InMemoryEventBus(EventBus):
    """Reference, in-process :class:`EventBus` for tests and examples --
    not for production use. Dispatches synchronously: ``publish()``
    calls every matching handler before returning."""

    def __init__(self) -> None:
        self._subscriptions: dict[
            int, tuple[BaseSpecification[EventEnvelope[Any]], Callable[[EventEnvelope[Any]], None]]
        ] = {}
        self._next_token = 0

    def publish(self, envelope: EventEnvelope[Any]) -> None:
        for filter_spec, handler in list(self._subscriptions.values()):
            if filter_spec.is_satisfied_by(envelope):
                handler(envelope)

    def subscribe(
        self,
        filter: BaseSpecification[EventEnvelope[Any]],
        handler: Callable[[EventEnvelope[Any]], None],
    ) -> Subscription:
        token = self._next_token
        self._next_token += 1
        self._subscriptions[token] = (filter, handler)
        return _InMemorySubscription(self, token)

    def _unsubscribe(self, token: int) -> None:
        self._subscriptions.pop(token, None)
