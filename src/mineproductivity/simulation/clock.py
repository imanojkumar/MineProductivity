"""``SimulationClock``/``TimeProgressionMode``: time progression
(design spec §11).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
Standard-library ``datetime``/``timedelta`` only, per design spec §6's
own dependency entry -- no lower-package time concept exists to reuse
(``events.AsOf`` is a point-in-time *reference*, not a progression
mechanism), and no new one beyond this small utility is introduced.
The clock holds no dependency on any specific ``SimulationModel``
category (§11): ``SimulationExecutor`` selects which
``TimeProgressionMode`` applies from the registered model's
``SimulationCategory``, never by inspecting the model's concrete type.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from mineproductivity.simulation.exceptions import SimulationValidationError

__all__ = ["SimulationClock", "TimeProgressionMode"]


class TimeProgressionMode(Enum):
    """Which of the three interface-only methodologies (design spec
    §13-§15) a ``SimulationClock`` is paced for."""

    FIXED_TIMESTEP = "fixed_timestep"  # system dynamics
    NEXT_EVENT = "next_event"  # discrete event
    TRIAL_BASED = "trial_based"  # Monte Carlo -- repeated independent trials, no continuous time


class SimulationClock:
    """Represents how simulated time advances for a given
    ``TimeProgressionMode`` (design spec §11): a fixed-timestep clock
    advances by a constant ``dt`` each step; a next-event clock
    advances directly by the delta the model's ``_advance`` returned;
    a trial-based clock does not advance continuous time at all --
    each trial is independent, and 'time' within a trial is whatever
    the concrete ``MonteCarloModel`` implementation defines it to be.

    Examples
    --------
    >>> clock = SimulationClock(mode=TimeProgressionMode.FIXED_TIMESTEP, dt=timedelta(minutes=5))
    >>> clock.advance(datetime(2026, 7, 8)).minute
    5
    >>> next_event = SimulationClock(mode=TimeProgressionMode.NEXT_EVENT)
    >>> next_event.advance(datetime(2026, 7, 8), delta=timedelta(minutes=17)).minute
    17
    >>> trial = SimulationClock(mode=TimeProgressionMode.TRIAL_BASED)
    >>> trial.advance(datetime(2026, 7, 8)) == datetime(2026, 7, 8)
    True
    """

    def __init__(self, *, mode: TimeProgressionMode, dt: timedelta | None = None) -> None:
        if mode is TimeProgressionMode.FIXED_TIMESTEP and dt is None:
            raise SimulationValidationError("SimulationClock in FIXED_TIMESTEP mode requires a dt")
        self.mode = mode
        self.dt = dt

    def advance(self, current: datetime, *, delta: timedelta | None = None) -> datetime:
        """The next simulated instant after ``current``. In
        ``NEXT_EVENT`` mode ``delta`` is the model-supplied time until
        the next scheduled event (design spec §14) and is required; in
        ``FIXED_TIMESTEP`` mode the constructor-fixed ``dt`` governs
        and ``delta`` is ignored; in ``TRIAL_BASED`` mode continuous
        time never advances."""
        if self.mode is TimeProgressionMode.FIXED_TIMESTEP:
            assert self.dt is not None  # guaranteed by the constructor guard
            return current + self.dt
        if self.mode is TimeProgressionMode.NEXT_EVENT:
            if delta is None:
                raise SimulationValidationError(
                    "SimulationClock in NEXT_EVENT mode requires a delta per advance() call"
                )
            return current + delta
        return current

    def __repr__(self) -> str:
        return f"{type(self).__name__}(mode={self.mode!r}, dt={self.dt!r})"
