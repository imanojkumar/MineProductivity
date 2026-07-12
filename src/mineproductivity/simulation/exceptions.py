"""The ``mineproductivity.simulation`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

__all__ = [
    "ScenarioConflictError",
    "SimulationExecutionError",
    "SimulationRunNotFoundError",
    "SimulationValidationError",
    "SimulationVersionConflictError",
]


class SimulationValidationError(ValidationError):
    """A ``SimulationMetadata``, ``Scenario``, or ``SimulationState``
    failed validation (design spec §29, §9, §10) -- e.g. an empty
    ``code``, a ``Scenario`` with no ``model_code``, or a
    ``SimulationState`` with empty ``attributes``."""


class SimulationRunNotFoundError(NotFoundError):
    """``SimulationRunRepository.get(run_id)`` found no run for that
    id, or ``REGISTRY.get(code)`` found no registered
    ``SimulationModel`` for that code (design spec §6)."""


class SimulationExecutionError(MineProductivityError):
    """``SimulationExecutor`` raised for a batch of steps/trials that
    should have been structurally valid -- distinct from a
    legitimately-incomplete-input case (design spec §8's 'qualify,
    don't coerce' rule), which returns a ``SimulationResult`` carrying
    a warning instead of raising (§28)."""


class SimulationVersionConflictError(RegistrationError):
    """A plugin attempted to re-register an existing ``SimulationModel``
    type code with materially different metadata without a version
    bump, mirroring ``digital_twin.TwinVersionConflictError`` (spec 08
    §6) and ``decision.DecisionVersionConflictError`` (spec 07 §6)."""


class ScenarioConflictError(RegistrationError):
    """A governance action attempted to re-register an existing,
    ``Active`` ``Scenario`` code with different parameters/initial
    conditions without a version bump and a ``Superseded`` transition
    for the prior version -- the ``Scenario``-layer analogue of
    :class:`SimulationVersionConflictError`, since a ``Scenario`` is a
    separate governed artifact from a ``SimulationModel``
    implementation (design spec §9, §25)."""
