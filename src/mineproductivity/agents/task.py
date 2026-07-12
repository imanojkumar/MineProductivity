"""``Task``/``TaskStatus``: agent execution's stateful core (design
spec §11).

Reuse audit: ``core.BaseEntity[str]`` reused by literal inheritance,
following ``optimization.OptimizationRun``'s precedent (spec 10 §10)
exactly -- identity-based equality inherited unchanged, state changes
via :meth:`Task.with_state`, never in-place mutation. The task is the
*record* of an execution; a task's next ``TaskState`` is produced by
whichever registered ``Agent``'s ``_act`` the ``TaskExecutor`` (§12)
dispatches to on its behalf.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseEntity

from mineproductivity.agents.exceptions import AgentValidationError
from mineproductivity.agents.state import TaskState

__all__ = ["Task", "TaskStatus"]


class TaskStatus(Enum):
    """A ``Task``'s own operational lifecycle -- mirrors
    ``optimization.RunStatus`` (spec 10 §10) in shape, extended with
    ``AWAITING_APPROVAL`` (design spec §11), the one member no lower
    package's execution lifecycle needed, since none of them pauses
    for a human decision mid-execution. ``COMPLETED`` and ``FAILED``
    are terminal (§11's state diagram)."""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Task(BaseEntity[str]):
    """The root of one executing or completed unit of agent work --
    'Task-as-entity,' following ``optimization.OptimizationRun``'s own
    precedent (spec 10 §10) exactly. Immutable; trivially safe to read
    and share across threads (design spec §32).

    Examples
    --------
    >>> task = Task(
    ...     id="TASK-1",
    ...     goal_code="GOAL.NightShiftRecovery",
    ...     agent_code="FLEET.ReassignmentAdvisor",
    ...     state=TaskState(attributes={"provisioned": True}),
    ... )
    >>> task.status
    <TaskStatus.SCHEDULED: 'scheduled'>
    >>> task.with_state(task.state, status=TaskStatus.RUNNING).status
    <TaskStatus.RUNNING: 'running'>
    >>> task.status  # the original instance is untouched
    <TaskStatus.SCHEDULED: 'scheduled'>
    """

    goal_code: str
    agent_code: str
    state: TaskState
    status: TaskStatus = dataclasses.field(default=TaskStatus.SCHEDULED)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Design spec §28: non-empty ``goal_code`` and
        ``agent_code``."""
        if not self.goal_code.strip():
            raise AgentValidationError("Task.goal_code must not be empty")
        if not self.agent_code.strip():
            raise AgentValidationError("Task.agent_code must not be empty")

    def with_state(self, state: TaskState, *, status: TaskStatus | None = None) -> Task:
        """Returns a NEW ``Task`` instance with ``state`` (and
        optionally ``status``) replacing the current ones -- identical
        to ``OptimizationRun.with_state()`` (spec 10 §10)."""
        return dataclasses.replace(
            self, state=state, status=status if status is not None else self.status
        )
