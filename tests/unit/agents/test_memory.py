"""Tests for mineproductivity.agents.memory (design spec §14):
interface-only ABC contract -- no reasoning-correctness test exists,
by design (§35)."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

import mineproductivity.agents.memory as memory_module
from mineproductivity.agents.abstractions import AgentContext
from mineproductivity.agents.memory import AgentMemory


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            AgentMemory()  # type: ignore[abstract]

    def test_remember_and_recall_are_the_two_abstract_methods(self) -> None:
        assert AgentMemory.__abstractmethods__ == frozenset({"remember", "recall"})

    def test_module_defines_no_concrete_subclass(self) -> None:
        """Design spec §35's interface-purity proof, module-local."""
        for _, obj in inspect.getmembers(memory_module, inspect.isclass):
            if issubclass(obj, AgentMemory):
                assert inspect.isabstract(obj)


class _TaskScopedMemory(AgentMemory):
    """Test-local fixture backend -- per-task_id scoping per design
    spec §14, §33."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], Any] = {}

    def remember(self, task_id: str, key: str, value: Any, *, context: AgentContext) -> None:
        self._store[(task_id, key)] = value

    def recall(self, task_id: str, key: str, *, context: AgentContext) -> Any | None:
        return self._store.get((task_id, key))


class TestRecallMissConvention:
    def test_a_miss_returns_none_never_raises(self) -> None:
        """Design spec §14: a recall() miss is never an error."""
        memory = _TaskScopedMemory()
        assert memory.recall("TASK-1", "unseen", context=AgentContext()) is None

    def test_memory_is_scoped_per_task_id(self) -> None:
        """Design spec §33: one task's recalled context never leaks
        into an unrelated task's reasoning."""
        memory = _TaskScopedMemory()
        memory.remember("TASK-1", "plan", "B", context=AgentContext())
        assert memory.recall("TASK-1", "plan", context=AgentContext()) == "B"
        assert memory.recall("TASK-2", "plan", context=AgentContext()) is None
