"""Tests for mineproductivity.agents.result (design spec §20)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.tool import ToolInvocation
from mineproductivity.core.serialization import to_dict
from mineproductivity.decision import Explanation

_WHEN = datetime(2026, 7, 1, 6, 0, tzinfo=timezone.utc)


class TestDefaults:
    def test_empty_envelope(self) -> None:
        result = AgentResult()
        assert result.task_id == ""
        assert result.warnings == ()
        assert dict(result.output) == {}
        assert result.explanation is None
        assert result.tool_invocations == ()
        assert result.computed_at.tzinfo is not None

    def test_output_is_frozen_and_copied(self) -> None:
        source: dict[str, Any] = {"action": "reassign"}
        result = AgentResult(output=source)
        source["action"] = "mutated"
        assert result.output["action"] == "reassign"


class TestExplanationReuse:
    def test_explanation_is_decision_explanation_directly(self) -> None:
        """Design spec §20: no second justification type exists."""
        explanation = Explanation(premises=("OEE below 0.65",), evidence_refs=("UTIL.OEE",))
        result = AgentResult(explanation=explanation)
        assert result.explanation is explanation
        assert type(result.explanation) is Explanation


class TestToolInvocations:
    def test_carried_verbatim(self) -> None:
        invocation = ToolInvocation(
            tool_code="TOOL.DispatchQuery",
            arguments={"pit": "north"},
            result={"trucks": 12},
            invoked_at=_WHEN,
        )
        result = AgentResult(tool_invocations=(invocation,))
        assert result.tool_invocations == (invocation,)


class TestReplaceAndSerialization:
    def test_replace_stamps_task_id_without_mutation(self) -> None:
        original = AgentResult(output={"action": "reassign"})
        stamped = original.replace(task_id="TASK-1")
        assert original.task_id == ""
        assert stamped.task_id == "TASK-1"
        assert stamped.output["action"] == "reassign"

    def test_serializes_via_core_serialization(self) -> None:
        serialized = to_dict(AgentResult(task_id="TASK-1", output={"a": 1}))
        assert serialized["task_id"] == "TASK-1"
        assert serialized["output"] == {"a": 1}
