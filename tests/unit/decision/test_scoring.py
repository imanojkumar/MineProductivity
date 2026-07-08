"""Tests for mineproductivity.decision.scoring."""

from __future__ import annotations

import pytest

from mineproductivity.analytics import DataQualityScore, RollingSpec, TrendResult
from mineproductivity.kpis import KPIResult

from mineproductivity.decision.abstractions import DecisionContext
from mineproductivity.decision.result import ConfidenceScore, Recommendation
from mineproductivity.decision.scoring import ConfidenceScorer, DecisionScorer


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


class TestDecisionScorer:
    def test_returns_a_decision_score(self) -> None:
        score = DecisionScorer().score(_recommendation())
        assert 0.0 <= score.value <= 1.0

    @pytest.mark.parametrize(
        ("severity", "expected_weight"),
        [("low", 0.25), ("medium", 0.5), ("high", 0.75), ("critical", 1.0)],
    )
    def test_severity_component_matches_expected_weight(
        self, severity: str, expected_weight: float
    ) -> None:
        score = DecisionScorer().score(_recommendation(severity=severity))
        assert score.components["severity"] == expected_weight

    def test_more_triggered_rules_increases_policy_weight(self) -> None:
        one_rule = DecisionScorer().score(_recommendation(triggered_rules=("a",)))
        three_rules = DecisionScorer().score(_recommendation(triggered_rules=("a", "b", "c")))
        assert three_rules.components["policy_weight"] > one_rule.components["policy_weight"]

    def test_policy_weight_caps_at_one(self) -> None:
        many_rules = tuple(f"rule_{i}" for i in range(20))
        score = DecisionScorer().score(_recommendation(triggered_rules=many_rules))
        assert score.components["policy_weight"] == 1.0

    def test_empty_triggered_rules_has_zero_policy_weight(self) -> None:
        score = DecisionScorer().score(_recommendation(triggered_rules=()))
        assert score.components["policy_weight"] == 0.0

    def test_no_confidence_defaults_to_full_confidence_weight(self) -> None:
        score = DecisionScorer().score(_recommendation())
        assert score.components["confidence"] == 1.0

    def test_explicit_confidence_is_used(self) -> None:
        score = DecisionScorer().score(
            _recommendation(), confidence=ConfidenceScore(value=0.4, basis="rule_strength")
        )
        assert score.components["confidence"] == 0.4

    def test_lower_confidence_yields_lower_score(self) -> None:
        high_confidence = DecisionScorer().score(
            _recommendation(), confidence=ConfidenceScore(value=1.0, basis="rule_strength")
        )
        low_confidence = DecisionScorer().score(
            _recommendation(), confidence=ConfidenceScore(value=0.0, basis="rule_strength")
        )
        assert high_confidence.value > low_confidence.value

    def test_critical_severity_scores_higher_than_low(self) -> None:
        critical = DecisionScorer().score(_recommendation(severity="critical"))
        low = DecisionScorer().score(_recommendation(severity="low"))
        assert critical.value > low.value

    def test_score_boundaries_are_deterministic(self) -> None:
        """Same input always yields the exact same DecisionScore --
        DecisionScorer is a pure function with no hidden state."""
        first = DecisionScorer().score(_recommendation())
        second = DecisionScorer().score(_recommendation())
        assert first == second


class TestConfidenceScorer:
    def test_falls_back_to_rule_strength_when_no_data_quality_present(self) -> None:
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        confidence = ConfidenceScorer().score(_recommendation(), context=context)
        assert confidence.basis == "rule_strength"

    def test_rule_strength_basis_value_matches_rule_count(self) -> None:
        context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
        confidence = ConfidenceScorer().score(
            _recommendation(triggered_rules=("a", "b")), context=context
        )
        assert confidence.value == pytest.approx(2 / 5)

    def test_uses_combined_basis_when_data_quality_score_present(self) -> None:
        dq = DataQualityScore(completeness=1.0, validity=1.0, overall_score=0.9, reasons=())
        context = DecisionContext(kpi_results=(), analytics_results=(dq,), scope={})
        confidence = ConfidenceScorer().score(_recommendation(), context=context)
        assert confidence.basis == "combined"

    def test_combined_value_averages_data_quality_and_rule_strength(self) -> None:
        dq = DataQualityScore(completeness=1.0, validity=1.0, overall_score=1.0, reasons=())
        context = DecisionContext(kpi_results=(), analytics_results=(dq,), scope={})
        confidence = ConfidenceScorer().score(
            _recommendation(triggered_rules=("a",)), context=context
        )
        # rule_strength = 1/5 = 0.2, data_quality = 1.0 -> combined = 0.6
        assert confidence.value == pytest.approx(0.6)

    def test_ignores_non_data_quality_analytics_results(self) -> None:
        trend = TrendResult(
            model_code="TREND.Linear",
            slope=0.1,
            intercept=0.0,
            r_squared=0.5,
            direction="increasing",
            window=RollingSpec(periods=3),
        )
        context = DecisionContext(kpi_results=(), analytics_results=(trend,), scope={})
        confidence = ConfidenceScorer().score(_recommendation(), context=context)
        assert confidence.basis == "rule_strength"

    def test_no_kpi_results_needed(self) -> None:
        context = DecisionContext(
            kpi_results=(KPIResult(code="UTIL.OEE", value=0.5, unit=""),),
            analytics_results=(),
            scope={},
        )
        confidence = ConfidenceScorer().score(_recommendation(), context=context)
        assert 0.0 <= confidence.value <= 1.0
