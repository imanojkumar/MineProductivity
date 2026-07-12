"""``OptimizationModel``: the "Optimization-as-object" root, and
``OptimizationContext``, the collaborator/evidence bundle a model's
category method reasons over (design spec §8).

Reuse audit: ``OptimizationContext`` mirrors
``simulation.SimulationContext`` (spec 09 §8) one layer up, extended
with ``twin_snapshot``/``simulation_results`` since ``optimization``
is permitted to consume both directly -- evidence is read, never
re-derived (§3.2). ``OptimizationModel`` deliberately carries no
shared abstract solve method: the six solving paradigms (§11-§16) are
structurally different enough that each category base declares its
own, the identical reasoning ``simulation.SimulationModel`` already
applied (spec 09 §8). Context assembly happens once, at construction
-- never re-fetched per solve or per iteration (§26, §36).
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import ClassVar

from mineproductivity.analytics import AnalyticsResult
from mineproductivity.decision import DecisionResult
from mineproductivity.digital_twin import TwinSnapshot
from mineproductivity.kpis import KPIResult
from mineproductivity.simulation import SimulationResult

from mineproductivity.optimization.exceptions import OptimizationValidationError
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata

__all__ = ["OptimizationContext", "OptimizationModel"]


class OptimizationContext:
    """Bundles the evidence an ``OptimizationModel`` may need (design
    spec §8) -- carried once, at construction; the executor never
    reaches back into a lower package on its own initiative.

    Examples
    --------
    >>> context = OptimizationContext()
    >>> context.kpi_results
    ()
    >>> context.twin_snapshot is None
    True
    """

    def __init__(
        self,
        *,
        kpi_results: Sequence[KPIResult] = (),
        analytics_results: Sequence[AnalyticsResult] = (),
        decision_results: Sequence[DecisionResult] = (),
        twin_snapshot: TwinSnapshot | None = None,
        simulation_results: Sequence[SimulationResult] = (),
    ) -> None:
        self.kpi_results = tuple(kpi_results)
        self.analytics_results = tuple(analytics_results)
        self.decision_results = tuple(decision_results)
        self.twin_snapshot = twin_snapshot
        self.simulation_results = tuple(simulation_results)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(kpi_results={self.kpi_results!r}, "
            f"analytics_results={self.analytics_results!r}, "
            f"decision_results={self.decision_results!r}, "
            f"twin_snapshot={self.twin_snapshot!r}, "
            f"simulation_results={self.simulation_results!r})"
        )


class OptimizationModel(ABC):
    """The root of every registrable optimization model type (design
    spec §8). Deliberately carries no shared abstract solve method;
    each category base (§11-§16) declares its own.

    **Statelessness.** Every subclass, of every category, is stateless
    -- no instance attribute is mutated by any category method (§29,
    §32); statefulness lives entirely in ``OptimizationRun`` (§10). An
    ``EvolutionaryMetaheuristicModel`` in particular derives all
    randomness from a seed carried in ``problem.parameters``/
    ``state.attributes``, never internal generator state (§33, §34).
    """

    meta: ClassVar[OptimizationMetadata]


def _enforce_category(
    cls: type[OptimizationModel], namespace: str, category: OptimizationCategory
) -> None:
    """Shared namespace/category-conformance check the six category
    bases (design spec §11-§16) run from their own
    ``__init_subclass__`` hooks (§27) -- package-internal, mirroring
    ``simulation.abstractions._enforce_category`` exactly. Abstract
    intermediates declaring no ``meta`` are skipped; a violation fails
    at class-definition (import) time."""
    if "meta" not in cls.__dict__:
        return
    code = cls.meta.code
    if not (code == namespace or code.startswith(f"{namespace}.")):
        raise OptimizationValidationError(
            f"{cls.__name__}.meta.code {code!r} must fall in the {namespace!r} namespace"
        )
    if cls.meta.category is not category:
        raise OptimizationValidationError(
            f"{cls.__name__}.meta.category must be {category!r}, got {cls.meta.category!r}"
        )
