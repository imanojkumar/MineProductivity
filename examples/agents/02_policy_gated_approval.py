"""Human-in-the-loop approval (design spec §10, §16): a governed
``AgentPolicy`` gates a capability behind approval; the executor routes
the task to ``AwaitingApproval`` and only a caller-supplied, resolved
``ApprovalRequest`` (never one the executor constructs) resumes it. A
second, denying policy shows the hard-stop ``PermissionDeniedError``
branch.

The concrete ``Agent`` is example-local. ``publish_policy`` and
``publish_capabilities`` are process-wide governance functions,
deliberately not in the package's top-level ``__all__`` (spec 11 §7).

Run: python examples/agents/02_policy_gated_approval.py
"""

from __future__ import annotations

from mineproductivity.agents import (
    Agent,
    AgentAuditTrail,
    AgentCapabilitySet,
    AgentContext,
    AgentMetadata,
    AgentCategory,
    AgentResult,
    ApprovalRequest,
    ApprovalStatus,
    AgentPolicy,
    Permission,
    PermissionDeniedError,
    PolicyEngine,
    PolicyStatus,
    Task,
    TaskExecutor,
    TaskState,
    TaskStatus,
    register,
)
from mineproductivity.agents.capability import publish_capabilities
from mineproductivity.agents.policy import publish_policy
from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import InMemoryRepository

APPROVAL_CAP = "reallocate_fleet"
DENIED_CAP = "shut_down_pit"


@register
class DispatchAgent(Agent):
    """Adjusts dispatch assignments — example-local, stateless."""

    meta = AgentMetadata(
        code="DISPATCH.ShiftAdjust",
        category=AgentCategory.DISPATCH,
        description="Adjusts dispatch assignments for a shift.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        return AgentResult(output={"goal": task.goal_code, "adjusted": True})


def _new_executor() -> tuple[InMemoryRepository[Task, str], AgentAuditTrail, TaskExecutor]:
    repository: InMemoryRepository[Task, str] = InMemoryRepository()
    trail = AgentAuditTrail()
    executor = TaskExecutor(
        repository=repository,
        policy_engine=PolicyEngine(),
        audit_trail=trail,
        retry_policy=RetryPolicy(base_delay_s=0.0),
    )
    return repository, trail, executor


def main() -> None:
    print("--- 1. Govern one capability behind approval, deny another outright ---")
    publish_policy(
        AgentPolicy(
            code="POLICY.FleetReallocationApproval",
            rule=f"capability={APPROVAL_CAP} -> require_approval",
            status=PolicyStatus.ACTIVE,
            requires_approval=True,
        )
    )
    publish_policy(
        AgentPolicy(
            code="POLICY.PitShutdownDenied",
            rule=f"capability={DENIED_CAP} -> deny",
            status=PolicyStatus.ACTIVE,
            denies=True,
        )
    )
    publish_capabilities(
        AgentCapabilitySet(
            agent_code="DISPATCH.ShiftAdjust",
            permissions=(Permission(capability=APPROVAL_CAP), Permission(capability=DENIED_CAP)),
        )
    )
    print(f"approval-gated: {APPROVAL_CAP!r}; denied: {DENIED_CAP!r}")

    print()
    print("--- 2. An approval-gated task routes to AwaitingApproval, unaudited ---")
    repository, trail, executor = _new_executor()
    task = Task(
        id="TASK-APPROVE-1",
        goal_code="GOAL.ReallocateNightFleet",
        agent_code="DISPATCH.ShiftAdjust",
        state=TaskState(attributes={"pit": "north", "required_capabilities": (APPROVAL_CAP,)}),
    )
    repository.add(task)
    gated = executor.execute(task.id, task, context=AgentContext())
    print(f"warning: {gated.warnings[0]}")
    print(f"status: {repository.get(task.id).status.value}; audit entries: {len(trail.query())}")

    print()
    print("--- 3. A supervisor approves; resume() dispatches through to Completed ---")
    approved = executor.resume(
        task.id,
        approval=ApprovalRequest(
            task_id=task.id,
            requested_action=APPROVAL_CAP,
            status=ApprovalStatus.APPROVED,
            approver="shift_supervisor",
        ),
        context=AgentContext(),
    )
    print(f"output: {dict(approved.output)}")
    print(f"status: {repository.get(task.id).status.value}; audit entries: {len(trail.query())}")

    print()
    print("--- 4. A denying policy is a hard stop, never a completed result ---")
    repository2, _, executor2 = _new_executor()
    denied_task = Task(
        id="TASK-DENY-1",
        goal_code="GOAL.EmergencyPitShutdown",
        agent_code="DISPATCH.ShiftAdjust",
        state=TaskState(attributes={"required_capabilities": (DENIED_CAP,)}),
    )
    repository2.add(denied_task)
    try:
        executor2.execute(denied_task.id, denied_task, context=AgentContext())
    except PermissionDeniedError as error:
        print(f"PermissionDeniedError raised: {error}")
    print(f"status stays: {repository2.get(denied_task.id).status is TaskStatus.SCHEDULED}")


if __name__ == "__main__":
    main()
