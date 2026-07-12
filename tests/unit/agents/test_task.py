"""Tests for mineproductivity.agents.task (design spec §11)."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.agents.exceptions import AgentValidationError
from mineproductivity.agents.state import TaskState
from mineproductivity.agents.task import Task, TaskStatus
from mineproductivity.core import BaseEntity
from mineproductivity.core.serialization import to_dict


def _task(task_id: str = "TASK-1", **overrides: object) -> Task:
    kwargs: dict[str, object] = {
        "id": task_id,
        "goal_code": "GOAL.NightShiftRecovery",
        "agent_code": "FLEET.ReassignmentAdvisor",
        "state": TaskState(attributes={"provisioned": True}),
    }
    kwargs.update(overrides)
    return Task(**kwargs)  # type: ignore[arg-type]


class TestTaskStatus:
    def test_exactly_the_six_members(self) -> None:
        assert {member.value for member in TaskStatus} == {
            "scheduled",
            "running",
            "awaiting_approval",
            "paused",
            "completed",
            "failed",
        }


class TestIdentity:
    def test_same_id_different_state_compare_equal(self) -> None:
        """Design spec §35: BaseEntity-inherited identity equality."""
        one = _task()
        other = _task().with_state(
            TaskState(attributes={"progress": 1.0}), status=TaskStatus.COMPLETED
        )
        assert one == other
        assert hash(one) == hash(other)

    def test_different_ids_never_equal(self) -> None:
        assert _task("TASK-1") != _task("TASK-2")

    def test_eq_and_hash_are_inherited_unchanged_from_base_entity(self) -> None:
        assert "__eq__" not in Task.__dict__
        assert "__hash__" not in Task.__dict__
        assert Task.__eq__ is BaseEntity.__eq__
        assert Task.__hash__ is BaseEntity.__hash__


class TestValidation:
    def test_empty_goal_code_raises(self) -> None:
        with pytest.raises(AgentValidationError, match="goal_code"):
            _task(goal_code="  ")

    def test_empty_agent_code_raises(self) -> None:
        with pytest.raises(AgentValidationError, match="agent_code"):
            _task(agent_code="")


class TestWithState:
    def test_returns_a_new_instance_and_never_mutates_self(self) -> None:
        original = _task()
        updated = original.with_state(
            TaskState(attributes={"progress": 0.5}), status=TaskStatus.RUNNING
        )
        assert updated is not original
        assert original.status is TaskStatus.SCHEDULED
        assert original.state.attributes == {"provisioned": True}
        assert updated.status is TaskStatus.RUNNING
        assert updated.state.attributes["progress"] == 0.5

    def test_status_omitted_keeps_the_current_status(self) -> None:
        running = _task().with_state(_task().state, status=TaskStatus.RUNNING)
        assert running.with_state(TaskState(attributes={"x": 1})).status is TaskStatus.RUNNING

    def test_task_is_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            _task().status = TaskStatus.RUNNING  # type: ignore[misc]

    def test_no_method_on_task_mutates_self(self) -> None:
        """Design spec §35 immutability proof: with_state is not
        overridden into a mutation anywhere."""
        assert Task.__dataclass_params__.frozen  # type: ignore[attr-defined]


class TestSerialization:
    def test_serializes_via_core_serialization(self) -> None:
        serialized = to_dict(_task())
        assert serialized["id"] == "TASK-1"
        assert serialized["goal_code"] == "GOAL.NightShiftRecovery"
        assert serialized["state"] == {"attributes": {"provisioned": True}}
