"""``Visualization``: the "Visualization-as-object" root, plus
``VisualizationContext`` (the caller-assembled evidence bundle) and
the ``VisualizationCategory``/``VisualizationMetadata`` registration
schema (design spec §8, §26 -- the locked §6 package structure hosts
metadata here rather than in a dedicated module).

Reuse audit: ``VisualizationContext`` mirrors ``agents.AgentContext``
(spec 11 §8) one layer up, extended with ``agent_audit_entries``
(each ``AgentAuditEntry`` already carries the ``AgentResult`` it
recorded, so no separate agent-results field is needed). Evidence is
read, never re-derived (§3.2); assembly happens once, at construction;
the caller-assembles pattern is used exclusively. ``Visualization``
shares one abstract method (``_render``) across all eight categories,
mirroring ``decision.DecisionModel``'s/``agents.Agent``'s
shared-method posture: every category answers the same underlying
question -- given evidence and a rendering context, produce a
structured presentation of it. THIS MODULE SHIPS NO CONCRETE SUBCLASS
-- choosing a specific charting library, templating engine, or
document-generation library is exactly the kind of implementation
decision this package's charter (§3.1, §3.5, §4) excludes.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from mineproductivity.agents import AgentAuditEntry
from mineproductivity.analytics import AnalyticsResult
from mineproductivity.core import BaseMetadata
from mineproductivity.decision import DecisionResult
from mineproductivity.digital_twin import TwinSnapshot
from mineproductivity.kpis import KPIResult
from mineproductivity.optimization import OptimizationResult
from mineproductivity.simulation import SimulationResult

from mineproductivity.visualization.exceptions import VisualizationValidationError

if TYPE_CHECKING:
    from mineproductivity.visualization.presentation import PresentationModel
    from mineproductivity.visualization.widget import Widget

__all__ = [
    "Visualization",
    "VisualizationCategory",
    "VisualizationContext",
    "VisualizationMetadata",
]


class VisualizationCategory(Enum):
    """Closed enum -- adding a member is a governance-reviewed change,
    mirroring ``agents.AgentCategory``'s closed-enum rule (spec 11
    §29): four general-purpose presentation shapes and four
    domain-specific views (design spec §17, §26)."""

    CHART = "chart"
    GRAPH = "graph"
    KPI_CARD = "kpi_card"
    TIMELINE = "timeline"
    SIMULATION_PLAYBACK = "simulation_playback"
    DIGITAL_TWIN_VIEW = "digital_twin_view"
    OPTIMIZATION_COMPARISON = "optimization_comparison"
    AGENT_EXPLANATION = "agent_explanation"


@dataclasses.dataclass(frozen=True, slots=True)
class VisualizationMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable
    ``Visualization`` type (design spec §26). ``code`` names a
    **type** (e.g. ``"KPI_CARD.Standard"``), never a ``Widget.code``.

    Examples
    --------
    >>> meta = VisualizationMetadata(
    ...     code="KPI_CARD.Standard",
    ...     category=VisualizationCategory.KPI_CARD,
    ...     description="A single-KPI headline card.",
    ... )
    >>> meta.name
    'KPI_CARD.Standard'
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    category: VisualizationCategory = dataclasses.field(kw_only=True)
    description: str = dataclasses.field(kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(VisualizationMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise VisualizationValidationError("VisualizationMetadata.code must not be empty")
        if not isinstance(self.category, VisualizationCategory):
            raise VisualizationValidationError(
                f"VisualizationMetadata.category must be a VisualizationCategory member, "
                f"got {self.category!r}"
            )
        super(VisualizationMetadata, self).validate()


class VisualizationContext:
    """Bundles the evidence a ``Visualization`` may need (design spec
    §8) -- carried once, at construction; this package renders exactly
    what the caller already assembled and never fetches additional
    evidence on its own initiative (§31).

    Examples
    --------
    >>> context = VisualizationContext()
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
        agent_audit_entries: Sequence[AgentAuditEntry] = (),
    ) -> None:
        self.kpi_results = tuple(kpi_results)
        self.analytics_results = tuple(analytics_results)
        self.decision_results = tuple(decision_results)
        self.twin_snapshot = twin_snapshot
        self.simulation_results = tuple(simulation_results)
        self.optimization_results = tuple(optimization_results)
        self.agent_audit_entries = tuple(agent_audit_entries)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(kpi_results={self.kpi_results!r}, "
            f"analytics_results={self.analytics_results!r}, "
            f"decision_results={self.decision_results!r}, "
            f"twin_snapshot={self.twin_snapshot!r}, "
            f"simulation_results={self.simulation_results!r}, "
            f"optimization_results={self.optimization_results!r}, "
            f"agent_audit_entries={self.agent_audit_entries!r})"
        )


class Visualization(ABC):
    """The root of every registrable visualization type (design spec
    §8) -- the eighth package-defining "as-object" root in this
    series, whose category members (§26) are presentation roles rather
    than algorithmic paradigms.

    **Statelessness.** Every subclass, of every category, is stateless
    -- no instance attribute is mutated by any ``_render``
    implementation (§26, §29); statefulness lives entirely in
    ``Dashboard`` (§10), so the same registered ``Visualization`` type
    can back many concurrent ``Widget``\\ s safely.

    **Qualify, don't coerce** (§30): no ``_render`` implementation
    raises for a legitimately incomplete widget binding or empty
    evidence -- it returns a ``PresentationModel`` carrying a warning
    instead.
    """

    meta: ClassVar[VisualizationMetadata]

    @abstractmethod
    def _render(self, widget: Widget, *, context: VisualizationContext) -> PresentationModel:
        """Given ``widget``'s binding and ``context``'s evidence,
        produce the structured, backend-independent presentation of it
        (design spec §8)."""
