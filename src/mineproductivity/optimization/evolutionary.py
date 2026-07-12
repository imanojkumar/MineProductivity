"""``EvolutionaryMetaheuristicModel``: interface-only extension point
(design spec §15) -- no concrete implementation ships in this package,
by explicit design (ADR-0010; a concrete subclass is a solver
*adapter* plugin, §17).

``_iterate`` is called repeatedly by ``OptimizationExecutor`` until
convergence or an iteration bound (§10, §15); all randomness derives
from a seed carried in ``problem.parameters``/``state.attributes``,
never mutable internal generator state (§33, §34's recorded
anti-pattern), so trajectories are reproducible independent of
execution order.
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
from mineproductivity.optimization.state import OptimizationState

__all__ = ["EvolutionaryMetaheuristicModel"]


class EvolutionaryMetaheuristicModel(OptimizationModel, ABC):
    """The contract a future evolutionary/metaheuristic adapter plugin
    implements. THIS MODULE SHIPS NO CONCRETE SUBCLASS (design spec
    §15, §35's interface-purity proof)."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _enforce_category(cls, "EVOLUTIONARY", OptimizationCategory.EVOLUTIONARY_METAHEURISTIC)

    @abstractmethod
    def _iterate(
        self,
        problem: OptimizationProblem,
        state: OptimizationState,
        *,
        context: OptimizationContext,
    ) -> OptimizationState:
        """One generation/step of the metaheuristic search -- no
        default implementation exists or is intended here (design spec
        §15)."""
