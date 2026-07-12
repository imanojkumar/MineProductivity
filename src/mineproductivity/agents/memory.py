"""``AgentMemory``: interface-only extension point (design spec §14)
-- no concrete implementation ships in this package.

Deliberately NOT a reuse of ``kpis.ResultCache``/
``digital_twin.TwinStateCache``/``simulation.SimulationStateCache``: a
cache is a performance optimization invisible to its caller, safe to
evict at any time with no behavioral consequence beyond a slower
re-fetch; ``AgentMemory`` is semantically meaningful to the agent's
own reasoning -- evicting it silently would change what the agent
concludes, not merely how fast it concludes it (design spec §14, §27).
Memory is scoped per ``task_id``, never global, so one task's recalled
context can never silently leak into an unrelated task's reasoning
(§14, §33).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from mineproductivity.agents.abstractions import AgentContext

__all__ = ["AgentMemory"]


class AgentMemory(ABC):
    """The contract a future memory-backend plugin implements (a
    vector store, a key-value store, a windowed in-context buffer, or
    any other recall mechanism). THIS MODULE SHIPS NO CONCRETE
    SUBCLASS -- choosing a specific embedding model, storage engine,
    or retention policy is exactly the kind of implementation decision
    this package's charter (design spec §3.1, §3.5, §4) excludes."""

    @abstractmethod
    def remember(self, task_id: str, key: str, value: Any, *, context: AgentContext) -> None:
        """Persist ``value`` under ``key`` for ``task_id``."""

    @abstractmethod
    def recall(self, task_id: str, key: str, *, context: AgentContext) -> Any | None:
        """Recall the value stored under ``key`` for ``task_id``. A
        miss returns ``None`` and is never an error (design spec §14)
        -- a calling ``Agent`` implementation reasons without whatever
        was not found."""
