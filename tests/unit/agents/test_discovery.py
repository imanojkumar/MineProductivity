"""Tests for mineproductivity.agents.discovery (design spec §23)."""

from __future__ import annotations

import uuid

from mineproductivity.agents._registry import register
from mineproductivity.agents.abstractions import Agent, AgentContext
from mineproductivity.agents.discovery import by_category, by_scope
from mineproductivity.agents.metadata import AgentCategory, AgentMetadata
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.state import TaskState
from mineproductivity.agents.task import Task, TaskStatus
from mineproductivity.core import InMemoryRepository


@register
class _DiscoveryFleetAgent(Agent):
    meta = AgentMetadata(
        code="FLEET.DiscoveryFixture",
        category=AgentCategory.FLEET,
        description="A fleet agent for discovery tests.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        return AgentResult()


def _task(task_id: str, agent_code: str = "FLEET.DiscoveryFixture", **attributes: object) -> Task:
    return Task(
        id=task_id,
        goal_code="GOAL.DiscoveryTest",
        agent_code=agent_code,
        state=TaskState(attributes=attributes or {"provisioned": True}),
    )


class TestByCategory:
    def test_matches_through_the_registry(self) -> None:
        repository: InMemoryRepository[Task, str] = InMemoryRepository()
        repository.add(_task("TASK-1"))
        matched = repository.list(by_category(AgentCategory.FLEET))
        assert [task.id for task in matched] == ["TASK-1"]
        assert list(repository.list(by_category(AgentCategory.ESG))) == []

    def test_unregistered_agent_never_matches_and_never_raises(self) -> None:
        repository: InMemoryRepository[Task, str] = InMemoryRepository()
        repository.add(_task("TASK-1", agent_code=f"FLEET.Never{uuid.uuid4().hex}"))
        assert list(repository.list(by_category(AgentCategory.FLEET))) == []


class TestByScope:
    def test_matches_on_typed_fields_and_state_attributes(self) -> None:
        repository: InMemoryRepository[Task, str] = InMemoryRepository()
        repository.add(_task("TASK-1", pit="north"))
        repository.add(
            _task("TASK-2").with_state(
                TaskState(attributes={"provisioned": True}), status=TaskStatus.COMPLETED
            )
        )
        assert [
            task.id for task in repository.list(by_scope({"goal_code": "GOAL.DiscoveryTest"}))
        ] == ["TASK-1", "TASK-2"]
        assert [
            task.id for task in repository.list(by_scope({"agent_code": "FLEET.DiscoveryFixture"}))
        ] == ["TASK-1", "TASK-2"]
        assert [task.id for task in repository.list(by_scope({"status": "completed"}))] == [
            "TASK-2"
        ]
        assert [task.id for task in repository.list(by_scope({"pit": "north"}))] == ["TASK-1"]
        assert list(repository.list(by_scope({"pit": "north", "status": "completed"}))) == []

    def test_requested_scope_is_copied_not_aliased(self) -> None:
        wanted = {"pit": "north"}
        specification = by_scope(wanted)
        wanted["pit"] = "south"
        repository: InMemoryRepository[Task, str] = InMemoryRepository()
        repository.add(_task("TASK-1", pit="north"))
        assert [task.id for task in repository.list(specification)] == ["TASK-1"]
