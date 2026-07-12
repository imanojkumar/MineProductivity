"""``TaskRepository``: where tasks are stored (design spec §25).

A literal ``type`` alias over ``core.BaseRepository[Task, str]`` --
not a new ABC, not a structural echo -- because ``Task`` genuinely
satisfies ``BaseRepository``'s ``TEntity: BaseEntity[Any]`` bound,
exactly mirroring ``optimization.OptimizationRunRepository``'s own
identical reuse (spec 10 §24): the fourth occurrence of this exact
reuse in the series. The reference implementation is
``core.InMemoryRepository[Task, str]()``, reused as-is with zero new
persistence code; it provides **no** locking of its own -- a
production-grade implementation MUST serialize concurrent writes for
the same ``id`` (design spec §32).
"""

from __future__ import annotations

from mineproductivity.core import BaseRepository

from mineproductivity.agents.task import Task

__all__ = ["TaskRepository"]

type TaskRepository = BaseRepository[Task, str]
