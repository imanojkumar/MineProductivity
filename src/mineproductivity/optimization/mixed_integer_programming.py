"""``MixedIntegerProgrammingModel``: interface-only extension point
(design spec §12) -- no concrete implementation ships in this package,
by explicit design (ADR-0010; a concrete subclass is a solver
*adapter* plugin, §17 -- this package never imports any third-party
solver library).

Goal programming is an ``OptimizationProblem``-authoring pattern
against this category (or LP), never a separate category or ABC
(§12): deviation variables are ordinary ``DecisionVariable`` entries
and goal levels ordinary ``Constraint`` entries.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from mineproductivity.optimization.abstractions import (
    OptimizationContext,
    OptimizationModel,
    _enforce_category,
)
from mineproductivity.optimization.metadata import OptimizationCategory
from mineproductivity.optimization.problem import OptimizationProblem
from mineproductivity.optimization.result import OptimizationResult

__all__ = ["MixedIntegerProgrammingModel"]


class MixedIntegerProgrammingModel(OptimizationModel, ABC):
    """The contract a future mixed-integer-programming adapter plugin
    implements. THIS MODULE SHIPS NO CONCRETE SUBCLASS (design spec
    §12, §35's interface-purity proof)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "MIP", OptimizationCategory.MIXED_INTEGER_PROGRAMMING)

    @abstractmethod
    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        """Solve the mixed-integer program -- no default implementation
        exists or is intended here (design spec §12)."""
