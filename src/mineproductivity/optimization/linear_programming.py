"""``LinearProgrammingModel``: interface-only extension point (design
spec §11) -- no concrete implementation ships in this package, by
explicit design (ADR-0010: choosing a solver library or algorithm is
exactly the scope this package's charter excludes; a concrete subclass
is a solver *adapter* plugin, §17, translating ``OptimizationProblem``
into its own library's modeling API -- this package never imports
any third-party solver library).

An LP-category problem admits CONTINUOUS decision variables only
(§11) -- the executor rejects a mismatched pairing before dispatch
(§27).
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

__all__ = ["LinearProgrammingModel"]


class LinearProgrammingModel(OptimizationModel, ABC):
    """The contract a future linear-programming adapter plugin
    implements. THIS MODULE SHIPS NO CONCRETE SUBCLASS (design spec
    §11, §35's interface-purity proof)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "LP", OptimizationCategory.LINEAR_PROGRAMMING)

    @abstractmethod
    def _solve_lp(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        """Solve the linear program -- no default implementation exists
        or is intended here (design spec §11)."""
