"""``SimulationState``: one run's simulated condition as of the last
executed step or trial (design spec §10).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseValueObject`` is reused verbatim as the base, and the
``MappingProxyType``-freezing convention for ``Mapping``-typed fields
is reused exactly as ``digital_twin.state``/``decision.result`` already
established. ``attributes`` is deliberately an open
``Mapping[str, Any]`` rather than a typed field set -- a Monte Carlo
haul-cycle model's simulated attributes share nothing structurally with
a system-dynamics stockpile model's -- mirroring
``digital_twin.TwinState.attributes``' identical escape hatch (spec 08
§12, design spec §6's own state.py entry).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.simulation.exceptions import SimulationValidationError

__all__ = ["SimulationState"]


@dataclasses.dataclass(frozen=True, slots=True)
class SimulationState(BaseValueObject):
    """One run's simulated attributes and simulated time as of the last
    executed step or trial (design spec §10). A frozen value object,
    not an entity -- the entity (continuous identity over an
    execution's lifetime) is ``SimulationRun`` itself; ``SimulationState``
    is what a run currently points to, exactly the identity/value
    distinction ``digital_twin.Twin``/``TwinState`` already draw one
    layer down (spec 08 §12).

    ``simulated_time`` is simulated, never wall-clock, time -- advanced
    by ``SimulationClock`` (§11) under whichever ``TimeProgressionMode``
    the executing model's category prescribes.

    Examples
    --------
    >>> from datetime import timezone
    >>> state = SimulationState(
    ...     attributes={"queue_len": 4, "tonnes_moved": 1850.0},
    ...     simulated_time=datetime(2026, 7, 8, tzinfo=timezone.utc),
    ... )
    >>> state.attributes["queue_len"]
    4
    >>> SimulationState(attributes={}, simulated_time=datetime(2026, 7, 8, tzinfo=timezone.utc))
    Traceback (most recent call last):
        ...
    mineproductivity.simulation.exceptions.SimulationValidationError: SimulationState.attributes must not be empty
    """

    attributes: Mapping[str, Any]
    simulated_time: datetime

    def _normalize(self) -> None:
        super(SimulationState, self)._normalize()
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def validate(self) -> None:
        if not self.attributes:
            raise SimulationValidationError("SimulationState.attributes must not be empty")
