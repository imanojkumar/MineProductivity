"""Agent discovery (design spec §23) -- category/scope-based lookup
over currently-known tasks, mirroring ``optimization.discovery``'s
identical pattern (spec 10 §22). The locked ``Task`` shape carries no
category field, so :func:`by_category` resolves lazily through
``REGISTRY`` (§22) at ``list()`` time via the task's own
``agent_code`` -- a task whose agent is unregistered simply does not
match (never raises) -- and :func:`by_scope` matches against the
task's own ``goal_code``/``agent_code``/``status`` fields plus its
open ``state.attributes`` mapping.
"""

from __future__ import annotations

from collections.abc import Mapping

from mineproductivity.core import BaseSpecification, PredicateSpecification

from mineproductivity.agents._registry import REGISTRY
from mineproductivity.agents.metadata import AgentCategory, AgentMetadata
from mineproductivity.agents.task import Task

__all__ = ["by_category", "by_scope"]


def _category_of(task: Task) -> AgentCategory | None:
    metadata = REGISTRY.metadata_for(task.agent_code)
    if metadata.is_nothing:
        return None
    found = metadata.unwrap()
    return found.category if isinstance(found, AgentMetadata) else None


def by_category(category: AgentCategory) -> BaseSpecification[Task]:
    """A specification satisfied by every task whose registered agent
    belongs to ``category`` -- compose with ``TaskRepository.list()``
    freely; an empty result is a legitimate answer, never a raise
    (design spec §23).

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[Task, str] = InMemoryRepository()
    >>> repository.list(by_category(AgentCategory.FLEET))
    []
    """
    return PredicateSpecification(lambda task: _category_of(task) is category)


def by_scope(scope: Mapping[str, str]) -> BaseSpecification[Task]:
    """A specification satisfied by every task carrying every
    key/value pair in ``scope``, resolved against ``goal_code``/
    ``agent_code``/``status`` first and the open ``state.attributes``
    mapping otherwise.

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[Task, str] = InMemoryRepository()
    >>> repository.list(by_scope({"agent_code": "FLEET.ReassignmentAdvisor"}))
    []
    """
    wanted = dict(scope)

    def _matches(task: Task) -> bool:
        for key, value in wanted.items():
            if key == "goal_code":
                observed: object = task.goal_code
            elif key == "agent_code":
                observed = task.agent_code
            elif key == "status":
                observed = task.status.value
            else:
                observed = task.state.attributes.get(key)
            if observed != value:
                return False
        return True

    return PredicateSpecification(_matches)
