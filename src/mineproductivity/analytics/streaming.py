"""Streaming analytics (§27): a long-lived session that subscribes to
an ``events.EventBus`` and incrementally updates one or more
``IncrementalAccumulator``\\ s as new envelopes arrive, without ever
re-scanning the full historical ``EventStore``. The live-operations-
center counterpart of ``BatchAnalyticsRunner`` (§28).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``IncrementalAccumulator`` (§29, ``incremental.py``) is reused verbatim
as the per-key running-statistics primitive -- this module never
recomputes a mean/variance itself, it only routes incoming envelope
field values into the correct accumulator's already-implemented
``update()``. ``events.EventBus``/``Subscription`` are reused verbatim
(ADR-0006's own "Dependency Rationale" section: "Analytics computations
legitimately need ``events.EventStore``/``EventBus`` directly... not
merely ``kpis.KPIResult`` objects") -- this module introduces no new
subscription/cancellation concept; ``start()`` returns the exact
``Subscription`` handle ``EventBus.subscribe()`` already returns.
``core.PredicateSpecification`` (already used identically by
``quality.py``'s ``_HasRequiredColumns`` for a different predicate) is
reused as the "match every envelope" filter ``subscribe()`` requires,
rather than defining a new trivial ``BaseSpecification`` subclass for a
one-line predicate -- exactly ``PredicateSpecification``'s own stated
purpose ("Adapts any plain callable... for one-off specifications that
do not warrant a dedicated class").

The one genuinely new piece is the per-envelope routing rule: which
accumulator does a given envelope update? Design spec §27's own
constructor signature (``accumulators: Mapping[str, IncrementalAccumulator]``)
keys accumulators by ``str`` but does not spell out what that string
means. ``timeseries.py``'s ``TimeSeries.from_event_query`` already
establishes the one precedent for turning an event payload into a
number: a ``value_field: str`` naming an attribute on the payload,
read via ``getattr(payload, value_field)``. This module reuses that
exact convention rather than inventing a second one: each accumulator's
key names a payload attribute; an incoming envelope updates every
accumulator whose key names an attribute actually present on that
envelope's payload (silently skipping the rest -- a payload naturally
only has some of the tracked fields, "qualify, don't coerce," never
``AttributeError``).
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from typing import Any

from mineproductivity.core import PredicateSpecification
from mineproductivity.events.bus import EventBus, Subscription
from mineproductivity.events.envelope import EventEnvelope

from mineproductivity.analytics.incremental import IncrementalAccumulator
from mineproductivity.analytics.result import StatisticalSummary

__all__ = ["StreamingAnalyticsSession"]


class StreamingAnalyticsSession:
    """A long-lived session that subscribes to an ``events.EventBus``
    and incrementally updates one or more ``IncrementalAccumulator``\\ s
    as new envelopes arrive, without ever re-scanning the full
    historical ``EventStore``. The live-operations-center counterpart of
    ``BatchAnalyticsRunner`` (§28).

    A session is long-lived but restartable-from-cold: if a session's
    process restarts, its ``IncrementalAccumulator``\\ s start from zero
    rather than attempting to replay history through the bus -- a caller
    that needs a warm-started session is expected to seed the
    accumulator from a ``BatchAnalyticsRunner`` pass over the relevant
    window first (§28), then call :meth:`start` to continue
    incrementally. This class performs no such seeding automatically.

    **Thread safety.** The Event Framework's own concurrency contract
    guarantees ``EventBus.publish()`` is only called after the
    corresponding ``append()`` has confirmed durability, but makes no
    guarantee about which thread a subscriber's handler runs on, nor
    that a single subscriber never receives two concurrent calls. This
    class does not assume single-threaded delivery: it serializes
    concurrent ``update()`` calls per accumulator key via one
    ``threading.Lock`` per key (mirroring ``kpis.ResultCache``'s own
    per-key-write concurrency contract) -- independent keys have no
    shared state and update fully in parallel.

    Examples
    --------
    >>> from mineproductivity.events.bus import _InMemoryEventBus
    >>> from mineproductivity.events.canonical import CycleEvent
    >>> from mineproductivity.events.envelope import EventEnvelope, EventMetadata
    >>> from mineproductivity.events.identifier import EventID
    >>> from mineproductivity.events.versioning import EventVersion
    >>> from datetime import datetime, timezone
    >>> bus = _InMemoryEventBus()
    >>> session = StreamingAnalyticsSession(
    ...     bus=bus, accumulators={"payload_t": IncrementalAccumulator()}
    ... )
    >>> subscription = session.start()
    >>> now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    >>> envelope = EventEnvelope(
    ...     event_id=EventID.generate(), version=EventVersion(),
    ...     payload=CycleEvent(equipment_id="HT-1", shift_id="A", queue_min=1.0,
    ...                         spot_min=0.5, load_min=2.0, haul_min=8.0, dump_min=1.0,
    ...                         return_min=6.0, payload_t=220.0),
    ...     event_time_utc=now, processing_time_utc=now, ingestion_time_utc=now,
    ...     metadata=EventMetadata(name="cycle", source_system="test"),
    ... )
    >>> bus.publish(envelope)
    >>> session.snapshot("payload_t").mean
    220.0
    >>> subscription.cancel()
    """

    def __init__(
        self, *, bus: EventBus, accumulators: Mapping[str, IncrementalAccumulator]
    ) -> None:
        self._bus = bus
        self._accumulators = dict(accumulators)
        self._locks = {key: threading.Lock() for key in self._accumulators}

    def start(self) -> Subscription:
        """Subscribes to ``bus``; each published ``EventEnvelope``
        updates the relevant accumulator(s)."""
        return self._bus.subscribe(PredicateSpecification(lambda envelope: True), self._on_envelope)

    def snapshot(self, key: str) -> StatisticalSummary:
        """The current, up-to-the-last-event ``StatisticalSummary`` for
        ``key``, read from its ``IncrementalAccumulator`` without
        touching the ``EventStore`` at all."""
        return self._accumulators[key].snapshot()

    def _on_envelope(self, envelope: EventEnvelope[Any]) -> None:
        for key, accumulator in self._accumulators.items():
            value = getattr(envelope.payload, key, None)
            if value is None:
                continue
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            with self._locks[key]:
                accumulator.update(numeric_value)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(keys={tuple(self._accumulators)!r})"
