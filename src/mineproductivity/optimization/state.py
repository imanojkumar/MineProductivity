"""``OptimizationState``: one run's condition as of the last solve or
iteration (design spec §10).

Reuse audit: ``core.BaseValueObject`` and the
``MappingProxyType``-freezing convention reused verbatim; ``attributes``
is the same open escape hatch ``simulation.SimulationState.attributes``
establishes (spec 09 §10) -- an evolutionary population, an incumbent
solution, or a convergence trace share nothing structurally across
categories. Unlike a simulation, an optimization attempt has no
simulated time, so no time field exists here.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.optimization.exceptions import OptimizationValidationError

__all__ = ["OptimizationState"]


@dataclasses.dataclass(frozen=True, slots=True)
class OptimizationState(BaseValueObject):
    """One run's attributes as of the last executed solve or iteration
    -- a frozen value object; the entity is ``OptimizationRun`` (design
    spec §10). Deliberately not an ``OptimizationResult`` subclass
    (§18).

    Examples
    --------
    >>> OptimizationState(attributes={"incumbent": 42.0}).attributes["incumbent"]
    42.0
    """

    attributes: Mapping[str, Any]

    def _normalize(self) -> None:
        super(OptimizationState, self)._normalize()
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def validate(self) -> None:
        if not self.attributes:
            raise OptimizationValidationError("OptimizationState.attributes must not be empty")
