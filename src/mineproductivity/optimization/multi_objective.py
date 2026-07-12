"""``MultiObjectiveModel``: interface-only extension point (design
spec §14) -- no concrete implementation ships in this package, by
explicit design (ADR-0010; a concrete subclass is a solver *adapter*
plugin, §17 -- this package never imports any third-party solver
library).

A multi-objective problem declares two or more ``Objective`` entries
(§14) -- the executor rejects a single-objective pairing before
dispatch (§27). The result is a Pareto front of mutually non-dominated
candidates, never a single scalarized winner imposed by this package.
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
from mineproductivity.optimization.result import ParetoResult

__all__ = ["MultiObjectiveModel"]


class MultiObjectiveModel(OptimizationModel, ABC):
    """The contract a future multi-objective adapter plugin implements.
    THIS MODULE SHIPS NO CONCRETE SUBCLASS (design spec §14, §35's
    interface-purity proof)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "MULTIOBJECTIVE", OptimizationCategory.MULTI_OBJECTIVE)

    @abstractmethod
    def _solve_pareto(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> ParetoResult:
        """Search the trade-off surface -- no default implementation
        exists or is intended here (design spec §14)."""
