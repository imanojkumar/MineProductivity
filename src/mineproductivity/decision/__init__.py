"""``mineproductivity.decision`` -- the platform's prescriptive layer,
built directly on top of ``analytics``.

Answers the question ``analytics`` deliberately does not: given a
trend, a benchmark classification, a baseline, or a confidence
interval, what should the business actually do about it? ``decision``
consumes already-correct ``kpis.KPIResult``/``analytics.AnalyticsResult``
evidence and produces recommended, ranked, explained, actionable
decisions as new, equally discoverable, equally versioned result
objects -- never recomputing a KPI value, a trend, or a benchmark
classification itself.

**Phase 07.1 -- Decision Intelligence Foundation** implements every
component required before concrete decision models can exist:
``DecisionModel`` (ABC)/``DecisionContext`` (§8); ``DecisionMetadata``/
``DecisionCategory`` (§30); the full ``DecisionResult`` family (§28);
``Threshold`` (§13); ``DecisionPipeline``/``PipelineStage``/``ModelStage``
(§9); ``REGISTRY``/``register`` (§32); and the full exception hierarchy.

**Phase 07.2 -- Decision Rule Engine** implements rule evaluation,
policy governance, and the default decision strategy: ``Rule``/
``RuleEngine``/``RuleEngineStage`` (§10); ``Policy``/``DecisionStatus``
(§12); ``DecisionStrategy`` (ABC)/``ThresholdDecisionStrategy`` (§14),
self-registered into ``REGISTRY`` at import time.

**Phase 07.3 -- Decision Intelligence Analysis Layer** implements the
analytical capabilities that operate on already-produced
``Recommendation``/``DecisionResult`` objects: ``DecisionScorer``/
``ConfidenceScorer`` (§23, §24) -- the numeric weight backing ranking
and the trust weight backing how strongly a recommendation should be
acted on, the latter deriving from ``analytics.DataQualityScore`` when
present in a ``DecisionContext``'s evidence, never recomputing data
quality itself; ``RankingStrategy`` (ABC)/``WeightedScoreRanking`` (§16)
-- orders ``Recommendation``\\ s by ``DecisionScore.value``, descending,
self-registered into ``REGISTRY``; ``ExplanationBuilder``/
``ExplanationStage`` (§17) -- walks a ``Recommendation``'s provenance
into a structured, evidence-linked ``Explanation``; ``ActionPrioritizer``
(§20) -- assigns each ``RankedRecommendation`` an ``ActionPriority``
(urgency/impact/effort), a distinct question from ranking; and
``RootCauseAnalyzer`` (§18) -- an interface-only ABC with zero concrete
subclasses by design (ADR-0007), defining the contract a future causal-
inference plugin implements. ``DecisionContext`` gained a second,
Phase-07.3 extension (``recommendations``, alongside Phase 07.2's
``triggered_rules``) for the same reason: ``WeightedScoreRanking``/
``ExplanationStage`` operate over a *batch* of already-produced
``Recommendation``\\ s, not raw evidence (see
``abstractions.DecisionContext``'s own docstring).

**Phase 07.4 -- Decision Operational Services** completes the package:
``WhatIfEngine`` (§19) -- an interface-only ABC with zero concrete
subclasses by design, the decision-layer counterpart to
``RootCauseAnalyzer``, reusing ``events.AsOf``'s already-reserved
``scenario`` field rather than inventing a second scenario concept;
``ActionPlanner`` (§21) -- sequences prioritized actions into an
``ActionPlan``, respecting declared dependencies via its own narrow,
self-contained topological ordering (deliberately not
``kpis.DependencyGraph``, per §33's own anti-pattern entry);
``AlertGenerator`` (§22) -- produces an ``Alert`` from a
``ThresholdBreach`` or a high-severity ``Recommendation``, a pure value-
object factory with no channel-delivery side effects;
``RealTimeDecisionSession``/``BatchDecisionRunner`` (§25, §26) -- the
two execution modes, the live event-driven counterpart and the bounded,
scheduled-report counterpart of running one ``DecisionPipeline``, both
composing ``kpis.KPIEngine``/``analytics.BatchAnalyticsRunner`` rather
than recomputing anything themselves; and ``DecisionAuditTrail``/
``DecisionAuditEntry`` (§27, §28) -- the append-only accountability
record every operationally-actionable ``DecisionPipeline`` run should
feed, optionally wired into both execution modes. ``recommendation.py``
(§15, §6) holds the recommendation-generation logic with no public API
of its own, per §6's own entry for it -- ``ThresholdDecisionStrategy``'s
methods delegate ``Recommendation`` construction to it, keeping exactly
one summary-text/traceability format package-wide. This completes every
module design spec §6 enumerates -- ``decision`` is now feature-complete
per the Reference Implementation Blueprint. See the package's own
README.md for the full slice inventory and phase status.

``decision`` depends on ``core``, ``events``, ``ontology``, ``registry``,
``plugins``, ``connectors``, ``kpis``, and ``analytics`` -- and MUST
NEVER import ``digital_twin``, ``simulation``, ``optimization``,
``visualization``, or ``agents``, none of which this package may see.

Everything documented here is part of the public API and can be
imported directly from ``mineproductivity.decision``, e.g.::

    from mineproductivity.decision import DecisionModel, DecisionContext
"""

from __future__ import annotations

from mineproductivity.decision._registry import REGISTRY, register
from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.alerting import AlertGenerator
from mineproductivity.decision.audit import DecisionAuditEntry, DecisionAuditTrail
from mineproductivity.decision.batch import BatchDecisionRunner
from mineproductivity.decision.exceptions import (
    DecisionModelNotFoundError,
    DecisionValidationError,
    DecisionVersionConflictError,
    NoApplicablePolicyError,
    PolicyConflictError,
)
from mineproductivity.decision.explanation import ExplanationBuilder, ExplanationStage
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
from mineproductivity.decision.pipeline import DecisionPipeline, ModelStage, PipelineStage
from mineproductivity.decision.planning import ActionPlanner
from mineproductivity.decision.policy import DecisionStatus, Policy
from mineproductivity.decision.prioritization import ActionPrioritizer
from mineproductivity.decision.ranking import RankingStrategy, WeightedScoreRanking
from mineproductivity.decision.realtime import RealTimeDecisionSession
from mineproductivity.decision.result import (
    ActionPlan,
    ActionPriority,
    Alert,
    ConfidenceScore,
    DecisionResult,
    DecisionScore,
    Explanation,
    RankedRecommendation,
    Recommendation,
    RootCauseResult,
    ThresholdBreach,
    WhatIfResult,
)
from mineproductivity.decision.root_cause import RootCauseAnalyzer
from mineproductivity.decision.rules import Rule, RuleEngine, RuleEngineStage
from mineproductivity.decision.scoring import ConfidenceScorer, DecisionScorer
from mineproductivity.decision.strategy import DecisionStrategy, ThresholdDecisionStrategy
from mineproductivity.decision.thresholds import Threshold
from mineproductivity.decision.what_if import WhatIfEngine

__all__ = [
    "ActionPlan",
    "ActionPlanner",
    "ActionPrioritizer",
    "ActionPriority",
    "Alert",
    "AlertGenerator",
    "BatchDecisionRunner",
    "ConfidenceScore",
    "ConfidenceScorer",
    "DecisionAuditEntry",
    "DecisionAuditTrail",
    "DecisionCategory",
    "DecisionContext",
    "DecisionMetadata",
    "DecisionModel",
    "DecisionModelNotFoundError",
    "DecisionPipeline",
    "DecisionResult",
    "DecisionScore",
    "DecisionScorer",
    "DecisionStatus",
    "DecisionStrategy",
    "DecisionValidationError",
    "DecisionVersionConflictError",
    "Explanation",
    "ExplanationBuilder",
    "ExplanationStage",
    "ModelStage",
    "NoApplicablePolicyError",
    "PipelineStage",
    "Policy",
    "PolicyConflictError",
    "REGISTRY",
    "RankedRecommendation",
    "RankingStrategy",
    "RealTimeDecisionSession",
    "Recommendation",
    "RootCauseAnalyzer",
    "RootCauseResult",
    "Rule",
    "RuleEngine",
    "RuleEngineStage",
    "Threshold",
    "ThresholdBreach",
    "ThresholdDecisionStrategy",
    "WeightedScoreRanking",
    "WhatIfEngine",
    "WhatIfResult",
    "register",
]
