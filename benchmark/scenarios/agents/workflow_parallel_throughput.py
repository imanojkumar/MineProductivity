"""Benchmark scenario: task-dispatch throughput, sequential vs.
parallel, at representative task counts (AI Agents implementation
checklist, Benchmarks). ``WorkflowEngine.run`` is a thin ordered loop
over ``TaskExecutor.execute``; this measures that per-task dispatch
path (policy gate → act → persist → audit) directly.

Independent ``Task``s (distinct ids) target distinct repository keys
and execute without contention (design spec §32), so the workload
parallelizes across a thread pool. The example-local agent is a
trivial, fast echo so the measurement isolates the executor's
gate/dispatch/persistence/audit overhead, not reasoning-backend cost.

Standalone by design. Results are recorded in
``benchmark/reports/agents/``.

Run: python benchmark/scenarios/agents/workflow_parallel_throughput.py
"""

from __future__ import annotations

import platform
import time
from concurrent.futures import ThreadPoolExecutor

from mineproductivity.agents import (
    Agent,
    AgentAuditTrail,
    AgentContext,
    AgentCategory,
    AgentMetadata,
    AgentResult,
    PolicyEngine,
    Task,
    TaskExecutor,
    TaskState,
    register,
)
from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import InMemoryRepository

TASK_COUNTS = (50, 200, 1_000)
WORKERS = 8


@register
class _BenchmarkEchoAgent(Agent):
    meta = AgentMetadata(
        code="FLEET.BenchmarkEcho",
        category=AgentCategory.FLEET,
        description="Trivial fast echo isolating executor dispatch/persistence/audit cost.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        return AgentResult(output={"goal": task.goal_code})


def _tasks(count: int) -> list[Task]:
    return [
        Task(
            id=f"TASK-{index:06d}",
            goal_code="GOAL.Benchmark",
            agent_code="FLEET.BenchmarkEcho",
            state=TaskState(attributes={"provisioned": True}),
        )
        for index in range(count)
    ]


def _new_executor() -> tuple[InMemoryRepository[Task, str], TaskExecutor]:
    repository: InMemoryRepository[Task, str] = InMemoryRepository()
    executor = TaskExecutor(
        repository=repository,
        policy_engine=PolicyEngine(),
        audit_trail=AgentAuditTrail(),
        retry_policy=RetryPolicy(base_delay_s=0.0),
    )
    return repository, executor


def _sequential(count: int, context: AgentContext) -> float:
    repository, executor = _new_executor()
    tasks = _tasks(count)
    for task in tasks:
        repository.add(task)
    start = time.perf_counter()
    for task in tasks:
        executor.execute(task.id, task, context=context)
    return time.perf_counter() - start


def _parallel(count: int, context: AgentContext) -> float:
    repository, executor = _new_executor()
    tasks = _tasks(count)
    for task in tasks:
        repository.add(task)

    def _one(task: Task) -> None:
        executor.execute(task.id, task, context=context)

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(_one, tasks))
    return time.perf_counter() - start


def main() -> None:
    print("AI Agents task-dispatch throughput (sequential vs. parallel)")
    print(f"python={platform.python_version()} machine={platform.machine()} workers={WORKERS}")
    print()
    print(f"{'tasks':>8} {'seq_ms':>10} {'seq_per_s':>12} {'par_ms':>10} {'par_per_s':>12}")

    context = AgentContext()
    for count in TASK_COUNTS:
        seq_seconds = _sequential(count, context)
        par_seconds = _parallel(count, context)
        print(
            f"{count:>8} {seq_seconds * 1e3:>10.2f} {count / seq_seconds:>12.0f}"
            f" {par_seconds * 1e3:>10.2f} {count / par_seconds:>12.0f}"
        )


if __name__ == "__main__":
    main()
