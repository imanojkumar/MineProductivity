"""Tests for mineproductivity.agents.goal (design spec §13)."""

from __future__ import annotations

from typing import Any

import pytest

from mineproductivity.agents.goal import Goal
from mineproductivity.core.serialization import to_dict


class TestGoal:
    def test_success_criteria_default_empty(self) -> None:
        assert dict(Goal(description="Recover throughput").success_criteria) == {}

    def test_success_criteria_are_frozen_and_copied(self) -> None:
        source: dict[str, Any] = {"target_tph": 1200.0}
        goal = Goal(description="Recover throughput", success_criteria=source)
        source["target_tph"] = 0.0
        assert goal.success_criteria["target_tph"] == 1200.0
        with pytest.raises(TypeError):
            goal.success_criteria["target_tph"] = 0.0  # type: ignore[index]

    def test_value_equality(self) -> None:
        assert Goal(description="x") == Goal(description="x")
        assert Goal(description="x") != Goal(description="y")

    def test_serializes_via_core_serialization(self) -> None:
        serialized = to_dict(Goal(description="x", success_criteria={"k": 1}))
        assert serialized == {"description": "x", "success_criteria": {"k": 1}}
