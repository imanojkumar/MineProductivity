"""Tests for mineproductivity.decision.prioritization."""

from __future__ import annotations

import pytest

from mineproductivity.decision.prioritization import ActionPrioritizer
from mineproductivity.decision.result import (
    ActionPriority,
    DecisionScore,
    RankedRecommendation,
    Recommendation,
)


def _ranked(
    *,
    policy_code: str = "AVAIL.LowFleetAvailability",
    severity: str = "medium",
    score: float = 0.5,
    rank: int = 1,
) -> RankedRecommendation:
    rec = Recommendation(
        policy_code=policy_code,
        triggered_rules=("low_oee",),
        summary="x",
        severity=severity,  # type: ignore[arg-type]
        evidence=(),
    )
    return RankedRecommendation(
        recommendation=rec, score=DecisionScore(value=score, components={}), rank=rank
    )


class TestActionPrioritizerPrioritize:
    def test_empty_sequence_yields_empty_result(self) -> None:
        assert ActionPrioritizer().prioritize([]) == ()

    def test_single_item_produces_one_tuple(self) -> None:
        prioritized = ActionPrioritizer().prioritize([_ranked()])
        assert len(prioritized) == 1
        item, priority = prioritized[0]
        assert isinstance(item, RankedRecommendation)
        assert isinstance(priority, ActionPriority)

    def test_impact_equals_the_decision_score_value(self) -> None:
        _, priority = ActionPrioritizer().prioritize([_ranked(score=0.73)])[0]
        assert priority.impact == 0.73

    @pytest.mark.parametrize(
        ("severity", "expected_urgency"),
        [("low", 0.25), ("medium", 0.5), ("high", 0.75), ("critical", 1.0)],
    )
    def test_urgency_matches_severity_weight(self, severity: str, expected_urgency: float) -> None:
        _, priority = ActionPrioritizer().prioritize([_ranked(severity=severity)])[0]
        assert priority.urgency == expected_urgency

    def test_default_effort_is_used_when_no_estimate_supplied(self) -> None:
        _, priority = ActionPrioritizer(default_effort=2.0).prioritize([_ranked()])[0]
        assert priority.effort == 2.0

    def test_effort_estimate_is_looked_up_by_policy_code(self) -> None:
        prioritizer = ActionPrioritizer(effort_estimates={"AVAIL.LowFleetAvailability": 5.0})
        _, priority = prioritizer.prioritize([_ranked(policy_code="AVAIL.LowFleetAvailability")])[0]
        assert priority.effort == 5.0

    def test_effort_estimate_miss_falls_back_to_default(self) -> None:
        prioritizer = ActionPrioritizer(effort_estimates={"OTHER.Policy": 5.0}, default_effort=1.5)
        _, priority = prioritizer.prioritize([_ranked(policy_code="AVAIL.LowFleetAvailability")])[0]
        assert priority.effort == 1.5

    def test_preserves_input_order(self) -> None:
        first = _ranked(policy_code="FIRST", rank=1)
        second = _ranked(policy_code="SECOND", rank=2)
        prioritized = ActionPrioritizer().prioritize([first, second])
        assert [item.recommendation.policy_code for item, _ in prioritized] == ["FIRST", "SECOND"]

    def test_priority_score_property_is_consistent(self) -> None:
        _, priority = ActionPrioritizer().prioritize([_ranked(severity="critical", score=0.8)])[0]
        assert priority.priority_score == pytest.approx((1.0 * 0.8) / 1.0)

    def test_repr_includes_effort_estimates(self) -> None:
        prioritizer = ActionPrioritizer(effort_estimates={"X": 3.0})
        assert "X" in repr(prioritizer)
