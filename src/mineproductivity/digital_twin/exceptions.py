"""The ``mineproductivity.digital_twin`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

__all__ = [
    "TwinNotFoundError",
    "TwinStateConflictError",
    "TwinSyncError",
    "TwinValidationError",
    "TwinVersionConflictError",
]


class TwinValidationError(ValidationError):
    """A ``TwinMetadata``, ``TwinState``, or ``TwinSnapshot`` failed
    validation (design spec §26, §12, §13) -- e.g. an empty ``code``, or
    a ``TwinState`` with an empty ``attributes`` mapping where the twin
    category requires at least one attribute."""


class TwinNotFoundError(NotFoundError):
    """``TwinRepository.get(twin_id)`` found no twin for that id, or
    ``REGISTRY.get(code)`` found no registered ``Twin`` type for that
    code (design spec §6)."""


class TwinSyncError(MineProductivityError):
    """``Twin._apply()`` raised for a batch of events that should have
    been structurally valid -- distinct from a legitimately-empty-input
    case (design spec §8's 'qualify, don't coerce' rule), which returns
    a ``SyncResult`` carrying a warning instead of raising (§24)."""


class TwinVersionConflictError(RegistrationError):
    """A plugin attempted to re-register an existing ``Twin`` type code
    with materially different metadata without a version bump, mirroring
    ``decision.DecisionVersionConflictError`` (spec 07 §6) and
    ``analytics.AnalyticsVersionConflictError`` (spec 06 §6)."""


class TwinStateConflictError(MineProductivityError):
    """Two concurrent ``synchronize()`` calls for the same ``twin_id``
    raced past this package's per-id write serialization (design spec
    §29) -- raised only if that serialization contract itself is
    violated by a non-conforming ``TwinRepository`` implementation,
    never under normal operation with the reference in-memory
    repository."""
