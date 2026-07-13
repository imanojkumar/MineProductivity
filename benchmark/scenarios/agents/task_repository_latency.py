"""Benchmark scenario: ``TaskRepository.get()``/``list()`` latency at
representative task-population scale (AI Agents implementation
checklist, Benchmarks).

Standalone by design -- mirroring the established harness-free posture
of the other packages' scenarios. Results are recorded in
``benchmark/reports/agents/``.

Scale rationale: a busy site's autonomous/semi-autonomous workload
accumulates tasks continuously; 10³/10⁴/10⁵ spans "a shift" through
"a quarter, never pruned". ``get()`` is the hot per-dispatch path and
must stay O(1) (design spec §36).

Run: python benchmark/scenarios/agents/task_repository_latency.py
"""

from __future__ import annotations

import platform
import time

from mineproductivity.agents import Task, TaskState, by_scope
from mineproductivity.core import InMemoryRepository

POPULATIONS = (1_000, 10_000, 100_000)
GET_REPEATS = 10_000
LIST_REPEATS = 5


def _task(index: int) -> Task:
    agent_code = "FLEET.Reallocation" if index % 2 == 0 else "MAINTENANCE.Triage"
    return Task(
        id=f"TASK-{index:06d}",
        goal_code="GOAL.Benchmark",
        agent_code=agent_code,
        state=TaskState(attributes={"pit": "north"}),
    )


def main() -> None:
    print("TaskRepository.get()/list() latency (core.InMemoryRepository reference)")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print()
    print(f"{'tasks':>8} {'get_us':>8} {'list_all_ms':>12} {'list_scope_ms':>14} {'matches':>8}")

    for population in POPULATIONS:
        repository: InMemoryRepository[Task, str] = InMemoryRepository()
        for index in range(population):
            repository.add(_task(index))

        middle_id = f"TASK-{population // 2:06d}"
        start = time.perf_counter()
        for _ in range(GET_REPEATS):
            repository.get(middle_id)
        get_seconds = (time.perf_counter() - start) / GET_REPEATS

        start = time.perf_counter()
        for _ in range(LIST_REPEATS):
            everything = repository.list()
        list_all_seconds = (time.perf_counter() - start) / LIST_REPEATS

        specification = by_scope({"agent_code": "FLEET.Reallocation"})
        start = time.perf_counter()
        for _ in range(LIST_REPEATS):
            matched = repository.list(specification)
        list_scope_seconds = (time.perf_counter() - start) / LIST_REPEATS

        assert len(everything) == population
        print(
            f"{population:>8} {get_seconds * 1e6:>8.2f} {list_all_seconds * 1e3:>12.2f}"
            f" {list_scope_seconds * 1e3:>14.2f} {len(matched):>8}"
        )


if __name__ == "__main__":
    main()
