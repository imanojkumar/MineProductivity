"""Tests for mineproductivity.decision.strategy."""

from __future__ import annotations

import pytest

from mineproductivity.analytics import AnalyticsResult, RollingSpec, TrendResult
from mineproductivity.core import PredicateSpecification
from mineproductivity.kpis import KPIResult

from mineproductivity.decision._registry import REGISTRY
from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.policy import Policy
from mineproductivity.decision.result import DecisionResult, Recommendation, ThresholdBreach
from mineproductivity.decision.rules import RuleEngine
from mineproductivity.decision.strategy import DecisionStrategy, ThresholdDecisionStrategy
from mineproductivity.decision.thresholds import Threshold

_LOW_OEE_RULE = PredicateSpecification(
    lambda ctx: any(r.value is not None and r.value < 0.65 for r in ctx.kpi_results)
)
_NEVER_RULE = PredicateSpecification(lambda ctx: False)


def _oee_context(value: float = 0.58) -> DecisionContext:
    return DecisionContext(
        kpi_results=(KPIResult(code="UTIL.OEE", value=value, unit=""),),
        analytics_results=(),
        scope={"pit": "north"},
    )


def _policy(**overrides: object) -> Policy:
    fields: dict[str, object] = {
        "code": "AVAIL.LowFleetAvailability",
        "rules": {"low_oee": _LOW_OEE_RULE},
        "thresholds": {"low_oee": Threshold(field="value", comparator="<", limit=0.65)},
        "strategy_code": "STRATEGY.Threshold",
    }
    fields.update(overrides)
    return Policy(**fields)  # type: ignore[arg-type]


class TestDecisionStrategyIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            DecisionStrategy()  # type: ignore[abstract]

    def test_is_a_decision_model(self) -> None:
        assert issubclass(DecisionStrategy, DecisionModel)


class TestThresholdDecisionStrategyMetadata:
    def test_code_is_strategy_threshold(self) -> None:
        assert ThresholdDecisionStrategy.meta.code == "STRATEGY.Threshold"

    def test_is_a_decision_strategy(self) -> None:
        assert issubclass(ThresholdDecisionStrategy, DecisionStrategy)

    def test_description_is_non_empty(self) -> None:
        assert ThresholdDecisionStrategy.meta.description

    def test_repr_includes_policy_and_severity(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy(), severity="high")
        assert "AVAIL.LowFleetAvailability" in repr(strategy)
        assert "high" in repr(strategy)


class TestThresholdDecisionStrategyIsRegistered:
    def test_code_is_in_the_registry(self) -> None:
        assert "STRATEGY.Threshold" in REGISTRY

    def test_registry_get_returns_this_class(self) -> None:
        assert REGISTRY.get("STRATEGY.Threshold") is ThresholdDecisionStrategy


class TestThresholdDecisionStrategyDecide:
    def test_triggered_rule_produces_a_recommendation(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy())
        result = strategy.decide(_oee_context(0.58))
        assert isinstance(result, Recommendation)
        assert result.policy_code == "AVAIL.LowFleetAvailability"
        assert result.triggered_rules == ("low_oee",)
        assert result.model_code == "STRATEGY.Threshold"

    def test_no_triggered_rule_returns_a_bare_decision_result(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy(rules={"never": _NEVER_RULE}))
        result = strategy.decide(_oee_context(0.58))
        assert type(result) is DecisionResult
        assert not isinstance(result, Recommendation)

    def test_default_severity_is_medium(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy())
        result = strategy.decide(_oee_context(0.58))
        assert isinstance(result, Recommendation)
        assert result.severity == "medium"

    def test_explicit_severity_is_used(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy(), severity="critical")
        result = strategy.decide(_oee_context(0.58))
        assert isinstance(result, Recommendation)
        assert result.severity == "critical"

    def test_evidence_includes_kpi_result_codes(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy())
        result = strategy.decide(_oee_context(0.58))
        assert isinstance(result, Recommendation)
        assert "UTIL.OEE" in result.evidence

    def test_evidence_includes_analytics_result_model_codes(self) -> None:
        trend = TrendResult(
            model_code="TREND.Linear",
            slope=-0.5,
            intercept=1.0,
            r_squared=0.9,
            direction="decreasing",
            window=RollingSpec(periods=7),
        )
        context = DecisionContext(
            kpi_results=(KPIResult(code="UTIL.OEE", value=0.58, unit=""),),
            analytics_results=(trend,),
            scope={},
        )
        strategy = ThresholdDecisionStrategy(policy=_policy())
        result = strategy.decide(context)
        assert isinstance(result, Recommendation)
        assert "TREND.Linear" in result.evidence

    def test_multiple_rules_all_named_in_triggered_rules(self) -> None:
        second_rule = PredicateSpecification(lambda ctx: True)
        policy = _policy(rules={"low_oee": _LOW_OEE_RULE, "always": second_rule})
        strategy = ThresholdDecisionStrategy(policy=policy)
        result = strategy.decide(_oee_context(0.58))
        assert isinstance(result, Recommendation)
        assert result.triggered_rules == ("always", "low_oee")

    def test_conflicting_rules_only_the_satisfied_one_is_named(self) -> None:
        policy = _policy(rules={"low_oee": _LOW_OEE_RULE, "never": _NEVER_RULE})
        strategy = ThresholdDecisionStrategy(policy=policy)
        result = strategy.decide(_oee_context(0.58))
        assert isinstance(result, Recommendation)
        assert result.triggered_rules == ("low_oee",)

    def test_precomputed_context_triggered_rules_are_trusted_without_recomputation(self) -> None:
        """When a RuleEngineStage has already run, ThresholdDecisionStrategy
        must use its result rather than re-evaluating -- proven here by
        attaching a triggered_rules value that contradicts what
        RuleEngine.evaluate would itself compute, showing the
        pre-attached value wins."""
        strategy = ThresholdDecisionStrategy(policy=_policy(rules={"never": _NEVER_RULE}))
        context = DecisionContext(
            kpi_results=(KPIResult(code="UTIL.OEE", value=0.58, unit=""),),
            analytics_results=(),
            scope={},
            triggered_rules=("precomputed",),
        )
        result = strategy.decide(context)
        assert isinstance(result, Recommendation)
        assert result.triggered_rules == ("precomputed",)

    def test_explicit_rule_engine_is_used(self) -> None:
        calls: list[str] = []

        class _RecordingRuleEngine(RuleEngine):
            def evaluate(self, rules: object, context: object) -> tuple[str, ...]:  # type: ignore[override]
                calls.append("called")
                return super().evaluate(rules, context)  # type: ignore[arg-type]

        strategy = ThresholdDecisionStrategy(policy=_policy(), rule_engine=_RecordingRuleEngine())
        strategy.decide(_oee_context(0.58))
        assert calls == ["called"]

    def test_precomputed_empty_triggered_rules_is_trusted_without_recomputation(self) -> None:
        """Regression test: DecisionContext.triggered_rules defaults to
        None (not-yet-computed), distinct from () (computed as
        genuinely empty) -- proven here by pre-attaching an empty tuple
        (as RuleEngineStage would when nothing triggers) to a context
        whose Policy WOULD trigger if actually (re-)evaluated, showing
        the pre-attached empty result wins and no recomputation happens."""
        calls: list[str] = []

        class _RecordingRuleEngine(RuleEngine):
            def evaluate(self, rules: object, context: object) -> tuple[str, ...]:  # type: ignore[override]
                calls.append("called")
                return super().evaluate(rules, context)  # type: ignore[arg-type]

        strategy = ThresholdDecisionStrategy(policy=_policy(), rule_engine=_RecordingRuleEngine())
        context = DecisionContext(
            kpi_results=(KPIResult(code="UTIL.OEE", value=0.58, unit=""),),
            analytics_results=(),
            scope={},
            triggered_rules=(),
        )
        result = strategy.decide(context)
        assert calls == []
        assert type(result) is DecisionResult
        assert not isinstance(result, Recommendation)


class TestThresholdDecisionStrategyCheckThresholds:
    def test_breach_detected_for_bare_value_field(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy())
        breaches = strategy.check_thresholds(_oee_context(0.58))
        assert len(breaches) == 1
        assert isinstance(breaches[0], ThresholdBreach)
        assert breaches[0].observed_value == 0.58

    def test_no_breach_when_value_does_not_satisfy_comparator(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy())
        breaches = strategy.check_thresholds(_oee_context(0.90))
        assert breaches == ()

    def test_no_thresholds_declared_yields_no_breaches(self) -> None:
        strategy = ThresholdDecisionStrategy(policy=_policy(thresholds={}))
        assert strategy.check_thresholds(_oee_context(0.58)) == ()

    def test_unresolvable_field_is_skipped_not_raised(self) -> None:
        policy = _policy(
            thresholds={"missing": Threshold(field="nonexistent_field", comparator="<", limit=1.0)}
        )
        strategy = ThresholdDecisionStrategy(policy=policy)
        assert strategy.check_thresholds(_oee_context(0.58)) == ()

    def test_dotted_field_resolves_against_matching_analytics_result(self) -> None:
        trend = TrendResult(
            model_code="TREND.Linear",
            slope=-0.5,
            intercept=1.0,
            r_squared=0.9,
            direction="decreasing",
            window=RollingSpec(periods=7),
        )
        context = DecisionContext(kpi_results=(), analytics_results=(trend,), scope={})
        policy = _policy(
            rules={"declining": PredicateSpecification(lambda ctx: True)},
            thresholds={"declining": Threshold(field="trend.slope", comparator="<", limit=0.0)},
        )
        strategy = ThresholdDecisionStrategy(policy=policy)
        breaches = strategy.check_thresholds(context)
        assert len(breaches) == 1
        assert breaches[0].observed_value == -0.5

    def test_dotted_field_with_no_matching_category_yields_no_breach(self) -> None:
        other = AnalyticsResult(model_code="BENCHMARK.Band")
        context = DecisionContext(kpi_results=(), analytics_results=(other,), scope={})
        policy = _policy(
            thresholds={"declining": Threshold(field="trend.slope", comparator="<", limit=0.0)}
        )
        strategy = ThresholdDecisionStrategy(policy=policy)
        assert strategy.check_thresholds(context) == ()

    @pytest.mark.parametrize(
        ("comparator", "value", "limit", "expected"),
        [
            ("<", 0.5, 1.0, True),
            ("<", 1.5, 1.0, False),
            ("<=", 1.0, 1.0, True),
            (">", 1.5, 1.0, True),
            (">", 0.5, 1.0, False),
            (">=", 1.0, 1.0, True),
            ("==", 1.0, 1.0, True),
            ("==", 1.1, 1.0, False),
            ("!=", 1.1, 1.0, True),
            ("!=", 1.0, 1.0, False),
        ],
    )
    def test_every_comparator_edge_case(
        self, comparator: str, value: float, limit: float, expected: bool
    ) -> None:
        policy = _policy(
            thresholds={"t": Threshold(field="value", comparator=comparator, limit=limit)}  # type: ignore[arg-type]
        )
        strategy = ThresholdDecisionStrategy(policy=policy)
        breaches = strategy.check_thresholds(_oee_context(value))
        assert (len(breaches) == 1) is expected


class TestThresholdDecisionStrategyPipelineIntegration:
    def test_rule_engine_stage_then_model_stage_produces_a_recommendation(self) -> None:
        from mineproductivity.decision.pipeline import DecisionPipeline, ModelStage
        from mineproductivity.decision.rules import RuleEngineStage

        policy = _policy()
        pipeline = DecisionPipeline(
            stages=(
                RuleEngineStage(policy=policy),
                ModelStage(ThresholdDecisionStrategy(policy=policy)),
            )
        )
        outcome = pipeline.run(_oee_context(0.58))
        assert outcome.is_ok
        result = outcome.unwrap()
        assert isinstance(result, Recommendation)
        assert result.triggered_rules == ("low_oee",)

    def test_model_stage_alone_without_rule_engine_stage_still_works(self) -> None:
        from mineproductivity.decision.pipeline import DecisionPipeline, ModelStage

        policy = _policy()
        pipeline = DecisionPipeline(stages=(ModelStage(ThresholdDecisionStrategy(policy=policy)),))
        outcome = pipeline.run(_oee_context(0.58))
        assert outcome.is_ok
        assert isinstance(outcome.unwrap(), Recommendation)
