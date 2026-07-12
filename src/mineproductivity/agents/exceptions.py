"""The ``mineproductivity.agents`` exception hierarchy."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

__all__ = [
    "AgentExecutionError",
    "AgentValidationError",
    "AgentVersionConflictError",
    "PermissionDeniedError",
    "PolicyConflictError",
    "TaskNotFoundError",
]


class AgentValidationError(ValidationError):
    """An ``AgentMetadata``, ``Task``, or ``TaskState`` failed
    validation (design spec §29, §11) -- e.g. an empty code, a Task
    with no assigned agent code, or a State with empty attributes."""


class TaskNotFoundError(NotFoundError):
    """``TaskRepository.get(task_id)`` found no task for that id, or
    ``REGISTRY.get(code)`` found no registered ``Agent`` for that code
    (design spec §6)."""


class AgentExecutionError(MineProductivityError):
    """``TaskExecutor`` raised for a step that should have been
    structurally valid -- distinct from a legitimately-denied or
    legitimately-pending case (design spec §30's 'qualify, don't
    coerce' rule), which returns an ``AgentResult`` carrying a warning
    instead of raising."""


class AgentVersionConflictError(RegistrationError):
    """A plugin attempted to re-register an existing ``Agent`` or
    ``Tool`` type code with materially different metadata without a
    version bump, mirroring
    ``optimization.OptimizationVersionConflictError`` (spec 10 §6)."""


class PolicyConflictError(RegistrationError):
    """A governance action attempted to re-register an existing,
    ``Active`` ``AgentPolicy`` code with a different rule without a
    version bump -- the Policy-layer analogue of
    ``AgentVersionConflictError``, mirroring
    ``optimization.ProblemConflictError``'s identical reasoning
    (spec 10 §6)."""


class PermissionDeniedError(MineProductivityError):
    """``PolicyEngine.evaluate()`` rejected a ``Task`` outright (as
    opposed to routing it to ``AWAITING_APPROVAL``) -- the one case in
    this package where a policy violation is not a warning but a hard
    stop, since dispatching to an ``Agent`` lacking the required
    ``Permission`` is never a legitimate outcome to persist as a
    completed ``AgentResult`` (design spec §10, §28)."""
