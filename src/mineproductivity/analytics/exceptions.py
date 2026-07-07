"""The ``mineproductivity.analytics`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

__all__ = [
    "AnalyticsModelNotFoundError",
    "AnalyticsValidationError",
    "AnalyticsVersionConflictError",
    "InsufficientDataError",
]


class AnalyticsValidationError(ValidationError):
    """An ``AnalyticsMetadata``, ``RollingSpec``, ``TimeSeries``, or other
    Analytics value object failed validation -- e.g. an empty ``code``,
    a ``RollingSpec`` with neither (or both) of ``time_window``/``periods``
    set -- or a caller passed malformed arguments to an Analytics method,
    e.g. ``AggregationEngine.reduce_kpi_results`` given an empty or
    mixed-``code`` sequence of ``KPIResult``\\ s."""


class InsufficientDataError(ValidationError):
    """Raised only where a caller explicitly requests raising behavior
    instead of :meth:`~mineproductivity.analytics.abstractions.AnalyticsModel.analyze`'s
    default warning-carrying result for a series shorter than
    ``AnalyticsMetadata.min_observations``."""


class AnalyticsModelNotFoundError(NotFoundError):
    """``REGISTRY.get(code)`` found no registered ``AnalyticsModel`` for
    that code."""


class AnalyticsVersionConflictError(RegistrationError):
    """A plugin attempted to re-register an existing ``AnalyticsModel``
    code with materially different metadata without a version bump,
    mirroring ``kpis.KPIVersionConflictError``."""
