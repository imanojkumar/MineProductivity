"""The ``mineproductivity.kpis`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

__all__ = [
    "KPIAggregationError",
    "KPICircularDependencyError",
    "KPINotFoundError",
    "KPIValidationError",
    "KPIVersionConflictError",
]


class KPIValidationError(ValidationError):
    """``KPIMetadata`` failed validation -- e.g. malformed identifier,
    missing mandatory field, aggregation/time-model violation."""


class KPINotFoundError(NotFoundError):
    """``REGISTRY.get(code)`` found no registered, non-``Retired`` KPI."""


class KPICircularDependencyError(MineProductivityError):
    """``DependencyGraph.detect_cycle()`` found a cycle -- raised at
    registration time (registering the KPI that completes the cycle),
    never deferred to first execution."""


class KPIAggregationError(MineProductivityError):
    """An attempt was made to aggregate a RATIO/AVERAGE-kind KPI's
    already-computed sub-period results as if they were ADDITIVE (the
    "averaging shift TPHs" mistake, made structurally impossible by the
    engine rather than merely discouraged by documentation)."""


class KPIVersionConflictError(RegistrationError):
    """A plugin attempted to re-register an existing, ``Active`` KPI
    code with metadata that changes its formula/units/semantics without
    a MAJOR version bump."""
