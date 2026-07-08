"""The design spec §9 worked example, end-to-end: a fleet-availability
policy evaluated against a real ``UTIL.OEE`` fact and its week-long
trend -- gather evidence via ``kpis``/``analytics`` (never recomputed
here), evaluate rules, recommend, explain, rank, and audit.

Run: python examples/decision/01_pipeline_over_evidence.py
"""

from __future__ import annotations

from datetime import timezone

from _evidence import OEE_HISTORY, SHIFT_END, SHIFT_ID, build_engine, load_event_store

from mineproductivity.analytics import (
    AnalyticsContext,
    AnalyticsPipeline,
    BatchAnalyticsRunner,
    LinearTrendModel,
    TimeSeries,
    TrendResult,
)
from mineproductivity.analytics import ModelStage as AnalyticsModelStage
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
from mineproductivity.kpis import KPIResult

OEE_TARGET = 0.85


def main() -> None:
    print("--- 1. Evidence: UTIL.OEE for the shift, from the real KPIEngine ---")
    store = load_event_store()
    engine = build_engine(store)
    oee = engine.execute("UTIL.OEE", window="shift", scope={"shift": SHIFT_ID}).unwrap()
    assert oee.value is not None
    print(f"UTIL.OEE = {oee.value:.4f} (n={oee.n})")

    print()
    print("--- 2. Evidence: its week-long trend, from the real BatchAnalyticsRunner ---")
    history = [KPIResult(code="UTIL.OEE", value=value, unit="") for _, value in OEE_HISTORY]
    timestamps = [timestamp for timestamp, _ in OEE_HISTORY]
    series = TimeSeries.from_kpi_results([*history, oee], timestamps=[*timestamps, SHIFT_END])
    trend_runner = BatchAnalyticsRunner(
        pipeline=AnalyticsPipeline(stages=(AnalyticsModelStage(LinearTrendModel()),)),
        context=AnalyticsContext(event_store=store),
    )
    trend = trend_runner.run(series).unwrap()
    assert isinstance(trend, TrendResult)
    print(f"{trend.model_code}: direction={trend.direction!r} slope={trend.slope:.3e}")

    print()
    print("--- 3. A versioned, governed fleet-availability Policy ---")
    rules: dict[str, Rule] = {
        "oee_below_target": PredicateSpecification(
            lambda ctx: any(r.value is not None and r.value < OEE_TARGET for r in ctx.kpi_results)
        ),
        "oee_trend_declining": PredicateSpecification(
            lambda ctx: any(
                isinstance(r, TrendResult) and r.direction == "decreasing"
                for r in ctx.analytics_results
            )
        ),
    }
    policy = Policy(
        code="AVAIL.LowFleetAvailability",
        rules=rules,
        thresholds={
            "oee_below_target": Threshold(field="value", comparator="<", limit=OEE_TARGET),
            "oee_trend_declining": Threshold(field="trend.slope", comparator="<", limit=0.0),
        },
        strategy_code="STRATEGY.Threshold",
    )
    print(f"policy={policy.code!r} v{policy.version} rules={sorted(policy.rules)}")

    print()
    print("--- 4. Rule-evaluate + recommend, via one audited DecisionPipeline run ---")
    context = DecisionContext(
        kpi_results=(oee,), analytics_results=(trend,), scope={"shift": SHIFT_ID}
    )
    strategy = ThresholdDecisionStrategy(policy=policy, severity="high")
    decide_pipeline = DecisionPipeline(
        stages=(RuleEngineStage(policy=policy), ModelStage(strategy))
    )
    trail = DecisionAuditTrail()
    outcome = BatchDecisionRunner(pipeline=decide_pipeline, audit_trail=trail).run(context)
    recommendation = outcome.unwrap()
    assert isinstance(recommendation, Recommendation)
    print(f"triggered: {recommendation.triggered_rules}")
    print(f"summary:   {recommendation.summary}")
    print(f"evidence:  {recommendation.evidence}")

    print()
    print("--- 5. The declarative Thresholds independently confirm the breaches ---")
    for breach in strategy.check_thresholds(context):
        threshold = breach.threshold
        print(
            f"{threshold.field} {threshold.comparator} {threshold.limit}"
            f" (observed {breach.observed_value:.4f})"
        )

    print()
    print("--- 6. Explain + rank, composed as pipeline stages ---")
    explain_context = DecisionContext(
        kpi_results=(oee,),
        analytics_results=(trend,),
        scope={"shift": SHIFT_ID},
        recommendations=(recommendation,),
    )
    explain_pipeline = DecisionPipeline(
        stages=(ExplanationStage(), ModelStage(WeightedScoreRanking()))
    )
    ranked = explain_pipeline.run(explain_context).unwrap()
    assert isinstance(ranked, RankedRecommendation)
    print(f"rank={ranked.rank} score={ranked.score.value:.3f}")
    print(f"components: {dict(ranked.score.components)}")
    explanation = ranked.recommendation.explanation
    assert explanation is not None
    for premise in explanation.premises:
        print(f"premise: {premise}")

    print()
    print("--- 7. The audit trail recorded the operationally-actionable run ---")
    entries = trail.query(scope={"shift": SHIFT_ID})
    recorded = entries[0].recorded_at.astimezone(timezone.utc)
    print(f"{len(entries)} entry, recorded_at={recorded.isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
