"""The ``mineproductivity.decision`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

__all__ = [
    "DecisionModelNotFoundError",
    "DecisionValidationError",
    "DecisionVersionConflictError",
    "NoApplicablePolicyError",
    "PolicyConflictError",
]


class DecisionValidationError(ValidationError):
    """A ``DecisionMetadata``, ``Policy``, or ``Threshold`` failed
    validation (design spec §30, §12, §13) -- e.g. an empty ``code``, a
    ``Policy`` with zero rules, or an empty ``Threshold.field`` -- or a
    caller passed malformed arguments to a Decision method."""


class NoApplicablePolicyError(NotFoundError):
    """Raised only where a caller explicitly requests raising behavior
    instead of :meth:`~mineproductivity.decision.abstractions.DecisionModel.decide`'s
    default empty-recommendation result for a context no policy applies
    to (design spec §8)."""


class DecisionModelNotFoundError(NotFoundError):
    """``REGISTRY.get(code)`` found no registered ``DecisionModel`` for
    that code (design spec §32)."""


class DecisionVersionConflictError(RegistrationError):
    """A plugin attempted to re-register an existing ``DecisionModel``
    code with materially different metadata without a version bump
    (design spec §32), mirroring ``kpis.KPIVersionConflictError`` and
    ``analytics.AnalyticsVersionConflictError``."""


class PolicyConflictError(RegistrationError):
    """A plugin or governance action attempted to re-register an
    existing, ``Active`` ``Policy`` code with different rules/thresholds
    without a version bump and a ``Superseded`` transition for the prior
    version (design spec §12, §29) -- the ``Policy``-layer analogue of
    :class:`DecisionVersionConflictError`, since a ``Policy`` is a
    separate governed artifact from a ``DecisionModel`` implementation
    (design spec §3.6)."""
