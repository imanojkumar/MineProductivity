"""Root-cause interfaces (design spec §18) -- interface only.

``RootCauseAnalyzer`` is the contract a future root-cause-analysis
plugin implements. This module ships no concrete subclass: identifying
*why* a threshold was breached (which upstream signal, equipment, or
process step is the likely cause) is a causal-inference problem,
exactly the kind of modeling decision this package deliberately does
not make (§3.1, §3.4) -- the same reasoning ``analytics.forecasting``
already states for why it ships no concrete ``ForecastingModel``
subclass (ADR-0006's "Alternatives Rejected" section, reapplied at this
layer by ADR-0007's own "Alternatives Rejected" section: "scope creep
into causal inference and simulation," "premature commitment to an
interface's shape via its first implementation"). Defining the contract
now lets a future, independently-versioned plugin (or a future
``agents``/``digital_twin`` capability, §36) register against a stable
interface.

No new result type is introduced: ``RootCauseResult`` and
``ConfidenceScore`` already exist in ``result.py`` (Phase 07.1) -- a
root-cause finding is a set of candidate causes plus a confidence
weight, exactly what those two existing types already compose.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.result import Alert, Recommendation, RootCauseResult

__all__ = ["RootCauseAnalyzer"]


class RootCauseAnalyzer(DecisionModel, ABC):
    """The contract a future root-cause-analysis plugin implements. THIS
    MODULE SHIPS NO CONCRETE SUBCLASS -- identifying *why* a threshold
    was breached is a causal-inference problem this package's charter
    (§3.4) excludes.

    Leaves :meth:`~mineproductivity.decision.abstractions.DecisionModel._decide`
    abstract (inherited, unoverridden) exactly as every other category
    base in this package does (``DecisionStrategy``, ``RankingStrategy``)
    -- only a concrete subclass decides how its own ``_decide`` relates
    to ``_analyze``, since no concrete subclass ships here to make that
    decision on a future plugin's behalf.
    """

    @abstractmethod
    def _analyze(
        self, symptom: Recommendation | Alert, *, context: DecisionContext
    ) -> RootCauseResult:
        """Identify candidate causes for ``symptom`` (an already-produced
        ``Recommendation`` or ``Alert``), returning a
        :class:`~mineproductivity.decision.result.RootCauseResult`
        (``candidate_causes``, ``confidence``)."""
