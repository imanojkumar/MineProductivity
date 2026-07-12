"""Tests for mineproductivity.agents.persistence (design spec §25,
§35's repository-substitutability proof: written against the
``core.BaseRepository[Task, str]`` contract alone)."""

from __future__ import annotations

from typing import get_args

import pytest

from mineproductivity.agents.persistence import TaskRepository
from mineproductivity.agents.state import TaskState
from mineproductivity.agents.task import Task
from mineproductivity.core import (
    BaseRepository,
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
)


def _task(task_id: str) -> Task:
    return Task(
        id=task_id,
        goal_code="GOAL.PersistenceTest",
        agent_code="FLEET.PersistenceFixture",
        state=TaskState(attributes={"provisioned": True}),
    )


def _make_repository() -> BaseRepository[Task, str]:
    reference: InMemoryRepository[Task, str] = InMemoryRepository()
    return reference


class TestAlias:
    def test_is_a_literal_type_alias_over_core_base_repository(self) -> None:
        aliased = TaskRepository.__value__
        assert aliased.__origin__ is BaseRepository
        assert get_args(aliased) == (Task, str)
        assert type(_make_repository()) is InMemoryRepository


class TestRepositoryContract:
    def test_full_contract_round_trip(self) -> None:
        repository = _make_repository()
        task = _task("TASK-1")
        repository.add(task)
        assert repository.get("TASK-1") is task
        assert repository.find("TASK-1").unwrap() is task
        assert repository.find("NO-SUCH").is_nothing
        assert "TASK-1" in repository
        with pytest.raises(DuplicateError):
            repository.add(_task("TASK-1"))
        repository.add(_task("TASK-2"))
        assert sorted(t.id for t in repository.list()) == ["TASK-1", "TASK-2"]
        repository.remove("TASK-1")
        with pytest.raises(NotFoundError):
            repository.get("TASK-1")
        with pytest.raises(NotFoundError):
            repository.remove("NO-SUCH")
