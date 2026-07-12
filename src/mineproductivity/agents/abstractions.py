"""``Agent``: the "Agent-as-object" root, and ``AgentContext``, the
collaborator/evidence bundle a concrete agent reasons over (design
spec §8).

Reuse audit: ``AgentContext`` mirrors
``optimization.OptimizationContext`` (spec 10 §8) one layer up,
extended with ``optimization_results`` -- an agent may read an
already-solved plan a not-yet-solved ``OptimizationProblem`` could
never reference. Evidence is read, never re-derived (§3.2), and
assembly happens once, at construction -- never re-fetched per retry
or per delegation (§27, §36). Per ``decision.DecisionContext``'s own
established convention (spec 07 §8), the caller-assembles pattern is
used exclusively. ``Agent`` shares one abstract method (``_act``)
across all ten categories, mirroring ``decision.DecisionModel``'s
shared-``_decide`` posture (spec 07 §8) rather than ``simulation``'s/
``optimization``'s no-shared-method posture: every category answers
the same underlying question -- given a task and context, decide what
should happen next. THIS MODULE SHIPS NO CONCRETE SUBCLASS --
choosing a specific reasoning backend (a hosted large-language-model
service, a local model, a rule engine) is exactly the kind of
implementation decision this package's charter (§3.1, §3.5, §4)
excludes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

from mineproductivity.analytics import AnalyticsResult
from mineproductivity.decision import DecisionResult
from mineproductivity.digital_twin import TwinSnapshot
from mineproductivity.kpis import KPIResult
from mineproductivity.optimization import OptimizationResult
from mineproductivity.simulation import SimulationResult

from mineproductivity.agents.metadata import AgentMetadata

if TYPE_CHECKING:
    from mineproductivity.agents.result import AgentResult
    from mineproductivity.agents.task import Task

__all__ = ["Agent", "AgentContext"]


class AgentContext:
    """Bundles the evidence an ``Agent`` may need (design spec §8) --
    carried once, at construction; every fact an agent reasons over
    has a stable, structured home in a lower package, never a
    re-derivation of its own.

    Examples
    --------
    >>> context = AgentContext()
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
        optimization_results: Sequence[OptimizationResult] = (),
    ) -> None:
        self.kpi_results = tuple(kpi_results)
        self.analytics_results = tuple(analytics_results)
        self.decision_results = tuple(decision_results)
        self.twin_snapshot = twin_snapshot
        self.simulation_results = tuple(simulation_results)
        self.optimization_results = tuple(optimization_results)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(kpi_results={self.kpi_results!r}, "
            f"analytics_results={self.analytics_results!r}, "
            f"decision_results={self.decision_results!r}, "
            f"twin_snapshot={self.twin_snapshot!r}, "
            f"simulation_results={self.simulation_results!r}, "
            f"optimization_results={self.optimization_results!r})"
        )


class Agent(ABC):
    """The root of every registrable agent type (design spec §8) --
    the direct counterpart of ``optimization.OptimizationModel`` one
    layer down, whose category members (§29) are domain roles rather
    than algorithmic paradigms.

    **Statelessness.** Every subclass, of every category, is stateless
    -- no instance attribute is mutated by any ``_act`` implementation
    (§29, §32); statefulness lives entirely in ``Task`` (§11), so the
    same registered ``Agent`` type can execute many concurrent
    ``Task``\\ s safely.

    **Qualify, don't coerce** (§30): no ``_act`` implementation raises
    for a legitimately incomplete or ambiguous task -- it returns an
    ``AgentResult`` carrying a warning instead.
    """

    meta: ClassVar[AgentMetadata]

    @abstractmethod
    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        """Given ``task`` and ``context``, decide what should happen
        next -- the one shared reasoning call every category answers
        (design spec §8)."""
