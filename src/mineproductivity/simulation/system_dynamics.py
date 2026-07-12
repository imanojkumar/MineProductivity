"""``SystemDynamicsModel``: interface-only extension point (design
spec §15) -- no concrete implementation ships in this package, by
explicit design.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
No stock-and-flow integration method (Euler, Runge-Kutta, or
otherwise) is chosen or shipped: choosing one is a modeling decision
this package does not make on the implementer's behalf (design spec
§15). ``_step`` is called once per fixed timestep with ``dt`` supplied
by a ``SimulationClock`` in ``TimeProgressionMode.FIXED_TIMESTEP``
mode (§11) -- the model itself never decides its own step size,
keeping time-progression policy entirely in ``SimulationClock``/
``Scenario``, not scattered across model implementations. The
``"SYSTEMDYNAMICS"`` code namespace mirrors ``"MONTECARLO"``'s own
spec-exampled convention (§29), compacted the same way.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta

from mineproductivity.simulation.abstractions import (
    SimulationContext,
    SimulationModel,
    _enforce_category,
)
from mineproductivity.simulation.metadata import SimulationCategory
from mineproductivity.simulation.state import SimulationState

__all__ = ["SystemDynamicsModel"]


class SystemDynamicsModel(SimulationModel, ABC):
    """The contract a future system-dynamics plugin implements. THIS
    MODULE SHIPS NO CONCRETE SUBCLASS (design spec §15, §35's
    interface-purity proof)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "SYSTEMDYNAMICS", SimulationCategory.SYSTEM_DYNAMICS)

    @abstractmethod
    def _step(
        self, state: SimulationState, *, context: SimulationContext, dt: timedelta
    ) -> SimulationState:
        """One fixed timestep of length ``dt`` -- no default
        implementation exists or is intended here (design spec §15)."""
