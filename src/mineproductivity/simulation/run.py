"""``SimulationRun``/``RunStatus``: simulation execution's stateful
core (design spec §10).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseEntity[str]`` is reused by literal inheritance, following
``digital_twin.Twin``'s own precedent (spec 08 §3.3, §8) exactly --
``__eq__``/``__hash__`` inherited unchanged (identity-based on ``id``,
ignoring ``state``/``status``), state changes producing a new instance
via :meth:`SimulationRun.with_state`, never in-place mutation. Unlike
``Twin``, ``SimulationRun`` carries no ``_apply``-style abstract
method of its own: a run's next ``SimulationState`` is produced by
whichever ``SimulationModel`` category method (§13-§15)
``SimulationExecutor`` dispatches to on the run's behalf --
``SimulationRun`` is the *record* of an execution, not the executor
itself (§10's own recorded difference from ``Twin``), which also makes
it concrete rather than abstract.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseEntity

from mineproductivity.simulation.state import SimulationState

__all__ = ["RunStatus", "SimulationRun"]


class RunStatus(Enum):
    """A ``SimulationRun``'s own operational lifecycle -- distinct in
    shape from ``digital_twin.TwinStatus`` (spec 08 §10), which tracks
    a twin instance's synchronization freshness; ``RunStatus`` instead
    tracks execution progress, with values shaped by what
    ``SimulationExecutor`` (design spec §10) actually does.
    ``COMPLETED`` and ``FAILED`` are terminal -- no transition leads
    out of either (§10's state diagram)."""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class SimulationRun(BaseEntity[str]):
    """The root of one executing or completed simulation --
    'Run-as-entity,' following ``digital_twin.Twin``'s own precedent
    (spec 08 §3.3, §8) exactly: ``id`` (inherited) is the run's
    identity, and representing a state change means producing a NEW
    ``SimulationRun`` instance via :meth:`with_state`, never mutating
    fields in place.

    **Thread safety.** ``SimulationRun`` instances are immutable --
    trivially safe to read and share across threads (design spec §32).

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> run = SimulationRun(
    ...     id="RUN-1",
    ...     scenario_code="FLEET.NightShiftSurge",
    ...     state=SimulationState(
    ...         attributes={"provisioned": True},
    ...         simulated_time=datetime(2026, 7, 8, tzinfo=timezone.utc),
    ...     ),
    ... )
    >>> run.status
    <RunStatus.SCHEDULED: 'scheduled'>
    >>> run.with_state(run.state, status=RunStatus.RUNNING).status
    <RunStatus.RUNNING: 'running'>
    >>> run.status  # the original instance is untouched
    <RunStatus.SCHEDULED: 'scheduled'>
    """

    scenario_code: str
    state: SimulationState
    status: RunStatus = dataclasses.field(default=RunStatus.SCHEDULED)

    def with_state(
        self, state: SimulationState, *, status: RunStatus | None = None
    ) -> SimulationRun:
        """Returns a NEW ``SimulationRun`` instance with ``state`` (and
        optionally ``status``) replacing the current ones -- the
        ``dataclasses.replace``-style helper ``core.BaseEntity``'s own
        docstring anticipates, identical to ``Twin.with_state()``
        (spec 08 §8)."""
        return dataclasses.replace(
            self, state=state, status=status if status is not None else self.status
        )
