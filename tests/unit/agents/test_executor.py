"""Tests for mineproductivity.agents.executor -- design spec §12's
policy-gate/dispatch/persistence/audit sequence, the approval-required,
denied, and cleared branches, failure recovery, the per-category
flagship agents (§35), and the §32 concurrency contract."""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import mineproductivity.agents.executor as executor_module
from mineproductivity.agents._registry import register
from mineproductivity.agents.abstractions import Agent, AgentContext
from mineproductivity.agents.approval import ApprovalRequest, ApprovalStatus
from mineproductivity.agents.audit import AgentAuditTrail
from mineproductivity.agents.capability import (
    AgentCapabilitySet,
    Permission,
    publish_capabilities,
)
from mineproductivity.agents.exceptions import (
    AgentExecutionError,
    AgentValidationError,
    PermissionDeniedError,
    TaskNotFoundError,
)
from mineproductivity.agents.executor import TaskExecutor
from mineproductivity.agents.metadata import AgentCategory, AgentMetadata
from mineproductivity.agents.policy import AgentPolicy, PolicyEngine, PolicyStatus, publish_policy
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.state import TaskState
from mineproductivity.agents.task import Task, TaskStatus
from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import InMemoryRepository
from mineproductivity.decision import Explanation


@register
class _EchoAgent(Agent):
    meta = AgentMetadata(
        code="FLEET.ExecutorEchoFixture",
        category=AgentCategory.FLEET,
        description="Echoes the task's goal code back as output.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        return AgentResult(
            output={"goal": task.goal_code},
            explanation=Explanation(premises=("scripted",), evidence_refs=()),
        )


_FLAKY_CALLS: dict[str, list[int]] = {}


@register
class _FlakyAgent(Agent):
    """Fails transiently twice per task, succeeds on the third
    attempt -- attempt bookkeeping lives module-side so the agent
    instance itself stays stateless (design spec §32)."""

    meta = AgentMetadata(
        code="MAINTENANCE.ExecutorFlakyFixture",
        category=AgentCategory.MAINTENANCE,
        description="Recovers on the third attempt.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        calls = _FLAKY_CALLS.setdefault(task.id, [])
        calls.append(id(context))
        if len(calls) < 3:
            raise RuntimeError("transient outage")
        return AgentResult(output={"attempts": len(calls)})


@register
class _AlwaysRaisesAgent(Agent):
    meta = AgentMetadata(
        code="SAFETY.ExecutorRaisingFixture",
        category=AgentCategory.SAFETY,
        description="Always fails transiently.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        raise RuntimeError("permanent transient-looking failure")


@register
class _NonRecoverableAgent(Agent):
    meta = AgentMetadata(
        code="ESG.ExecutorNonRecoverableFixture",
        category=AgentCategory.ESG,
        description="Fails non-recoverably.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        raise ValueError("malformed downstream payload")


def _retry_policy(max_attempts: int = 3) -> RetryPolicy:
    return RetryPolicy(
        max_attempts=max_attempts, base_delay_s=0.0, retryable_exceptions=(RuntimeError,)
    )


def _env(
    *, policy_engine: PolicyEngine | None = None, max_attempts: int = 3
) -> tuple[InMemoryRepository[Task, str], AgentAuditTrail, TaskExecutor]:
    repository: InMemoryRepository[Task, str] = InMemoryRepository()
    trail = AgentAuditTrail()
    executor = TaskExecutor(
        repository=repository,
        policy_engine=policy_engine if policy_engine is not None else PolicyEngine(),
        audit_trail=trail,
        retry_policy=_retry_policy(max_attempts),
    )
    return repository, trail, executor


def _task(agent_code: str, task_id: str | None = None, **attributes: object) -> Task:
    return Task(
        id=task_id or f"TASK-{uuid.uuid4().hex[:12]}",
        goal_code="GOAL.ExecutorTest",
        agent_code=agent_code,
        state=TaskState(attributes={"provisioned": True, "pit": "north", **attributes}),
    )


class TestClearedBranch:
    def test_dispatch_persists_completed_and_audits(self) -> None:
        repository, trail, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture")
        repository.add(task)
        result = executor.execute(task.id, task, context=AgentContext())
        assert result.task_id == task.id
        assert result.output["goal"] == "GOAL.ExecutorTest"
        assert repository.get(task.id).status is TaskStatus.COMPLETED
        entries = trail.query(scope={"pit": "north"})
        assert len(entries) == 1
        assert entries[0].agent_code == "FLEET.ExecutorEchoFixture"
        assert entries[0].result is result

    def test_terminal_task_is_skipped_with_a_warning_and_no_second_audit(self) -> None:
        repository, trail, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture")
        repository.add(task)
        executor.execute(task.id, task, context=AgentContext())
        again = executor.execute(task.id, task, context=AgentContext())
        assert "terminal" in again.warnings[0]
        assert len(trail.query()) == 1

    def test_paused_task_is_dispatchable(self) -> None:
        """Design spec §11: Paused -> Running via caller-requested
        resume -- calling execute() is that request."""
        repository, _, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture")
        repository.add(task.with_state(task.state, status=TaskStatus.PAUSED))
        executor.execute(task.id, task, context=AgentContext())
        assert repository.get(task.id).status is TaskStatus.COMPLETED

    def test_missing_task_raises(self) -> None:
        _, _, executor = _env()
        with pytest.raises(TaskNotFoundError, match="stored"):
            executor.execute(
                "TASK-NEVER-STORED",
                _task("FLEET.ExecutorEchoFixture"),
                context=AgentContext(),
            )

    def test_unregistered_agent_raises(self) -> None:
        repository, _, executor = _env()
        task = _task(f"FLEET.NeverRegistered{uuid.uuid4().hex}")
        repository.add(task)
        with pytest.raises(TaskNotFoundError, match="registered"):
            executor.execute(task.id, task, context=AgentContext())

    def test_repr(self) -> None:
        assert "TaskExecutor" in repr(_env()[2])


class TestPolicyGate:
    @staticmethod
    def _gated(capability: str, *, denies: bool = False) -> str:
        """Publish an Active gate policy scoped to ``capability`` and
        grant the echo agent that capability."""
        publish_policy(
            AgentPolicy(
                code=f"POLICY.ExecutorGate{uuid.uuid4().hex[:8]}",
                rule=f"capability={capability} -> {'deny' if denies else 'require_approval'}",
                status=PolicyStatus.ACTIVE,
                requires_approval=not denies,
                denies=denies,
            )
        )
        publish_capabilities(
            AgentCapabilitySet(
                agent_code="FLEET.ExecutorEchoFixture",
                permissions=(Permission(capability=capability),),
            )
        )
        return capability

    def test_approval_required_routes_to_awaiting_approval(self) -> None:
        capability = self._gated(f"cap_{uuid.uuid4().hex[:8]}")
        repository, trail, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture", required_capabilities=(capability,))
        repository.add(task)
        result = executor.execute(task.id, task, context=AgentContext())
        assert "approval" in result.warnings[0]
        assert repository.get(task.id).status is TaskStatus.AWAITING_APPROVAL
        assert trail.query() == ()

    def test_execute_on_an_awaiting_task_stays_paused(self) -> None:
        capability = self._gated(f"cap_{uuid.uuid4().hex[:8]}")
        repository, _, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture", required_capabilities=(capability,))
        repository.add(task)
        executor.execute(task.id, task, context=AgentContext())
        again = executor.execute(task.id, task, context=AgentContext())
        assert "resume()" in again.warnings[0]
        assert repository.get(task.id).status is TaskStatus.AWAITING_APPROVAL

    def test_approved_resolution_resumes_to_completed(self) -> None:
        """Design spec §16: Approved transitions AwaitingApproval ->
        Running and dispatches through to Completed."""
        capability = self._gated(f"cap_{uuid.uuid4().hex[:8]}")
        repository, trail, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture", required_capabilities=(capability,))
        repository.add(task)
        executor.execute(task.id, task, context=AgentContext())
        result = executor.resume(
            task.id,
            approval=ApprovalRequest(
                task_id=task.id,
                requested_action=capability,
                status=ApprovalStatus.APPROVED,
                approver="supervisor",
            ),
            context=AgentContext(),
        )
        assert result.output["goal"] == "GOAL.ExecutorTest"
        assert repository.get(task.id).status is TaskStatus.COMPLETED
        assert len(trail.query()) == 1

    def test_rejected_resolution_fails_the_task_with_an_audited_warning(self) -> None:
        capability = self._gated(f"cap_{uuid.uuid4().hex[:8]}")
        repository, trail, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture", required_capabilities=(capability,))
        repository.add(task)
        executor.execute(task.id, task, context=AgentContext())
        result = executor.resume(
            task.id,
            approval=ApprovalRequest(
                task_id=task.id,
                requested_action=capability,
                status=ApprovalStatus.REJECTED,
                approver="supervisor",
            ),
            context=AgentContext(),
        )
        assert "rejected" in result.warnings[0]
        assert capability in result.warnings[0]
        assert repository.get(task.id).status is TaskStatus.FAILED
        assert trail.query()[0].result is result

    def test_denied_raises_and_persists_nothing(self) -> None:
        """Design spec §10, §30: a hard stop, never a completed
        AgentResult."""
        capability = self._gated(f"cap_{uuid.uuid4().hex[:8]}", denies=True)
        repository, trail, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture", required_capabilities=(capability,))
        repository.add(task)
        with pytest.raises(PermissionDeniedError):
            executor.execute(task.id, task, context=AgentContext())
        assert repository.get(task.id).status is TaskStatus.SCHEDULED
        assert trail.query() == ()

    def test_missing_capability_is_denied(self) -> None:
        repository, _, executor = _env()
        task = _task(
            "FLEET.ExecutorEchoFixture",
            required_capabilities=(f"cap_never_granted_{uuid.uuid4().hex[:8]}",),
        )
        repository.add(task)
        with pytest.raises(PermissionDeniedError, match="does not carry"):
            executor.execute(task.id, task, context=AgentContext())

    def test_resume_rejects_an_unresolved_request(self) -> None:
        capability = self._gated(f"cap_{uuid.uuid4().hex[:8]}")
        repository, _, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture", required_capabilities=(capability,))
        repository.add(task)
        executor.execute(task.id, task, context=AgentContext())
        with pytest.raises(AgentValidationError, match="unresolved"):
            executor.resume(
                task.id,
                approval=ApprovalRequest(task_id=task.id, requested_action=capability),
                context=AgentContext(),
            )

    def test_resume_rejects_a_mismatched_task_id(self) -> None:
        repository, _, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture")
        repository.add(task)
        with pytest.raises(AgentValidationError, match="does not name"):
            executor.resume(
                task.id,
                approval=ApprovalRequest(
                    task_id="TASK-OTHER",
                    requested_action="x",
                    status=ApprovalStatus.APPROVED,
                ),
                context=AgentContext(),
            )

    def test_resume_rejects_a_task_that_is_not_awaiting_approval(self) -> None:
        repository, _, executor = _env()
        task = _task("FLEET.ExecutorEchoFixture")
        repository.add(task)
        with pytest.raises(AgentValidationError, match="awaiting_approval"):
            executor.resume(
                task.id,
                approval=ApprovalRequest(
                    task_id=task.id, requested_action="x", status=ApprovalStatus.APPROVED
                ),
                context=AgentContext(),
            )

    def test_policy_is_evaluated_before_every_dispatch(self) -> None:
        """Design spec §35 proof 6: every execute() path calls
        PolicyEngine.evaluate before Agent._act."""
        order: list[str] = []

        class _RecordingEngine(PolicyEngine):
            def evaluate(self, task, *, capabilities, policies):  # type: ignore[no-untyped-def]
                order.append("evaluate")
                return super().evaluate(task, capabilities=capabilities, policies=policies)

        code = f"DISPATCH.OrderFixture{uuid.uuid4().hex[:8]}"

        @register
        class _OrderAgent(Agent):
            meta = AgentMetadata(
                code=code, category=AgentCategory.DISPATCH, description="Records order."
            )

            def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
                order.append("act")
                return AgentResult()

        repository, _, executor = _env(policy_engine=_RecordingEngine())
        task = _task(code)
        repository.add(task)
        executor.execute(task.id, task, context=AgentContext())
        assert order == ["evaluate", "act"]

    def test_executor_never_constructs_or_resolves_an_approval_request(self) -> None:
        """Design spec §16, §34: resolution is exclusively a caller
        action -- the executor's own source never instantiates one."""
        source = Path(executor_module.__file__).read_text(encoding="utf-8")
        assert "ApprovalRequest(" not in source


class TestFailureRecovery:
    def test_transient_failure_retries_and_succeeds(self) -> None:
        repository, _, executor = _env()
        task = _task("MAINTENANCE.ExecutorFlakyFixture")
        repository.add(task)
        result = executor.execute(task.id, task, context=AgentContext())
        assert result.output["attempts"] == 3
        assert repository.get(task.id).status is TaskStatus.COMPLETED

    def test_context_is_assembled_once_never_refetched_per_retry(self) -> None:
        """Design spec §27, §36: the same AgentContext instance is
        handed to every retry attempt."""
        repository, _, executor = _env()
        task = _task("MAINTENANCE.ExecutorFlakyFixture")
        repository.add(task)
        executor.execute(task.id, task, context=AgentContext())
        assert len(set(_FLAKY_CALLS[task.id])) == 1

    def test_exhausted_retries_fail_the_task_never_retrying_indefinitely(self) -> None:
        repository, _, executor = _env(max_attempts=2)
        task = _task("SAFETY.ExecutorRaisingFixture")
        repository.add(task)
        with pytest.raises(AgentExecutionError, match="retries exhausted after 2"):
            executor.execute(task.id, task, context=AgentContext())
        assert repository.get(task.id).status is TaskStatus.FAILED

    def test_non_recoverable_failure_fails_immediately(self) -> None:
        repository, _, executor = _env()
        task = _task("ESG.ExecutorNonRecoverableFixture")
        repository.add(task)
        with pytest.raises(AgentExecutionError, match="non-recoverable"):
            executor.execute(task.id, task, context=AgentContext())
        assert repository.get(task.id).status is TaskStatus.FAILED

    def test_retry_never_reassigns_to_a_different_agent(self) -> None:
        """Design spec §12, §34: the executor's source dispatches via
        the one agent resolved from Task.agent_code -- there is no
        second REGISTRY lookup inside the retry loop."""
        source = Path(executor_module.__file__).read_text(encoding="utf-8")
        assert source.count("REGISTRY.get(") == 1


class TestFlagshipCategories:
    @pytest.mark.parametrize("category", list(AgentCategory), ids=lambda c: c.value)
    def test_one_flagship_agent_per_category(self, category: AgentCategory) -> None:
        """Design spec §35: a scripted task with a known expected
        AgentResult, per category."""
        code = f"{category.name}.Flagship{uuid.uuid4().hex[:8]}"
        expected = {"category": category.value}

        @register
        class _Flagship(Agent):
            meta = AgentMetadata(
                code=code, category=category, description=f"Flagship {category.value} agent."
            )

            def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
                return AgentResult(output={"category": type(self).meta.category.value})

        repository, _, executor = _env()
        task = _task(code)
        repository.add(task)
        result = executor.execute(task.id, task, context=AgentContext())
        assert dict(result.output) == expected


class TestConcurrency:
    def test_independent_tasks_execute_fully_in_parallel(self) -> None:
        """Design spec §32: distinct ids target distinct repository
        keys -- no contention, no lost update."""
        repository, trail, executor = _env()
        tasks = [_task("FLEET.ExecutorEchoFixture") for _ in range(12)]
        for task in tasks:
            repository.add(task)

        def _one(task: Task) -> AgentResult:
            return executor.execute(task.id, task, context=AgentContext())

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(_one, tasks))
        assert len(results) == 12
        assert all(repository.get(task.id).status is TaskStatus.COMPLETED for task in tasks)
        assert len(trail.query()) == 12
