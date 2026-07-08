"""Tests for mineproductivity.decision.planning."""

from __future__ import annotations

from mineproductivity.decision.planning import ActionPlanner
from mineproductivity.decision.result import (
    ActionPriority,
    DecisionScore,
    RankedRecommendation,
    Recommendation,
)


def _item(
    *, policy_code: str, priority_score_inputs: tuple[float, float, float] = (0.5, 0.5, 1.0)
) -> tuple[RankedRecommendation, ActionPriority]:
    urgency, impact, effort = priority_score_inputs
    rec = Recommendation(
        policy_code=policy_code,
        triggered_rules=(),
        summary=f"Do {policy_code}",
        severity="medium",
        evidence=(),
    )
    ranked = RankedRecommendation(
        recommendation=rec, score=DecisionScore(value=impact, components={}), rank=1
    )
    priority = ActionPriority(urgency=urgency, impact=impact, effort=effort)
    return ranked, priority


class TestActionPlannerPlanWithoutDependencies:
    def test_empty_sequence_yields_empty_plan(self) -> None:
        result = ActionPlanner().plan([])
        assert result.is_ok
        assert result.unwrap().ordered_actions == ()

    def test_degrades_to_priority_score_descending_order(self) -> None:
        low = _item(policy_code="LOW", priority_score_inputs=(0.2, 0.2, 1.0))
        high = _item(policy_code="HIGH", priority_score_inputs=(0.9, 0.9, 1.0))
        result = ActionPlanner().plan([low, high])
        assert result.is_ok
        codes = [action.policy_code for action in result.unwrap().ordered_actions]
        assert codes == ["HIGH", "LOW"]

    def test_priorities_mapping_is_keyed_by_policy_code(self) -> None:
        item = _item(policy_code="A")
        result = ActionPlanner().plan([item])
        priorities = result.unwrap().priorities
        assert "A" in priorities
        assert priorities["A"] == item[1]


class TestActionPlannerPlanWithDependencies:
    def test_dependency_forces_prerequisite_first_even_with_lower_priority(self) -> None:
        a = _item(policy_code="A", priority_score_inputs=(0.9, 0.9, 1.0))
        b = _item(policy_code="B", priority_score_inputs=(0.1, 0.1, 1.0))
        result = ActionPlanner().plan([a, b], dependencies={"A": ("B",)})
        assert result.is_ok
        codes = [action.policy_code for action in result.unwrap().ordered_actions]
        assert codes == ["B", "A"]

    def test_dependency_referencing_a_key_not_in_prioritized_is_ignored(self) -> None:
        a = _item(policy_code="A")
        result = ActionPlanner().plan([a], dependencies={"A": ("MISSING",)})
        assert result.is_ok
        assert [action.policy_code for action in result.unwrap().ordered_actions] == ["A"]

    def test_dependency_key_not_in_prioritized_is_ignored(self) -> None:
        a = _item(policy_code="A")
        result = ActionPlanner().plan([a], dependencies={"MISSING": ("A",)})
        assert result.is_ok
        assert [action.policy_code for action in result.unwrap().ordered_actions] == ["A"]

    def test_diamond_dependency_resolves_correctly(self) -> None:
        # D depends on B and C; B and C both depend on A.
        a = _item(policy_code="A", priority_score_inputs=(0.5, 0.5, 1.0))
        b = _item(policy_code="B", priority_score_inputs=(0.9, 0.9, 1.0))
        c = _item(policy_code="C", priority_score_inputs=(0.1, 0.1, 1.0))
        d = _item(policy_code="D", priority_score_inputs=(0.5, 0.5, 1.0))
        result = ActionPlanner().plan(
            [a, b, c, d], dependencies={"B": ("A",), "C": ("A",), "D": ("B", "C")}
        )
        assert result.is_ok
        codes = [action.policy_code for action in result.unwrap().ordered_actions]
        assert codes.index("A") < codes.index("B") < codes.index("D")
        assert codes.index("A") < codes.index("C") < codes.index("D")

    def test_two_element_cycle_is_detected_and_rejected(self) -> None:
        a = _item(policy_code="A")
        b = _item(policy_code="B")
        result = ActionPlanner().plan([a, b], dependencies={"A": ("B",), "B": ("A",)})
        assert result.is_err

    def test_self_dependency_is_detected_and_rejected(self) -> None:
        a = _item(policy_code="A")
        result = ActionPlanner().plan([a], dependencies={"A": ("A",)})
        assert result.is_err

    def test_repr_is_stable(self) -> None:
        assert repr(ActionPlanner()) == "ActionPlanner()"


class TestActionPlannerRejectsDuplicatePolicyCodes:
    def test_duplicate_policy_code_is_rejected_rather_than_silently_dropped(self) -> None:
        first = _item(policy_code="A", priority_score_inputs=(0.9, 0.9, 1.0))
        second = _item(policy_code="A", priority_score_inputs=(0.1, 0.1, 1.0))
        result = ActionPlanner().plan([first, second])
        assert result.is_err

    def test_unique_policy_codes_are_unaffected(self) -> None:
        first = _item(policy_code="A")
        second = _item(policy_code="B")
        result = ActionPlanner().plan([first, second])
        assert result.is_ok
