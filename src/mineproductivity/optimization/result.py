"""``OptimizationResult``/``ParetoResult``: every concrete outcome
type this package produces (design spec §18).

Reuse audit: ``core.BaseValueObject`` reused verbatim; ``solution`` --
a mapping from each ``DecisionVariable.name`` to its optimal value --
IS the operational plan; no separate ``Plan`` wrapper is introduced
(§18). A legitimately infeasible problem is expressed as
``feasible=False`` plus a warning, never an exception (§28).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime, timezone
from types import MappingProxyType

from mineproductivity.core import BaseValueObject

__all__ = ["OptimizationResult", "ParetoResult"]


@dataclasses.dataclass(frozen=True, slots=True)
class OptimizationResult(BaseValueObject):
    """The shared envelope every concrete optimization outcome
    composes -- mirrors ``simulation.SimulationResult``'s role
    (spec 09 §18).

    Examples
    --------
    >>> result = OptimizationResult(objective_value=42.0, solution={"trucks": 7.0})
    >>> result.feasible, result.solution["trucks"]
    (True, 7.0)
    """

    run_id: str = dataclasses.field(default="")
    computed_at: datetime = dataclasses.field(default_factory=lambda: datetime.now(timezone.utc))
    warnings: tuple[str, ...] = dataclasses.field(default=())
    feasible: bool = dataclasses.field(default=True, kw_only=True)
    objective_value: float | None = dataclasses.field(default=None, kw_only=True)
    solution: Mapping[str, float] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        super(OptimizationResult, self)._normalize()
        object.__setattr__(self, "solution", MappingProxyType(dict(self.solution)))


@dataclasses.dataclass(frozen=True, slots=True)
class ParetoResult(OptimizationResult):
    """The outcome of a ``MultiObjectiveModel`` search (design spec
    §14, §18) -- a set of mutually non-dominated candidates, not a
    single winner; the trade-off surface lives entirely in ``front``.

    Examples
    --------
    >>> pareto = ParetoResult(front=(OptimizationResult(objective_value=1.0),))
    >>> len(pareto.front)
    1
    """

    front: tuple[OptimizationResult, ...] = dataclasses.field(kw_only=True)
