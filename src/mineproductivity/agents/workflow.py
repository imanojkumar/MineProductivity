"""``WorkflowEngine``: goal decomposition and multi-agent
orchestration (design spec §13, §19).

Reuse audit: composes ``TaskExecutor`` (§12) for each individual
``Task`` rather than duplicating its dispatch/persistence/audit logic
-- the same composition-over-duplication posture
``simulation.ExperimentRunner`` establishes over
``SimulationExecutor`` (spec 09 §17). Where a decomposed ``Task``
calls for exploring hypotheses, the assigned ``Agent`` composes
``simulation.ExperimentRunner.run_trials`` directly; where it calls
for searching candidate plans, it composes
``optimization.OptimizationExecutor``/``optimization.PlanComparator``
directly (§13) -- never a re-derivation of either inside this module.
Sub-tasks are independently parallelizable by default (§36): each
targets a distinct repository key, never contending with any other's
write (§32).

Disclosed reference resolution of spec-level imprecision: which
``Agent`` categories a ``Goal`` decomposes into is itself a
reasoning-backend decision this package's charter excludes (§19), so
the reference decomposition strategy is caller-authored -- the
``goal.success_criteria["agent_codes"]`` open-mapping entry names the
registered agent codes to assign, in order, the first acting as
coordinator; every subsequent task carries the delegation chain in
``Task.state.attributes["delegation_chain"]`` (§18's escape hatch).
An absent/empty entry decomposes to zero tasks -- a legitimately
incomplete input, never a raise (§30), mirroring
``simulation.ExperimentRunner``'s zero-trials convention.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

from mineproductivity.agents.abstractions import AgentContext
from mineproductivity.agents.executor import TaskExecutor
from mineproductivity.agents.goal import Goal
from mineproductivity.agents.persistence import TaskRepository
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.state import TaskState
from mineproductivity.agents.task import Task

__all__ = ["WorkflowEngine"]


class WorkflowEngine:
    """Decomposes a ``Goal`` into one or more ``Task``\\ s, each
    assigned to a registered ``Agent``, and coordinates delegation
    between them (design spec §13, §19) -- the one place a ``Goal``
    becomes multiple ``Task``\\ s."""

    def __init__(self, *, executor: TaskExecutor, repository: TaskRepository) -> None:
        self._executor = executor
        self._repository = repository

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(executor={self._executor!r}, repository={self._repository!r})"
        )

    def decompose(self, goal: Goal, *, context: AgentContext) -> Sequence[Task]:
        """Decompose ``goal`` into provisioned ``Task``\\ s -- one per
        agent code named by the caller-authored
        ``success_criteria["agent_codes"]`` entry, each persisted into
        the repository (``Scheduled``) ready for execution. The first
        named agent coordinates; each subsequent task's
        ``delegation_chain`` records the handoff (design spec §18)."""
        raw = goal.success_criteria.get("agent_codes", ())
        agent_codes = [str(code) for code in raw] if not isinstance(raw, str) else [raw]
        if not agent_codes:
            return ()

        goal_code = goal.description
        suffix = uuid.uuid4().hex[:8]
        coordinator = agent_codes[0]
        tasks: list[Task] = []
        for index, agent_code in enumerate(agent_codes):
            chain = (coordinator,) if index == 0 else (coordinator, agent_code)
            task = Task(
                id=f"{goal_code}::task-{index:04d}-{suffix}",
                goal_code=goal_code,
                agent_code=agent_code,
                state=TaskState(
                    attributes={
                        "goal": goal.description,
                        "delegation_chain": chain,
                        **{
                            key: value
                            for key, value in goal.success_criteria.items()
                            if key != "agent_codes"
                        },
                    }
                ),
            )
            self._repository.add(task)
            tasks.append(task)
        return tuple(tasks)

    def run(self, goal: Goal, *, context: AgentContext) -> Sequence[AgentResult]:
        """Decompose ``goal`` and execute every resulting ``Task`` via
        the composed ``TaskExecutor`` -- sub-tasks dispatch
        concurrently (design spec §36); results preserve decomposition
        order regardless of completion order."""
        tasks = self.decompose(goal, context=context)
        if not tasks:
            return ()

        def _one(task: Task) -> AgentResult:
            return self._executor.execute(task.id, task, context=context)

        with ThreadPoolExecutor() as pool:
            return tuple(pool.map(_one, tasks))
