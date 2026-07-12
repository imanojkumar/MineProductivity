"""Tests for mineproductivity.agents.state (design spec §11)."""

from __future__ import annotations

import pytest

from mineproductivity.agents.exceptions import AgentValidationError
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.state import TaskState
from mineproductivity.core.serialization import to_dict


class TestTaskState:
    def test_empty_attributes_raises(self) -> None:
        with pytest.raises(AgentValidationError, match="attributes"):
            TaskState(attributes={})

    def test_attributes_are_frozen_against_the_source_mapping(self) -> None:
        source = {"progress": 0.5}
        state = TaskState(attributes=source)
        source["progress"] = 1.0
        assert state.attributes["progress"] == 0.5
        with pytest.raises(TypeError):
            state.attributes["progress"] = 1.0  # type: ignore[index]

    def test_value_equality(self) -> None:
        assert TaskState(attributes={"a": 1}) == TaskState(attributes={"a": 1})
        assert TaskState(attributes={"a": 1}) != TaskState(attributes={"a": 2})

    def test_not_an_agent_result_subclass(self) -> None:
        """Design spec §20: the task's condition itself, never the
        outcome of an orchestration call about it."""
        assert not issubclass(TaskState, AgentResult)

    def test_serializes_via_core_serialization(self) -> None:
        assert to_dict(TaskState(attributes={"progress": 0.5})) == {"attributes": {"progress": 0.5}}
