"""``EventStore``: the append-only, immutable system of record."""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from mineproductivity.core import BaseSpecification, BaseValueObject, Maybe, Result

from mineproductivity.events.bus import EventBus
from mineproductivity.events.envelope import EventEnvelope
from mineproductivity.events.exceptions import EventNotFoundError, EventVersionConflictError
from mineproductivity.events.identifier import EventID
from mineproductivity.events.replay import AsOf, ReplayHandle
from mineproductivity.events.snapshot import EventSnapshot
from mineproductivity.events.versioning import EventVersion

__all__ = ["EventFilter", "EventQuery", "EventStore"]

TEnvelope = TypeVar("TEnvelope", bound=EventEnvelope[Any])

type EventFilter = BaseSpecification[EventEnvelope[Any]]
"""Reuses :class:`~mineproductivity.core.specification.BaseSpecification`
(``&``/``|``/``~`` composable) rather than a bespoke query DSL."""


@dataclasses.dataclass(frozen=True, slots=True)
class EventQuery(BaseValueObject):
    """A query over a store's envelopes.

    ``as_of_version_policy`` governs version resolution: ``"latest"``
    (the default) collapses to the highest stored version per
    ``EventID``; ``"as_of_ingestion"`` returns every stored version, as
    ingested, with no collapsing -- useful for audit/replay tooling that
    needs the full correction history rather than only the current view.
    """

    event_types: tuple[str, ...] | None = dataclasses.field(default=None, kw_only=True)
    equipment_ids: tuple[str, ...] | None = dataclasses.field(default=None, kw_only=True)
    shift_ids: tuple[str, ...] | None = dataclasses.field(default=None, kw_only=True)
    since_utc: datetime | None = dataclasses.field(default=None, kw_only=True)
    until_utc: datetime | None = dataclasses.field(default=None, kw_only=True)
    filters: tuple[EventFilter, ...] = dataclasses.field(default=(), kw_only=True)
    as_of_version_policy: Literal["latest", "as_of_ingestion"] = dataclasses.field(
        default="latest", kw_only=True
    )


class EventStore(ABC, Generic[TEnvelope]):
    """The append-only, immutable system of record.

    Specializes the shape of :class:`~mineproductivity.core.repository.BaseRepository`
    (add/get/find/list) with event-sourcing-specific operations:
    append-only writes (no update, no delete), version-aware retrieval,
    range queries by ``event_time_utc``, and replay. An ``EventStore``
    never mutates a stored envelope.
    """

    @abstractmethod
    def append(self, envelope: TEnvelope) -> Result[EventID]:
        """Append one envelope. Idempotent on ``(event_id, version)``: a
        second append of an identical envelope is a no-op success; an
        append of a *different* envelope under an already-stored
        ``(event_id, version)`` is a conflict."""

    @abstractmethod
    def append_batch(self, envelopes: Iterable[TEnvelope]) -> Result[Sequence[EventID]]:
        """Append many envelopes, short-circuiting on the first rejection."""

    @abstractmethod
    def get(self, event_id: EventID, *, as_of_version: EventVersion | None = None) -> TEnvelope:
        """Return the envelope for ``event_id``, at its highest stored
        version unless ``as_of_version`` pins an earlier one.

        Raises
        ------
        EventNotFoundError
            If no such envelope (at that version, if specified) exists.
        """

    @abstractmethod
    def find(self, event_id: EventID) -> Maybe[TEnvelope]:
        """Non-raising counterpart to :meth:`get`."""

    @abstractmethod
    def query(self, query: EventQuery) -> Iterator[TEnvelope]:
        """Stream envelopes matching ``query``. MUST be a generator (or
        otherwise lazy ``Iterator``) -- never a materialized ``list``."""

    @abstractmethod
    def replay(self, as_of: AsOf) -> ReplayHandle[TEnvelope]:
        """Reconstruct the store's logical state as of a point in time or
        a named scenario."""

    @abstractmethod
    def snapshot(self, as_of: AsOf) -> EventSnapshot:
        """Materialize a snapshot to accelerate future replay to or past ``as_of``."""

    def __contains__(self, event_id: EventID) -> bool:
        return self.find(event_id).is_some


class _InMemoryEventStore(EventStore[EventEnvelope[Any]]):
    """Reference, dictionary-backed :class:`EventStore` for tests and
    examples -- not for production use. Optionally wired to an
    :class:`~mineproductivity.events.bus.EventBus`: on a successful
    append, publishes the envelope to it after durability is confirmed.
    """

    def __init__(self, *, bus: EventBus | None = None) -> None:
        self._storage: dict[str, dict[int, EventEnvelope[Any]]] = {}
        self._append_order: list[EventEnvelope[Any]] = []
        self._bus = bus

    def append(self, envelope: EventEnvelope[Any]) -> Result[EventID]:
        versions = self._storage.setdefault(envelope.event_id.value, {})
        existing = versions.get(envelope.version.version)
        if existing is not None:
            if existing == envelope:
                return Result.ok(envelope.event_id)
            return Result.err(
                EventVersionConflictError(
                    f"conflicting content for event_id={envelope.event_id.value!r} "
                    f"version={envelope.version.version}"
                )
            )
        versions[envelope.version.version] = envelope
        self._append_order.append(envelope)
        if self._bus is not None:
            self._bus.publish(envelope)
        return Result.ok(envelope.event_id)

    def append_batch(self, envelopes: Iterable[EventEnvelope[Any]]) -> Result[Sequence[EventID]]:
        appended: list[EventID] = []
        for envelope in envelopes:
            result = self.append(envelope)
            if result.is_err:
                return Result.err(result.error)
            appended.append(result.unwrap())
        return Result.ok(tuple(appended))

    def get(
        self, event_id: EventID, *, as_of_version: EventVersion | None = None
    ) -> EventEnvelope[Any]:
        versions = self._storage.get(event_id.value)
        if not versions:
            raise EventNotFoundError(f"no envelope found for event_id={event_id.value!r}")
        if as_of_version is not None:
            envelope = versions.get(as_of_version.version)
            if envelope is None:
                raise EventNotFoundError(
                    f"no version {as_of_version.version} found for event_id={event_id.value!r}"
                )
            return envelope
        return versions[max(versions)]

    def find(self, event_id: EventID) -> Maybe[EventEnvelope[Any]]:
        versions = self._storage.get(event_id.value)
        if not versions:
            return Maybe.nothing()
        return Maybe.some(versions[max(versions)])

    def query(self, query: EventQuery) -> Iterator[EventEnvelope[Any]]:
        if query.as_of_version_policy == "latest":
            candidates = [
                versions[max(versions)] for versions in self._storage.values() if versions
            ]
        else:
            candidates = list(self._append_order)
        candidates.sort(key=lambda envelope: envelope.event_time_utc)
        for envelope in candidates:
            if self._matches(envelope, query):
                yield envelope

    def replay(self, as_of: AsOf) -> ReplayHandle[EventEnvelope[Any]]:
        eligible_latest = self._eligible_latest_per_id(as_of)
        envelopes = tuple(
            sorted(eligible_latest.values(), key=lambda envelope: envelope.event_time_utc)
        )
        return ReplayHandle(as_of=as_of, envelopes=envelopes)

    def snapshot(self, as_of: AsOf) -> EventSnapshot:
        eligible_latest = self._eligible_latest_per_id(as_of)
        return EventSnapshot(as_of=as_of, state=dict(eligible_latest))

    def _eligible_latest_per_id(self, as_of: AsOf) -> dict[str, EventEnvelope[Any]]:
        if as_of.utc is None:
            raise NotImplementedError(
                "the reference in-memory store only supports point-in-time (AsOf.utc) replay"
            )
        as_of_utc = as_of.utc
        result: dict[str, EventEnvelope[Any]] = {}
        for event_id, versions in self._storage.items():
            eligible = {v: e for v, e in versions.items() if e.event_time_utc <= as_of_utc}
            if eligible:
                result[event_id] = eligible[max(eligible)]
        return result

    def _matches(self, envelope: EventEnvelope[Any], query: EventQuery) -> bool:
        if (
            query.event_types is not None
            and envelope.payload.event_type_code not in query.event_types
        ):
            return False
        if (
            query.equipment_ids is not None
            and envelope.payload.equipment_id not in query.equipment_ids
        ):
            return False
        if query.shift_ids is not None and envelope.payload.shift_id not in query.shift_ids:
            return False
        if query.since_utc is not None and envelope.event_time_utc < query.since_utc:
            return False
        if query.until_utc is not None and envelope.event_time_utc >= query.until_utc:
            return False
        return all(spec.is_satisfied_by(envelope) for spec in query.filters)
