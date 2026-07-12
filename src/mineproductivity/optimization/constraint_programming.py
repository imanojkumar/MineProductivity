"""``ConstraintProgrammingModel``: interface-only extension point
(design spec §13) -- no concrete implementation ships in this package,
by explicit design (ADR-0010; a concrete subclass is a solver
*adapter* plugin, §17 -- this package never imports any third-party
solver library).
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

__all__ = ["ConstraintProgrammingModel"]


class ConstraintProgrammingModel(OptimizationModel, ABC):
    """The contract a future constraint-programming adapter plugin
    implements. THIS MODULE SHIPS NO CONCRETE SUBCLASS (design spec
    §13, §35's interface-purity proof)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "CP", OptimizationCategory.CONSTRAINT_PROGRAMMING)

    @abstractmethod
    def _solve_cp(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        """Solve the constraint program -- no default implementation
        exists or is intended here (design spec §13)."""
