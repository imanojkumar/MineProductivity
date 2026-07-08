"""Tests for mineproductivity.decision.ranking."""

from __future__ import annotations

import pytest

from mineproductivity.decision._registry import REGISTRY
from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.pipeline import DecisionPipeline, ModelStage
from mineproductivity.decision.ranking import RankingStrategy, WeightedScoreRanking
from mineproductivity.decision.result import DecisionResult, RankedRecommendation, Recommendation
from mineproductivity.decision.scoring import DecisionScorer


def _recommendation(**overrides: object) -> Recommendation:
    fields: dict[str, object] = {
        "policy_code": "AVAIL.LowFleetAvailability",
        "triggered_rules": ("low_oee",),
        "summary": "x",
        "severity": "medium",
        "evidence": (),
    }
    fields.update(overrides)
    return Recommendation(**fields)  # type: ignore[arg-type]


class TestRankingStrategyIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            RankingStrategy()  # type: ignore[abstract]

    def test_is_a_decision_model(self) -> None:
        assert issubclass(RankingStrategy, DecisionModel)


class TestWeightedScoreRankingMetadata:
    def test_code_is_ranking_weighted_score(self) -> None:
        assert WeightedScoreRanking.meta.code == "RANKING.WeightedScore"

    def test_is_a_ranking_strategy(self) -> None:
        assert issubclass(WeightedScoreRanking, RankingStrategy)

    def test_repr_includes_scorer(self) -> None:
        assert "DecisionScorer" in repr(WeightedScoreRanking())


class TestWeightedScoreRankingIsRegistered:
    def test_code_is_in_the_registry(self) -> None:
        assert "RANKING.WeightedScore" in REGISTRY

    def test_registry_get_returns_this_class(self) -> None:
        assert REGISTRY.get("RANKING.WeightedScore") is WeightedScoreRanking


class TestWeightedScoreRankingRank:
    def test_empty_sequence_yields_empty_result(self) -> None:
        assert WeightedScoreRanking().rank([]) == ()

    def test_single_recommendation_is_rank_one(self) -> None:
        ranked = WeightedScoreRanking().rank([_recommendation()])
        assert len(ranked) == 1
        assert ranked[0].rank == 1
        assert isinstance(ranked[0], RankedRecommendation)

    def test_higher_severity_ranks_first(self) -> None:
        low = _recommendation(policy_code="LOW", severity="low")
        critical = _recommendation(policy_code="CRITICAL", severity="critical")
        ranked = WeightedScoreRanking().rank([low, critical])
        assert ranked[0].recommendation.policy_code == "CRITICAL"
        assert ranked[1].recommendation.policy_code == "LOW"

    def test_ranks_are_sequential_starting_at_one(self) -> None:
        recs = [_recommendation(policy_code=f"P{i}", severity="medium") for i in range(4)]
        ranked = WeightedScoreRanking().rank(recs)
        assert [item.rank for item in ranked] == [1, 2, 3, 4]

    def test_ties_preserve_input_relative_order(self) -> None:
        first = _recommendation(policy_code="FIRST", severity="medium", triggered_rules=("a",))
        second = _recommendation(policy_code="SECOND", severity="medium", triggered_rules=("a",))
        ranked = WeightedScoreRanking().rank([first, second])
        assert [item.recommendation.policy_code for item in ranked] == ["FIRST", "SECOND"]

    def test_model_code_is_attached_to_each_ranked_recommendation(self) -> None:
        ranked = WeightedScoreRanking().rank([_recommendation()])
        assert ranked[0].model_code == "RANKING.WeightedScore"

    def test_explicit_scorer_is_used(self) -> None:
        calls: list[str] = []

        class _RecordingScorer(DecisionScorer):
            def score(self, recommendation: object, *, confidence: object = None):  # type: ignore[no-untyped-def, override]
                calls.append("called")
                return super().score(recommendation, confidence=confidence)  # type: ignore[arg-type]

        WeightedScoreRanking(scorer=_RecordingScorer()).rank([_recommendation()])
        assert calls == ["called"]


class TestWeightedScoreRankingDecide:
    def test_no_recommendations_in_context_returns_warning_result(self) -> None:
        from mineproductivity.kpis import KPIResult

        context = DecisionContext(
            kpi_results=(KPIResult(code="UTIL.OEE", value=1.0, unit=""),),
            analytics_results=(),
            scope={},
        )
        result = WeightedScoreRanking().decide(context)
        assert type(result) is DecisionResult
        assert "no recommendations to rank" in result.warnings[0]

    def test_decide_requires_evidence_per_base_contract(self) -> None:
        """DecisionModel.decide()'s own orchestration (Phase 07.1) still
        applies: no KPIResult/AnalyticsResult evidence at all short-
        circuits before _decide ever runs, regardless of recommendations."""
        context = DecisionContext(
            kpi_results=(), analytics_results=(), scope={}, recommendations=(_recommendation(),)
        )
        result = WeightedScoreRanking().decide(context)
        assert "no evidence in context" in result.warnings[0]

    def test_decide_returns_the_top_ranked_recommendation(self) -> None:
        from mineproductivity.kpis import KPIResult

        low = _recommendation(policy_code="LOW", severity="low")
        critical = _recommendation(policy_code="CRITICAL", severity="critical")
        context = DecisionContext(
            kpi_results=(KPIResult(code="UTIL.OEE", value=1.0, unit=""),),
            analytics_results=(),
            scope={},
            recommendations=(low, critical),
        )
        result = WeightedScoreRanking().decide(context)
        assert isinstance(result, RankedRecommendation)
        assert result.recommendation.policy_code == "CRITICAL"
        assert result.rank == 1


class TestWeightedScoreRankingPipelineIntegration:
    def test_model_stage_ranks_recommendations_attached_to_context(self) -> None:
        from mineproductivity.kpis import KPIResult

        low = _recommendation(policy_code="LOW", severity="low")
        critical = _recommendation(policy_code="CRITICAL", severity="critical")
        context = DecisionContext(
            kpi_results=(KPIResult(code="UTIL.OEE", value=1.0, unit=""),),
            analytics_results=(),
            scope={},
            recommendations=(low, critical),
        )
        pipeline = DecisionPipeline(stages=(ModelStage(WeightedScoreRanking()),))
        outcome = pipeline.run(context)
        assert outcome.is_ok
        result = outcome.unwrap()
        assert isinstance(result, RankedRecommendation)
        assert result.recommendation.policy_code == "CRITICAL"
