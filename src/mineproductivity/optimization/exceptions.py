"""The ``mineproductivity.optimization`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

__all__ = [
    "OptimizationExecutionError",
    "OptimizationRunNotFoundError",
    "OptimizationValidationError",
    "OptimizationVersionConflictError",
    "ProblemConflictError",
]


class OptimizationValidationError(ValidationError):
    """An ``OptimizationMetadata``, ``OptimizationProblem``, or
    ``OptimizationState`` failed validation (design spec §29, §9, §10),
    or a problem/category pairing violates §11/§14's variable-domain
    and objective-count rules."""


class OptimizationRunNotFoundError(NotFoundError):
    """``OptimizationRunRepository.get(run_id)`` found no run for that
    id, or ``REGISTRY.get(code)`` found no registered
    ``OptimizationModel`` for that code (design spec §6)."""


class OptimizationExecutionError(MineProductivityError):
    """``OptimizationExecutor`` raised for a solve/iteration that
    should have been structurally valid -- distinct from a legitimately
    infeasible problem (design spec §28), which returns an
    ``OptimizationResult(feasible=False, ...)`` carrying a warning
    instead of raising."""


class OptimizationVersionConflictError(RegistrationError):
    """A plugin attempted to re-register an existing
    ``OptimizationModel`` type code with materially different metadata
    without a version bump, mirroring
    ``simulation.SimulationVersionConflictError`` (spec 09 §6)."""


class ProblemConflictError(RegistrationError):
    """A governance action attempted to re-register an existing,
    ``Active`` ``OptimizationProblem`` code with different objectives/
    constraints/variables without a version bump and a ``Superseded``
    transition for the prior version (design spec §9, §25)."""
