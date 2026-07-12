"""``DiscreteEventModel``: interface-only extension point (design spec
§14) -- no concrete implementation ships in this package, by explicit
design.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
No event-queue scheduling policy is chosen or shipped: choosing one is
a modeling decision this package does not make on the implementer's
behalf (design spec §14). ``_advance`` returns both the next
``SimulationState`` and the time delta until that state becomes
current -- ``SimulationExecutor`` uses the returned delta to drive a
``SimulationClock`` in ``TimeProgressionMode.NEXT_EVENT`` (§11),
rather than the clock deciding the step size unilaterally. The
``"DISCRETEEVENT"`` code namespace mirrors ``"MONTECARLO"``'s own
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

__all__ = ["DiscreteEventModel"]


class DiscreteEventModel(SimulationModel, ABC):
    """The contract a future discrete-event plugin implements. THIS
    MODULE SHIPS NO CONCRETE SUBCLASS (design spec §14, §35's
    interface-purity proof)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "DISCRETEEVENT", SimulationCategory.DISCRETE_EVENT)

    @abstractmethod
    def _advance(
        self, state: SimulationState, *, context: SimulationContext
    ) -> tuple[SimulationState, timedelta]:
        """Advance to the next scheduled event: the next
        ``SimulationState`` plus the time delta until it becomes
        current -- no default implementation exists or is intended
        here (design spec §14)."""
