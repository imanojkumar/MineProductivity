"""The ``mineproductivity.events`` exception hierarchy.

Every exception raised by this package derives from
:class:`~mineproductivity.core.exceptions.MineProductivityError` (directly
or via a ``core`` intermediate such as :class:`ValidationError`), so
callers can catch every framework-raised error with a single ``except``
clause while still being able to catch a specific category.
"""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError

__all__ = [
    "DuplicateEventError",
    "EventNotFoundError",
    "EventValidationError",
    "EventVersionConflictError",
    "ReplayError",
]


class EventValidationError(ValidationError):
    """A :class:`~mineproductivity.events.base_event.BaseEvent` or
    :class:`~mineproductivity.events.envelope.EventEnvelope` failed
    structural or schema validation."""


class EventVersionConflictError(MineProductivityError):
    """An append specified a version that does not extend the store's
    current version chain for that ``EventID`` (e.g. appending version 1
    again with different field values)."""


class DuplicateEventError(MineProductivityError):
    """Raised when an implementation chooses to reject a duplicate rather
    than silently no-op it. Not raised by the reference in-memory store,
    which treats an identical re-append as an idempotent no-op."""


class EventNotFoundError(NotFoundError):
    """``EventStore.get()`` found no envelope for the given ``EventID``
    (optionally, at the given version)."""


class ReplayError(MineProductivityError):
    """A ``replay()`` or ``snapshot()`` request could not be satisfied
    (e.g. ``as_of`` predates the store's retention horizon)."""
