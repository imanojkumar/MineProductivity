"""``OptimizationMetadata``/``OptimizationCategory``: the minimal
registration schema for a discoverable
:class:`~mineproductivity.optimization.abstractions.OptimizationModel`
type (design spec §29).

Reuse audit: ``core.BaseMetadata`` reused verbatim; the whole module
mirrors ``simulation.metadata``/``digital_twin.metadata``
field-for-field, including the name-defaults-to-code convention.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseMetadata

from mineproductivity.optimization.exceptions import OptimizationValidationError

__all__ = ["OptimizationCategory", "OptimizationMetadata"]


class OptimizationCategory(Enum):
    """Closed enum -- adding a member is a governance-reviewed change,
    mirroring ``simulation.SimulationCategory``'s closed-enum rule
    (spec 09 §29)."""

    LINEAR_PROGRAMMING = "linear_programming"
    MIXED_INTEGER_PROGRAMMING = "mixed_integer_programming"
    CONSTRAINT_PROGRAMMING = "constraint_programming"
    MULTI_OBJECTIVE = "multi_objective"
    EVOLUTIONARY_METAHEURISTIC = "evolutionary_metaheuristic"
    NETWORK_OPTIMIZATION = "network_optimization"


@dataclasses.dataclass(frozen=True, slots=True)
class OptimizationMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable
    ``OptimizationModel`` type (design spec §29). ``code`` names a
    **type** (e.g. ``"MIP.FleetAllocation"``), never a run.

    Examples
    --------
    >>> meta = OptimizationMetadata(
    ...     code="MIP.FleetAllocation",
    ...     category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
    ...     description="Fleet/shift allocation as a MIP.",
    ... )
    >>> meta.name
    'MIP.FleetAllocation'
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    category: OptimizationCategory = dataclasses.field(kw_only=True)
    description: str = dataclasses.field(kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(OptimizationMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise OptimizationValidationError("OptimizationMetadata.code must not be empty")
        if not isinstance(self.category, OptimizationCategory):
            raise OptimizationValidationError(
                f"OptimizationMetadata.category must be an OptimizationCategory member, "
                f"got {self.category!r}"
            )
        super(OptimizationMetadata, self).validate()
