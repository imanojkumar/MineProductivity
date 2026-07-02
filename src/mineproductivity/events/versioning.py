"""``EventVersion``: the correction/revision counter for one ``EventID``."""

from __future__ import annotations

import dataclasses

from mineproductivity.core import BaseVersionedObject

__all__ = ["EventVersion"]


@dataclasses.dataclass(frozen=True, slots=True)
class EventVersion(BaseVersionedObject):
    """The correction/revision counter for one :class:`~mineproductivity.events.identifier.EventID`.

    An ``(EventID, EventVersion)`` pair is the true primary key of a
    stored envelope -- see the Learning & Benchmark Suite v1.0, "Event
    corrections and idempotency". ``version=1`` (the inherited default)
    is the original ingestion; ``version=2`` and beyond are corrections,
    reached only via :meth:`~mineproductivity.core.versioning.BaseVersionedObject.next_version`.
    Never reset.

    Examples
    --------
    >>> original = EventVersion()
    >>> original.version
    1
    >>> correction = original.next_version()
    >>> correction.version
    2
    """
