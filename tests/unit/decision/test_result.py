"""Tests for mineproductivity.decision.result."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.core import BaseValueObject
from mineproductivity.core.serialization import DataclassSerializer, to_dict

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
from mineproductivity.decision.thresholds import Threshold

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _recommendation(**overrides: object) -> Recommendation:
    fields: dict[str, object] = {
        "policy_code": "AVAIL.LowFleetAvailability",
        "triggered_rules": ("low_oee",),
        "summary": "Investigate fleet availability",
        "severity": "high",
        "evidence": ("UTIL.OEE",),
    }
    fields.update(overrides)
    return Recommendation(**fields)  # type: ignore[arg-type]


class TestDecisionResult:
    def test_defaults(self) -> None:
        result = DecisionResult()
        assert result.model_code == ""
        assert result.warnings == ()
        assert result.computed_at.tzinfo is not None

    def test_explicit_fields(self) -> None:
        result = DecisionResult(model_code="STRATEGY.Threshold", warnings=("no policy",))
        assert result.model_code == "STRATEGY.Threshold"
        assert result.warnings == ("no policy",)

    def test_equality_is_value_based(self) -> None:
        first = DecisionResult(model_code="STRATEGY.Threshold", computed_at=DAY_1)
        second = DecisionResult(model_code="STRATEGY.Threshold", computed_at=DAY_1)
        assert first == second


class TestExplanation:
    def test_construction(self) -> None:
        explanation = Explanation(premises=("OEE below 0.65",), evidence_refs=("UTIL.OEE",))
        assert explanation.premises == ("OEE below 0.65",)
        assert explanation.evidence_refs == ("UTIL.OEE",)

    def test_is_not_a_decision_result(self) -> None:
        """Deliberate (design spec §28): a supporting value attached to a
        decision output, not a decision output itself."""
        assert not issubclass(Explanation, DecisionResult)
        assert issubclass(Explanation, BaseValueObject)


class TestDecisionScore:
    def test_construction(self) -> None:
        score = DecisionScore(value=0.8, components={"severity": 0.5, "policy_weight": 0.3})
        assert score.value == 0.8
        assert score.components["severity"] == 0.5

    def test_components_is_frozen_into_a_read_only_mapping(self) -> None:
        score = DecisionScore(value=0.8, components={"severity": 0.5})
        with pytest.raises(TypeError):
            score.components["new"] = 1.0  # type: ignore[index]

    def test_is_not_a_decision_result(self) -> None:
        assert not issubclass(DecisionScore, DecisionResult)
        assert issubclass(DecisionScore, BaseValueObject)


class TestConfidenceScore:
    def test_construction(self) -> None:
        confidence = ConfidenceScore(value=0.9, basis="data_quality")
        assert confidence.value == 0.9
        assert confidence.basis == "data_quality"

    def test_is_not_a_decision_result(self) -> None:
        assert not issubclass(ConfidenceScore, DecisionResult)
        assert issubclass(ConfidenceScore, BaseValueObject)


class TestActionPriority:
    def test_construction(self) -> None:
        priority = ActionPriority(urgency=0.8, impact=0.6, effort=0.2)
        assert priority.urgency == 0.8

    def test_priority_score_is_urgency_times_impact_over_effort(self) -> None:
        priority = ActionPriority(urgency=0.8, impact=0.6, effort=0.2)
        assert priority.priority_score == pytest.approx((0.8 * 0.6) / 0.2)

    def test_priority_score_does_not_divide_by_zero_effort(self) -> None:
        priority = ActionPriority(urgency=1.0, impact=1.0, effort=0.0)
        assert priority.priority_score == pytest.approx(1.0 / 1e-9)

    def test_is_not_a_decision_result(self) -> None:
        assert not issubclass(ActionPriority, DecisionResult)
        assert issubclass(ActionPriority, BaseValueObject)


class TestThresholdBreach:
    def test_construction(self) -> None:
        breach = ThresholdBreach(
            threshold=Threshold(field="value", comparator="<", limit=0.65),
            observed_value=0.58,
            breached_at=DAY_1,
        )
        assert breach.observed_value == 0.58
        assert breach.threshold.field == "value"

    def test_is_not_a_decision_result(self) -> None:
        assert not issubclass(ThresholdBreach, DecisionResult)
        assert issubclass(ThresholdBreach, BaseValueObject)


class TestRecommendation:
    def test_construction(self) -> None:
        rec = _recommendation()
        assert rec.severity == "high"
        assert rec.explanation is None
        assert isinstance(rec, DecisionResult)

    def test_explanation_is_optional(self) -> None:
        explanation = Explanation(premises=("x",), evidence_refs=("UTIL.OEE",))
        rec = _recommendation(explanation=explanation)
        assert rec.explanation is explanation


class TestRankedRecommendation:
    def test_construction(self) -> None:
        rec = _recommendation()
        ranked = RankedRecommendation(
            recommendation=rec, score=DecisionScore(value=0.8, components={}), rank=1
        )
        assert ranked.rank == 1
        assert ranked.recommendation is rec
        assert isinstance(ranked, DecisionResult)


class TestActionPlan:
    def test_construction(self) -> None:
        rec = _recommendation()
        plan = ActionPlan(
            ordered_actions=(rec,),
            priorities={
                "AVAIL.LowFleetAvailability": ActionPriority(urgency=0.8, impact=0.6, effort=0.2)
            },
        )
        assert plan.ordered_actions == (rec,)
        assert isinstance(plan, DecisionResult)

    def test_priorities_is_frozen_into_a_read_only_mapping(self) -> None:
        plan = ActionPlan(
            ordered_actions=(),
            priorities={"x": ActionPriority(urgency=1.0, impact=1.0, effort=1.0)},
        )
        with pytest.raises(TypeError):
            plan.priorities["y"] = ActionPriority(urgency=1.0, impact=1.0, effort=1.0)  # type: ignore[index]


class TestAlert:
    def test_construction(self) -> None:
        alert = Alert(
            message="Fleet availability critical", severity="critical", scope={"pit": "north"}
        )
        assert alert.severity == "critical"
        assert alert.triggered_by is None
        assert isinstance(alert, DecisionResult)

    def test_scope_is_frozen_into_a_read_only_mapping(self) -> None:
        alert = Alert(message="x", severity="low", scope={"pit": "north"})
        with pytest.raises(TypeError):
            alert.scope["shift"] = "A"  # type: ignore[index]

    def test_triggered_by_is_optional(self) -> None:
        breach = ThresholdBreach(
            threshold=Threshold(field="value", comparator="<", limit=0.65),
            observed_value=0.58,
            breached_at=DAY_1,
        )
        alert = Alert(message="x", severity="high", scope={}, triggered_by=breach)
        assert alert.triggered_by is breach


class TestRootCauseResult:
    def test_construction(self) -> None:
        result = RootCauseResult(
            candidate_causes=("conveyor belt wear",),
            confidence=ConfidenceScore(value=0.6, basis="rule_strength"),
        )
        assert result.candidate_causes == ("conveyor belt wear",)
        assert isinstance(result, DecisionResult)


class TestWhatIfResult:
    def test_construction(self) -> None:
        result = WhatIfResult(
            hypothesis={"shift_length_hours": 10},
            predicted_outcome="OEE improves by 2%",
            confidence=ConfidenceScore(value=0.4, basis="rule_strength"),
        )
        assert result.predicted_outcome == "OEE improves by 2%"
        assert isinstance(result, DecisionResult)

    def test_hypothesis_is_frozen_into_a_read_only_mapping(self) -> None:
        result = WhatIfResult(
            hypothesis={"shift_length_hours": 10},
            predicted_outcome="x",
            confidence=ConfidenceScore(value=0.4, basis="rule_strength"),
        )
        with pytest.raises(TypeError):
            result.hypothesis["new_key"] = 1  # type: ignore[index]


class TestSerialization:
    """Design spec §28: 'Every DecisionResult subclass... serializes via
    core.serialization (DataclassSerializer/to_dict) with no bespoke
    per-type serializer.'"""

    _INSTANCES = (
        DecisionResult(model_code="STRATEGY.Threshold"),
        Explanation(premises=("x",), evidence_refs=("UTIL.OEE",)),
        DecisionScore(value=0.8, components={"severity": 0.5}),
        ConfidenceScore(value=0.9, basis="data_quality"),
        ActionPriority(urgency=0.8, impact=0.6, effort=0.2),
        ThresholdBreach(
            threshold=Threshold(field="value", comparator="<", limit=0.65),
            observed_value=0.58,
            breached_at=DAY_1,
        ),
        _recommendation(),
        Alert(message="x", severity="low", scope={"pit": "north"}),
    )

    @pytest.mark.parametrize("instance", _INSTANCES)
    def test_to_dict_works_generically_for_every_result_type(self, instance: object) -> None:
        data = to_dict(instance)
        assert isinstance(data, dict)
        assert data

    @pytest.mark.parametrize("instance", _INSTANCES)
    def test_no_result_type_defines_its_own_to_dict_method(self, instance: object) -> None:
        assert "to_dict" not in type(instance).__dict__

    def test_decision_result_round_trips(self) -> None:
        serializer = DataclassSerializer(DecisionResult)
        original = DecisionResult(model_code="STRATEGY.Threshold", warnings=("no policy",))
        assert serializer.deserialize(serializer.serialize(original)) == original

    def test_decision_score_round_trips(self) -> None:
        serializer = DataclassSerializer(DecisionScore)
        original = DecisionScore(value=0.8, components={"severity": 0.5})
        assert serializer.deserialize(serializer.serialize(original)) == original
