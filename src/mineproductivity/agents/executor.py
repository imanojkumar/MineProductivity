"""``TaskExecutor``: orchestrates one ``Task`` (design spec §12).

Reuse audit: dispatch reads the registered ``Agent`` off
``Task.agent_code`` via ``REGISTRY``, exactly once per task; the
``remove``-then-``add`` repository pair is the same single, narrow
mutable operation every prior package concentrates its mutation into,
with a serialization violation surfacing as ``AgentExecutionError``
(§32). ``connectors.RetryPolicy``/``BackoffStrategy`` (spec 04 §10)
are composed directly as the *configuration shape* for this module's
own retry loop -- the value objects, not connectors' own
retry-execution code, since that is coupled to
``connectors.SourceUnavailableError``-style exceptions this package's
own failures are not. ``retry_policy.is_retryable`` decides what
counts as a transient (recoverable) failure; retries always target
the *same* agent's ``_act`` -- a task is never silently reassigned
(§12, §34) -- and exhausted retries transition the task to ``Failed``,
never retrying indefinitely.

Disclosed reference resolutions of spec-level imprecision:

- The §12 sequence diagram's ``final_state`` is the task's current
  state -- an ``Agent`` communicates its outcome via ``AgentResult``,
  and this executor never invents a state on its behalf.
- The policy gate's inputs come from the governed stores:
  ``capability.published_capabilities(task.agent_code)`` (an agent
  with no published set holds no permissions) and
  ``policy.published_policies()`` (the engine filters ``Active``).
- ``AgentAuditEntry.scope`` is derived from the task's own
  string-valued ``state.attributes`` entries -- the same open scope
  vocabulary ``discovery.by_scope`` (§23) already queries.
- :meth:`TaskExecutor.resume` is the §16 resolution-*application*
  seam: the executor never resolves an ``ApprovalRequest`` itself --
  resolution (``PENDING`` -> ``APPROVED``/``REJECTED``) is exclusively
  a caller action; this method only applies the documented §11
  transition an already-resolved request implies.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import DuplicateError, NotFoundError
from mineproductivity.registry import UnregisteredLookupError

from mineproductivity.agents._registry import REGISTRY
from mineproductivity.agents.abstractions import Agent, AgentContext
from mineproductivity.agents.approval import ApprovalRequest, ApprovalStatus
from mineproductivity.agents.audit import AgentAuditEntry, AgentAuditTrail
from mineproductivity.agents.capability import AgentCapabilitySet, published_capabilities
from mineproductivity.agents.exceptions import (
    AgentExecutionError,
    AgentValidationError,
    TaskNotFoundError,
)
from mineproductivity.agents.persistence import TaskRepository
from mineproductivity.agents.policy import PolicyEngine, _ApprovalRequired, published_policies
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.task import Task, TaskStatus

__all__ = ["TaskExecutor"]

_TERMINAL = (TaskStatus.COMPLETED, TaskStatus.FAILED)


class TaskExecutor:
    """Orchestrates one ``Task``: evaluates policy, dispatches to the
    registered ``Agent``'s ``_act``, gates on approval, retries on a
    recoverable failure, persists the resulting state via the
    repository swap, and appends terminal outcomes to the audit trail
    (design spec §12's sequence diagram)."""

    def __init__(
        self,
        *,
        repository: TaskRepository,
        policy_engine: PolicyEngine,
        audit_trail: AgentAuditTrail,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._repository = repository
        self._policy_engine = policy_engine
        self._audit_trail = audit_trail
        self._retry_policy = retry_policy if retry_policy is not None else RetryPolicy()

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(repository={self._repository!r}, "
            f"policy_engine={self._policy_engine!r}, "
            f"audit_trail={self._audit_trail!r}, "
            f"retry_policy={self._retry_policy!r})"
        )

    def execute(self, task_id: str, task: Task, *, context: AgentContext) -> AgentResult:
        """Execute ``task`` for the instance stored under ``task_id``.

        A task already ``Completed``/``Failed`` is terminal (design
        spec §11): execution is skipped and a warning-carrying result
        returned. A task stored as ``AwaitingApproval`` stays paused
        -- only :meth:`resume` with a resolved ``ApprovalRequest``
        moves it (§16).

        Raises
        ------
        TaskNotFoundError
            If no task is stored under ``task_id``, or no ``Agent``
            is registered for ``task.agent_code``.
        PermissionDeniedError
            If ``PolicyEngine.evaluate`` denies the task outright --
            never persisted as a completed ``AgentResult`` (§10, §30).
        AgentExecutionError
            If the agent's ``_act`` failed (retries exhausted or a
            non-recoverable failure; the task is marked ``Failed``
            first, §12), or the repository's per-id write
            serialization contract was violated mid-swap (§32).
        """
        stored = self._find(task_id)

        if stored.status in _TERMINAL:
            return AgentResult(
                task_id=task_id,
                warnings=(
                    f"task is {stored.status.value}; execution skipped "
                    f"({stored.status.value} is terminal)",
                ),
            )
        if stored.status is TaskStatus.AWAITING_APPROVAL:
            return AgentResult(
                task_id=task_id,
                warnings=(
                    "task is awaiting approval; resolve its ApprovalRequest and "
                    "apply it via resume()",
                ),
            )

        capabilities = published_capabilities(stored.agent_code)
        if capabilities is None:
            capabilities = AgentCapabilitySet(agent_code=stored.agent_code, permissions=())
        gate = self._policy_engine.evaluate(
            stored, capabilities=capabilities, policies=published_policies()
        )
        if gate.is_err:
            error = gate.error
            if isinstance(error, _ApprovalRequired):
                self._replace(
                    task_id, stored.with_state(stored.state, status=TaskStatus.AWAITING_APPROVAL)
                )
                return AgentResult(task_id=task_id, warnings=(str(error),))
            raise error

        return self._dispatch(task_id, stored, context=context)

    def resume(
        self, task_id: str, *, approval: ApprovalRequest, context: AgentContext
    ) -> AgentResult:
        """Apply an already-resolved ``approval`` to the
        ``AwaitingApproval`` task stored under ``task_id`` (design
        spec §16): ``APPROVED`` transitions it back to ``Running`` and
        dispatches; ``REJECTED`` transitions it directly to ``Failed``,
        carrying the rejection as a warning on the returned (and
        audited) ``AgentResult``. This executor never resolves the
        request itself -- a still-``PENDING`` request is rejected as
        structurally invalid.

        Raises
        ------
        TaskNotFoundError
            If no task is stored under ``task_id``.
        AgentValidationError
            If ``approval`` is still ``PENDING``, names a different
            ``task_id``, or the stored task is not
            ``AwaitingApproval``.
        """
        stored = self._find(task_id)
        if approval.task_id != task_id:
            raise AgentValidationError(
                f"ApprovalRequest.task_id {approval.task_id!r} does not name task {task_id!r}"
            )
        if approval.status is ApprovalStatus.PENDING:
            raise AgentValidationError(
                f"ApprovalRequest for task {task_id!r} is unresolved; resolution is "
                f"exclusively a caller action (design spec §16)"
            )
        if stored.status is not TaskStatus.AWAITING_APPROVAL:
            raise AgentValidationError(
                f"task {task_id!r} is {stored.status.value}, not awaiting_approval; "
                f"there is no approval gate to apply a resolution to (design spec §11)"
            )

        if approval.status is ApprovalStatus.REJECTED:
            failed = stored.with_state(stored.state, status=TaskStatus.FAILED)
            self._replace(task_id, failed)
            result = AgentResult(
                task_id=task_id,
                warnings=(
                    f"approval rejected"
                    f"{f' by {approval.approver}' if approval.approver else ''}: "
                    f"{approval.requested_action}",
                ),
            )
            self._record(failed, result)
            return result

        return self._dispatch(task_id, stored, context=context)

    def _dispatch(self, task_id: str, stored: Task, *, context: AgentContext) -> AgentResult:
        """The cleared branch of §12's sequence diagram: persist
        ``Running``, retry the same agent's ``_act`` per
        ``retry_policy``, persist the terminal status, audit, and
        return the result stamped with ``task_id``."""
        try:
            agent_cls = REGISTRY.get(stored.agent_code)
        except UnregisteredLookupError as exc:
            raise TaskNotFoundError(
                f"No Agent is registered for code {stored.agent_code!r}"
            ) from exc

        running = stored.with_state(stored.state, status=TaskStatus.RUNNING)
        self._replace(task_id, running)

        agent: Agent = agent_cls()
        attempts = self._retry_policy.max_attempts
        for attempt in range(1, attempts + 1):
            try:
                result = agent._act(running, context=context)
                break
            except Exception as exc:
                recoverable = self._retry_policy.is_retryable(exc)
                if not recoverable or attempt == attempts:
                    failed = running.with_state(running.state, status=TaskStatus.FAILED)
                    self._replace(task_id, failed)
                    reason = "retries exhausted" if recoverable else "non-recoverable failure"
                    raise AgentExecutionError(
                        f"Agent {stored.agent_code!r} failed task {task_id!r} "
                        f"({reason} after {attempt} attempt(s)): {exc}"
                    ) from exc
                time.sleep(self._retry_policy.compute_delay(attempt))

        completed = running.with_state(running.state, status=TaskStatus.COMPLETED)
        self._replace(task_id, completed)
        result = result.replace(task_id=task_id)
        self._record(completed, result)
        return result

    def _record(self, task: Task, result: AgentResult) -> None:
        scope = {
            key: value for key, value in task.state.attributes.items() if isinstance(value, str)
        }
        self._audit_trail.record(
            AgentAuditEntry(
                recorded_at=datetime.now(timezone.utc),
                result=result,
                agent_code=task.agent_code,
                scope=scope,
            )
        )

    def _find(self, task_id: str) -> Task:
        maybe = self._repository.find(task_id)
        if maybe.is_nothing:
            raise TaskNotFoundError(f"No task is stored under id {task_id!r}")
        return maybe.unwrap()

    def _replace(self, task_id: str, replacement: Task) -> None:
        try:
            self._repository.remove(task_id)
            self._repository.add(replacement)
        except (NotFoundError, DuplicateError) as exc:
            raise AgentExecutionError(
                f"Concurrent execute() calls for task {task_id!r} raced past the "
                f"repository's per-id write serialization contract (design spec §32)"
            ) from exc
