"""Tests for mineproductivity.decision.explanation."""

from __future__ import annotations

from mineproductivity.analytics import RollingSpec, TrendResult
from mineproductivity.kpis import KPIResult

from mineproductivity.decision.abstractions import DecisionContext
from mineproductivity.decision.explanation import ExplanationBuilder, ExplanationStage
from mineproductivity.decision.pipeline import DecisionPipeline, ModelStage
from mineproductivity.decision.ranking import WeightedScoreRanking
from mineproductivity.decision.result import RankedRecommendation, Recommendation


def _recommendation(**overrides: object) -> Recommendation:
    fields: dict[str, object] = {
        "policy_code": "AVAIL.LowFleetAvailability",
        "triggered_rules": ("low_oee",),
        "summary": "x",
        "severity": "high",
        "evidence": ("UTIL.OEE",),
    }
    fields.update(overrides)
    return Recommendation(**fields)  # type: ignore[arg-type]


def _context_with(recommendation: Recommendation, value: float = 0.58) -> DecisionContext:
    return DecisionContext(
        kpi_results=(KPIResult(code="UTIL.OEE", value=value, unit=""),),
        analytics_results=(),
        scope={},
        recommendations=(recommendation,),
    )


class TestExplanationBuilder:
    def test_evidence_refs_match_recommendation_evidence(self) -> None:
        rec = _recommendation(evidence=("UTIL.OEE", "TREND.Linear"))
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        explanation = ExplanationBuilder().build(rec, context=context)
        assert explanation.evidence_refs == ("UTIL.OEE", "TREND.Linear")

    def test_premises_include_one_per_triggered_rule(self) -> None:
        rec = _recommendation(triggered_rules=("low_oee", "declining_trend"))
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        explanation = ExplanationBuilder().build(rec, context=context)
        assert any("low_oee" in premise for premise in explanation.premises)
        assert any("declining_trend" in premise for premise in explanation.premises)

    def test_premises_include_matching_kpi_result_values(self) -> None:
        rec = _recommendation(evidence=("UTIL.OEE",))
        context = _context_with(rec, value=0.58)
        explanation = ExplanationBuilder().build(rec, context=context)
        assert any("UTIL.OEE" in premise and "0.58" in premise for premise in explanation.premises)

    def test_kpi_result_not_in_evidence_is_not_cited(self) -> None:
        rec = _recommendation(evidence=())
        context = _context_with(rec, value=0.58)
        explanation = ExplanationBuilder().build(rec, context=context)
        assert not any("0.58" in premise for premise in explanation.premises)

    def test_premises_include_matching_analytics_result(self) -> None:
        rec = _recommendation(evidence=("TREND.Linear",))
        trend = TrendResult(
            model_code="TREND.Linear",
            slope=-0.5,
            intercept=1.0,
            r_squared=0.9,
            direction="decreasing",
            window=RollingSpec(periods=3),
        )
        context = DecisionContext(kpi_results=(), analytics_results=(trend,), scope={})
        explanation = ExplanationBuilder().build(rec, context=context)
        assert any("TREND.Linear" in premise for premise in explanation.premises)

    def test_no_triggered_rules_and_no_matching_evidence_yields_empty_premises(self) -> None:
        rec = _recommendation(triggered_rules=(), evidence=())
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        explanation = ExplanationBuilder().build(rec, context=context)
        assert explanation.premises == ()


class TestExplanationStage:
    def test_attaches_explanation_to_each_recommendation(self) -> None:
        rec = _recommendation()
        context = _context_with(rec)
        result = ExplanationStage().process(context)
        assert result.recommendations is not None
        assert result.recommendations[0].explanation is not None

    def test_returns_the_same_context_object(self) -> None:
        rec = _recommendation()
        context = _context_with(rec)
        result = ExplanationStage().process(context)
        assert result is context

    def test_no_recommendations_is_a_no_op(self) -> None:
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        result = ExplanationStage().process(context)
        assert result.recommendations is None

    def test_multiple_recommendations_are_all_explained(self) -> None:
        first = _recommendation(policy_code="A")
        second = _recommendation(policy_code="B")
        context = DecisionContext(
            kpi_results=(), analytics_results=(), scope={}, recommendations=(first, second)
        )
        result = ExplanationStage().process(context)
        assert result.recommendations is not None
        assert all(rec.explanation is not None for rec in result.recommendations)

    def test_explained_recommendations_preserve_original_fields(self) -> None:
        rec = _recommendation()
        context = _context_with(rec)
        result = ExplanationStage().process(context)
        assert result.recommendations is not None
        explained = result.recommendations[0]
        assert explained.policy_code == rec.policy_code
        assert explained.triggered_rules == rec.triggered_rules

    def test_repr_includes_builder(self) -> None:
        assert "ExplanationBuilder" in repr(ExplanationStage())

    def test_explicit_builder_is_used(self) -> None:
        calls: list[str] = []

        class _RecordingBuilder(ExplanationBuilder):
            def build(self, recommendation: Recommendation, *, context: DecisionContext):  # type: ignore[no-untyped-def, override]
                calls.append("called")
                return super().build(recommendation, context=context)

        rec = _recommendation()
        context = _context_with(rec)
        ExplanationStage(builder=_RecordingBuilder()).process(context)
        assert calls == ["called"]


class TestExplanationStagePipelineIntegration:
    def test_explanation_stage_then_ranking_model_stage(self) -> None:
        """ExplanationStage (non-terminal) runs first, attaching
        Explanations; WeightedScoreRanking (via ModelStage) is the
        pipeline's genuine terminal stage -- the correct, working
        composition disclosed in explanation.py's own module docstring."""
        low = _recommendation(policy_code="LOW", severity="low")
        critical = _recommendation(policy_code="CRITICAL", severity="critical")
        context = DecisionContext(
            kpi_results=(KPIResult(code="UTIL.OEE", value=0.58, unit=""),),
            analytics_results=(),
            scope={},
            recommendations=(low, critical),
        )
        pipeline = DecisionPipeline(stages=(ExplanationStage(), ModelStage(WeightedScoreRanking())))
        outcome = pipeline.run(context)
        assert outcome.is_ok
        result = outcome.unwrap()
        assert isinstance(result, RankedRecommendation)
        assert result.recommendation.policy_code == "CRITICAL"
        assert result.recommendation.explanation is not None
