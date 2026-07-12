"""``OptimizationRun``/``RunStatus``: optimization execution's
stateful core (design spec §10).

Reuse audit: ``core.BaseEntity[str]`` reused by literal inheritance,
following ``simulation.SimulationRun``'s precedent (spec 09 §10)
exactly -- identity-based equality inherited unchanged, state changes
via :meth:`OptimizationRun.with_state`, never in-place mutation. The
run is the *record* of an execution; the executor dispatches to
whichever category method produces its next state.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseEntity

from mineproductivity.optimization.state import OptimizationState

__all__ = ["OptimizationRun", "RunStatus"]


class RunStatus(Enum):
    """An ``OptimizationRun``'s own operational lifecycle -- mirrors
    ``simulation.RunStatus`` (spec 09 §10) exactly in shape.
    ``COMPLETED`` and ``FAILED`` are terminal (design spec §10's state
    diagram)."""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class OptimizationRun(BaseEntity[str]):
    """The root of one executing or completed optimization attempt --
    'Run-as-entity,' following ``simulation.SimulationRun``'s own
    precedent (spec 09 §10) exactly. Immutable; trivially safe to read
    and share across threads (design spec §32).

    Examples
    --------
    >>> run = OptimizationRun(
    ...     id="RUN-1",
    ...     problem_code="FLEET.NightShiftAllocation",
    ...     state=OptimizationState(attributes={"provisioned": True}),
    ... )
    >>> run.status
    <RunStatus.SCHEDULED: 'scheduled'>
    >>> run.with_state(run.state, status=RunStatus.RUNNING).status
    <RunStatus.RUNNING: 'running'>
    >>> run.status  # the original instance is untouched
    <RunStatus.SCHEDULED: 'scheduled'>
    """

    problem_code: str
    state: OptimizationState
    status: RunStatus = dataclasses.field(default=RunStatus.SCHEDULED)

    def with_state(
        self, state: OptimizationState, *, status: RunStatus | None = None
    ) -> OptimizationRun:
        """Returns a NEW ``OptimizationRun`` with ``state`` (and
        optionally ``status``) replacing the current ones -- identical
        to ``SimulationRun.with_state()`` (spec 09 §10)."""
        return dataclasses.replace(
            self, state=state, status=status if status is not None else self.status
        )
