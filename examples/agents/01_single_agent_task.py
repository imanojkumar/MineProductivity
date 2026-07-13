"""A single agent task, end-to-end (design spec §12): a governed
``Task`` dispatched through ``TaskExecutor`` - policy gate → dispatch →
persist → audit - producing an audited ``AgentResult``.

The concrete ``Agent`` below is example-local: the package ships zero
concrete agents by design (``Agent``/``Tool``/``AgentMemory`` are
interface-only extension points, spec 11 §3.1, §4). Choosing a
reasoning backend is exactly the decision this package excludes.

Run: python examples/agents/01_single_agent_task.py
"""

from __future__ import annotations

from mineproductivity.agents import (
    Agent,
    AgentContext,
    AgentMetadata,
    AgentResult,
    AgentAuditTrail,
    AgentCategory,
    PolicyEngine,
    Task,
    TaskExecutor,
    TaskState,
    TaskStatus,
    register,
)
from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import InMemoryRepository
from mineproductivity.decision import Explanation


@register
class HaulReallocationAgent(Agent):
    """Recommends a truck reallocation from the task's goal - a
    stateless, scripted reference agent; a real one would consult a
    reasoning backend and tools."""

    meta = AgentMetadata(
        code="FLEET.HaulReallocation",
        category=AgentCategory.FLEET,
        description="Recommends a truck reallocation for a haulage goal.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        target = float(task.state.attributes.get("target_tph", 0.0))
        return AgentResult(
            output={"goal": task.goal_code, "recommended_extra_trucks": 3, "target_tph": target},
            explanation=Explanation(
                premises=(f"target throughput {target:.0f} t/h not met",),
                evidence_refs=("UTIL.OEE", "HAUL.TruckCycleTime"),
            ),
        )


def main() -> None:
    print("--- 1. A governed task names its goal, its agent, and its scope ---")
    task = Task(
        id="TASK-HAUL-1",
        goal_code="GOAL.RecoverNightShiftHaulage",
        agent_code="FLEET.HaulReallocation",
        state=TaskState(attributes={"pit": "north", "target_tph": 1200.0}),
    )
    print(f"task={task.id} goal={task.goal_code!r} agent={task.agent_code!r}")

    print()
    print("--- 2. Dispatch through the executor: gate -> act -> persist -> audit ---")
    repository: InMemoryRepository[Task, str] = InMemoryRepository()
    repository.add(task)
    trail = AgentAuditTrail()
    executor = TaskExecutor(
        repository=repository,
        policy_engine=PolicyEngine(),
        audit_trail=trail,
        retry_policy=RetryPolicy(base_delay_s=0.0),
    )
    result = executor.execute(task.id, task, context=AgentContext())

    print()
    print("--- 3. The audited result ---")
    print(f"output: {dict(result.output)}")
    assert result.explanation is not None
    print(f"explanation premises: {result.explanation.premises}")
    print(f"task status COMPLETED: {repository.get(task.id).status is TaskStatus.COMPLETED}")

    print()
    print("--- 4. The append-only audit trail recorded it, queryable by scope ---")
    entries = trail.query(scope={"pit": "north"})
    print(f"audit entries for pit=north: {len(entries)} (agent {entries[0].agent_code})")


if __name__ == "__main__":
    main()
