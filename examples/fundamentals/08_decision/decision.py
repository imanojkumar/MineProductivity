"""Lesson 08 -- Decision: turning a measured drift into an explained action.

Lesson 07 left FL-NORTH degrading at roughly 12 t/h per shift. That is a
*characterisation*, not a decision. Someone still has to say: does this
breach policy, what should we do, why, and who can audit that reasoning
six months from now in an incident review?

That is the decision layer. Its discipline is strict: it re-derives
nothing. It consumes the governed KPI and the analytics judgement as
evidence, evaluates a *versioned policy*, and emits a recommendation that
carries its own explanation and evidence references.

Run: python examples/fundamentals/08_decision/decision.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.analytics import (
    AnalyticsContext,
    LinearTrendModel,
    TimeSeries,
    TimeSeriesPoint,
    TrendResult,
)
from mineproductivity.core import PredicateSpecification
from mineproductivity.decision import (
    BatchDecisionRunner,
    DecisionAuditTrail,
    DecisionContext,
    DecisionPipeline,
    ExplanationStage,
    ModelStage,
    Policy,
    RankedRecommendation,
    Recommendation,
    Rule,
    RuleEngineStage,
    Threshold,
    ThresholdDecisionStrategy,
    WeightedScoreRanking,
)
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.kpis import REGISTRY

WEEK_START = datetime(2026, 6, 22, 6, 0, tzinfo=timezone.utc)
SHIFT_ID = "A-2026-06-28"

# The site's governed target for the north fleet.
TPH_TARGET = 1_250.0

# The same fourteen shifts lesson 07 characterised (tonnes, operating hours).
SHIFT_LOG: list[tuple[float, float]] = [
    (15_600.0, 12.0),
    (15_480.0, 12.0),
    (15_720.0, 12.0),
    (15_360.0, 12.0),
    (15_240.0, 12.0),
    (15_120.0, 12.0),
    (14_880.0, 12.0),
    (14_760.0, 12.0),
    (14_640.0, 12.0),
    (14_400.0, 12.0),
    (14_280.0, 12.0),
    (14_160.0, 12.0),
    (13_920.0, 12.0),
    (13_800.0, 12.0),
]


def main() -> None:
    print("--- 1. Evidence, gathered -- never recomputed here ---")
    tph_kpi = REGISTRY.get("PROD.TPH")()
    points: list[TimeSeriesPoint] = []
    for index, (tonnes, hours) in enumerate(SHIFT_LOG):
        computed = tph_kpi.compute([{"payload_t": tonnes, "operating_h": hours}])
        assert computed.value is not None
        points.append(
            TimeSeriesPoint(
                timestamp=WEEK_START + timedelta(hours=12 * index), value=computed.value
            )
        )
    latest = tph_kpi.compute([{"payload_t": SHIFT_LOG[-1][0], "operating_h": SHIFT_LOG[-1][1]}])
    assert latest.value is not None

    # analyze() is the public contract; narrow to TrendResult to read its fields.
    analysed = LinearTrendModel().analyze(
        TimeSeries(points=tuple(points)),
        context=AnalyticsContext(event_store=_InMemoryEventStore()),
    )
    assert isinstance(analysed, TrendResult)
    trend = analysed
    print(f"KPI fact  : PROD.TPH = {latest.value:,.1f} t/h (target {TPH_TARGET:,.0f})")
    print(f"Analytics : {trend.model_code} direction={trend.direction!r} r^2={trend.r_squared:.3f}")
    print("(the decision layer will consume these two facts and derive neither)")

    print()
    print("--- 2. A versioned, governed Policy -- not an `if` buried in a script ---")
    rules: dict[str, Rule] = {
        "tph_below_target": PredicateSpecification(
            lambda ctx: any(r.value is not None and r.value < TPH_TARGET for r in ctx.kpi_results)
        ),
        "tph_trend_declining": PredicateSpecification(
            lambda ctx: any(
                isinstance(r, TrendResult) and r.direction == "decreasing"
                for r in ctx.analytics_results
            )
        ),
    }
    policy = Policy(
        code="PROD.NorthFleetUnderTarget",
        rules=rules,
        thresholds={
            "tph_below_target": Threshold(field="value", comparator="<", limit=TPH_TARGET),
            "tph_trend_declining": Threshold(field="trend.slope", comparator="<", limit=0.0),
        },
        strategy_code="STRATEGY.Threshold",
    )
    print(f"policy {policy.code!r} v{policy.version}")
    print(f"rules  : {sorted(policy.rules)}")
    print("(versioned: an auditor can ask which policy version produced a call)")

    print()
    print("--- 3. One audited pipeline run: evaluate rules, then recommend ---")
    context = DecisionContext(
        kpi_results=(latest,), analytics_results=(trend,), scope={"shift": SHIFT_ID}
    )
    strategy = ThresholdDecisionStrategy(policy=policy, severity="high")
    trail = DecisionAuditTrail()
    outcome = BatchDecisionRunner(
        pipeline=DecisionPipeline(stages=(RuleEngineStage(policy=policy), ModelStage(strategy))),
        audit_trail=trail,
    ).run(context)
    recommendation = outcome.unwrap()
    assert isinstance(recommendation, Recommendation)
    print(f"triggered: {recommendation.triggered_rules}")
    print(f"summary  : {recommendation.summary}")
    print(f"evidence : {recommendation.evidence}")

    print()
    print("--- 4. Declarative thresholds confirm the breach independently ---")
    for breach in strategy.check_thresholds(context):
        limit = breach.threshold
        print(
            f"  {limit.field} {limit.comparator} {limit.limit}"
            f"  (observed {breach.observed_value:,.4f})"
        )
    print("(the rule said 'this fired'; the threshold says 'by how much')")

    print()
    print("--- 5. Explain and rank -- an unexplained recommendation is not usable ---")
    ranked = (
        DecisionPipeline(stages=(ExplanationStage(), ModelStage(WeightedScoreRanking())))
        .run(
            DecisionContext(
                kpi_results=(latest,),
                analytics_results=(trend,),
                scope={"shift": SHIFT_ID},
                recommendations=(recommendation,),
            )
        )
        .unwrap()
    )
    assert isinstance(ranked, RankedRecommendation)
    print(f"rank={ranked.rank} score={ranked.score.value:.3f}")
    explanation = ranked.recommendation.explanation
    assert explanation is not None
    for premise in explanation.premises:
        print(f"  premise: {premise}")

    print()
    print("--- 6. The audit trail is the accountability record ---")
    entries = trail.query(scope={"shift": SHIFT_ID})
    print(f"{len(entries)} audited entry for shift {SHIFT_ID}")
    print("(append-only: six months later an incident review can reconstruct")
    print(" exactly which policy version fired, on what evidence, and why)")

    print()
    print("--- 7. What this package deliberately does NOT decide ---")
    print("decision.RootCauseAnalyzer and decision.WhatIfEngine are interfaces")
    print("with ZERO implementations (ADR-0007). The platform will tell you the")
    print("fleet is under target and declining -- it will not guess WHY without")
    print("a plugin that encodes your site's causal model. That refusal is the")
    print("feature: a fabricated root cause is worse than none.")


if __name__ == "__main__":
    main()
