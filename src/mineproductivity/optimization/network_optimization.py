"""``NetworkOptimizationModel``: interface-only extension point
(design spec §16) -- no concrete implementation ships in this package,
by explicit design (ADR-0010; a concrete subclass is a solver
*adapter* plugin, §17).

A network problem's graph structure is carried in
``OptimizationProblem.parameters`` -- no first-class ``Node``/``Edge``
value object is introduced for a shape exactly one category reads
(§16).
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

__all__ = ["NetworkOptimizationModel"]


class NetworkOptimizationModel(OptimizationModel, ABC):
    """The contract a future network-optimization adapter plugin
    implements. THIS MODULE SHIPS NO CONCRETE SUBCLASS (design spec
    §16, §35's interface-purity proof)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "NETWORK", OptimizationCategory.NETWORK_OPTIMIZATION)

    @abstractmethod
    def _solve_network(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        """Solve the network-flow/assignment/routing program -- no
        default implementation exists or is intended here (design spec
        §16)."""
