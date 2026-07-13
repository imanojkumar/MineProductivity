"""The design spec §19 multi-agent worked example, end-to-end: a
``ShiftSupervisor``-category agent coordinating a ``Fleet`` and a
``Maintenance`` agent to recover night-shift haulage after a breakdown.
``WorkflowEngine`` decomposes a ``Goal`` into one task per named agent
(recording the delegation chain in open state attributes), runs them in
order, and audits each - no category-specific behavior lives in the
orchestrator (spec 11 §19).

All three concrete agents are example-local.

Run: python examples/agents/03_multi_agent_workflow.py
"""

from __future__ import annotations

from mineproductivity.agents import (
    Agent,
    AgentAuditTrail,
    AgentCategory,
    AgentContext,
    AgentMetadata,
    AgentResult,
    Goal,
    PolicyEngine,
    Task,
    TaskExecutor,
    TaskStatus,
    WorkflowEngine,
    register,
)
from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import InMemoryRepository


def _make_agent(code: str, category: AgentCategory, note: str) -> None:
    @register
    class _WorkflowAgent(Agent):
        meta = AgentMetadata(code=code, category=category, description=note)

        def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
            return AgentResult(
                output={
                    "agent": type(self).meta.code,
                    "delegation_chain": task.state.attributes["delegation_chain"],
                    "note": type(self).meta.description,
                }
            )


SUPERVISOR = "SHIFT_SUPERVISOR.NightShiftCoordinator"
FLEET = "FLEET.HaulReallocation"
MAINTENANCE = "MAINTENANCE.BreakdownTriage"

_make_agent(SUPERVISOR, AgentCategory.SHIFT_SUPERVISOR, "Coordinates the recovery.")
_make_agent(FLEET, AgentCategory.FLEET, "Reallocates trucks around the outage.")
_make_agent(MAINTENANCE, AgentCategory.MAINTENANCE, "Triages the failed unit.")


def main() -> None:
    print("--- 1. A goal names the agents (first = coordinator) and its criteria ---")
    goal = Goal(
        description="Recover night-shift haulage throughput after a fleet breakdown",
        success_criteria={
            "agent_codes": (SUPERVISOR, FLEET, MAINTENANCE),
            "target_tph": 1200.0,
        },
    )
    print(f"agents: {goal.success_criteria['agent_codes']}")

    print()
    print("--- 2. Preview the decomposition: one task per agent, chain recorded ---")
    preview_repository: InMemoryRepository[Task, str] = InMemoryRepository()
    preview_engine = WorkflowEngine(
        executor=TaskExecutor(
            repository=preview_repository,
            policy_engine=PolicyEngine(),
            audit_trail=AgentAuditTrail(),
            retry_policy=RetryPolicy(base_delay_s=0.0),
        ),
        repository=preview_repository,
    )
    for task in preview_engine.decompose(goal, context=AgentContext()):
        print(f"  {task.agent_code}: chain={task.state.attributes['delegation_chain']}")

    print()
    print("--- 3. Run in decomposition order; every result is audited ---")
    repository: InMemoryRepository[Task, str] = InMemoryRepository()
    trail = AgentAuditTrail()
    engine = WorkflowEngine(
        executor=TaskExecutor(
            repository=repository,
            policy_engine=PolicyEngine(),
            audit_trail=trail,
            retry_policy=RetryPolicy(base_delay_s=0.0),
        ),
        repository=repository,
    )
    results = engine.run(goal, context=AgentContext())
    for result in results:
        print(f"  {result.output['agent']} -> {result.output['note']}")

    print()
    print("--- 4. Outcome ---")
    print(f"results: {len(results)}; audit entries: {len(trail.query())}")
    print(
        "all tasks COMPLETED: "
        f"{all(task.status is TaskStatus.COMPLETED for task in repository.list())}"
    )


if __name__ == "__main__":
    main()
