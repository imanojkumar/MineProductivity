"""``AgentPolicy``/``PolicyStatus``/``PolicyEngine``: guardrails on
autonomous action (design spec §10).

Reuse audit: ``core.BaseValueObject``/``core.Result`` reused verbatim;
the publish/supersede governance mirrors
``optimization.publish_problem`` exactly (spec 10 §9), and none of the
governance functions is re-exported from the package's top-level
``__all__`` (design spec §7 names ``AgentPolicy``/``PolicyStatus``/
``PolicyEngine`` only). ``AgentPolicy`` is a deliberate **non-reuse**
of ``decision.Policy`` (spec 07 §12): the shapes look similar, but a
business-recommendation threshold and an autonomous-action guardrail
are different concerns with different failure consequences (design
spec §10, §34).

``AgentPolicy.rule`` is a solver-independent string this engine never
parses or evaluates as executable code -- the same 'expression the
platform never executes, only stores' posture
``optimization.Constraint.expression`` establishes (spec 10 §9). The
**reference evaluation strategy** implemented here interprets the rule
only as declarative data: a rule of the documented form
``"capability=<name> -> <effect>"`` applies to a task exactly when
``<name>`` appears in the task's
``state.attributes["required_capabilities"]`` entry; any other rule
form applies unconditionally. The policy's own ``denies``/
``requires_approval`` flags -- not the rule text -- are authoritative
for the effect.
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Sequence
from enum import Enum

from mineproductivity.core import BaseValueObject, MineProductivityError, Result

from mineproductivity.agents.capability import AgentCapabilitySet
from mineproductivity.agents.exceptions import (
    AgentValidationError,
    PermissionDeniedError,
    PolicyConflictError,
)
from mineproductivity.agents.task import Task

__all__ = ["AgentPolicy", "PolicyEngine", "PolicyStatus"]

_policies: dict[str, AgentPolicy] = {}
_policy_history: dict[str, list[AgentPolicy]] = {}
_lock = threading.Lock()


class PolicyStatus(Enum):
    """The ``AgentPolicy`` lifecycle -- mirrors
    ``optimization.ProblemStatus`` (spec 10 §9) exactly, applied here
    to governed autonomous-action guardrails."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


@dataclasses.dataclass(frozen=True, slots=True)
class AgentPolicy(BaseValueObject):
    """A versioned, governed guardrail on autonomous action (design
    spec §10). An ``Active`` policy is never edited in place: a
    changed policy is a new version, the prior one ``Superseded``
    (§10, §26).

    Examples
    --------
    >>> policy = AgentPolicy(
    ...     code="POLICY.ShutdownNeedsApproval",
    ...     rule="capability=approve_shutdown -> require_approval",
    ...     requires_approval=True,
    ... )
    >>> policy.status
    <PolicyStatus.PROPOSED: 'proposed'>
    """

    code: str
    version: str = dataclasses.field(default="1.0.0", kw_only=True)
    status: PolicyStatus = dataclasses.field(
        default_factory=lambda: PolicyStatus.PROPOSED, kw_only=True
    )
    rule: str = dataclasses.field(kw_only=True)
    requires_approval: bool = dataclasses.field(default=False, kw_only=True)
    denies: bool = dataclasses.field(default=False, kw_only=True)

    def validate(self) -> None:
        if not self.code.strip():
            raise AgentValidationError("AgentPolicy.code must not be empty")
        if not self.rule.strip():
            raise AgentValidationError("AgentPolicy.rule must not be empty")


class _ApprovalRequired(MineProductivityError):
    """Package-internal marker carried by the second of
    ``PolicyEngine.evaluate``'s three outcomes -- routes the ``Task``
    to ``AWAITING_APPROVAL`` (design spec §10, §11), never surfaced to
    a caller as a raised exception."""


class PolicyEngine:
    """Evaluates a ``Task`` against the currently ``Active``
    ``AgentPolicy`` set and the assigned ``Agent``'s
    ``AgentCapabilitySet`` (design spec §9) before ``TaskExecutor``
    (§12) dispatches. Returns one of exactly three outcomes, never a
    fourth (§10, §28)."""

    def evaluate(
        self, task: Task, *, capabilities: AgentCapabilitySet, policies: Sequence[AgentPolicy]
    ) -> Result[None]:
        """The three-outcome contract (design spec §10):
        ``Result.ok(None)`` (proceed), ``Result.err`` carrying the
        required-approval marker (transition to ``AWAITING_APPROVAL``),
        or ``Result.err`` carrying ``PermissionDeniedError`` (a hard
        stop). Non-``Active`` policies never gate; the caller
        assembles the candidate policy set (the executor passes every
        published policy)."""
        required = _required_capabilities(task)
        held = {permission.capability for permission in capabilities.permissions}
        missing = tuple(capability for capability in required if capability not in held)
        if missing:
            return Result.err(
                PermissionDeniedError(
                    f"Task {task.id!r} requires capabilities {missing!r} that agent "
                    f"{task.agent_code!r}'s published AgentCapabilitySet does not carry"
                )
            )

        active = [policy for policy in policies if policy.status is PolicyStatus.ACTIVE]
        applicable = [policy for policy in active if _applies(policy, required)]
        for policy in applicable:
            if policy.denies:
                return Result.err(
                    PermissionDeniedError(
                        f"AgentPolicy {policy.code!r} denies task {task.id!r} outright"
                    )
                )
        for policy in applicable:
            if policy.requires_approval:
                return Result.err(
                    _ApprovalRequired(
                        f"AgentPolicy {policy.code!r} requires human approval for task {task.id!r}"
                    )
                )
        return Result.ok(None)

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


def _required_capabilities(task: Task) -> tuple[str, ...]:
    """The reference evaluation strategy's read of which capabilities
    a task requires: the open-mapping entry
    ``state.attributes["required_capabilities"]`` (design spec §11's
    escape hatch), absent meaning none."""
    raw = task.state.attributes.get("required_capabilities", ())
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, Sequence):
        return tuple(str(item) for item in raw)
    return ()


def _applies(policy: AgentPolicy, required: tuple[str, ...]) -> bool:
    """Whether ``policy`` applies to a task requiring ``required`` --
    declarative-data interpretation only, never execution (design spec
    §10): a ``"capability=<name> ..."`` rule applies when ``<name>``
    is required; any other rule form applies unconditionally."""
    rule = policy.rule.strip()
    if rule.startswith("capability="):
        name = rule[len("capability=") :].split("->", 1)[0].strip()
        return name in required
    return True


def publish_policy(policy: AgentPolicy) -> AgentPolicy:
    """Publish ``policy`` into the process-wide policy store, keyed by
    ``policy.code`` (design spec §10, §26).

    Raises
    ------
    PolicyConflictError
        If an ``Active`` policy is already published under
        ``policy.code`` and ``policy`` changes its rule without a
        version bump -- raised at publication time, never deferred.
    """
    with _lock:
        existing = _policies.get(policy.code)
        if existing is not None and existing.status is PolicyStatus.ACTIVE:
            changed = existing.rule != policy.rule
            if changed and policy.version == existing.version:
                raise PolicyConflictError(
                    f"AgentPolicy {policy.code!r} is Active at version "
                    f"{existing.version!r}; changing its rule requires a new "
                    f"version, not re-publication"
                )
            if changed and policy.status is PolicyStatus.ACTIVE:
                superseded = existing.replace(status=PolicyStatus.SUPERSEDED)
                _policy_history.setdefault(policy.code, []).append(superseded)
        _policies[policy.code] = policy
        return policy


def published_policy(code: str) -> AgentPolicy | None:
    """Non-raising lookup of the currently-published policy for
    ``code``, or ``None``."""
    with _lock:
        return _policies.get(code)


def published_policies() -> tuple[AgentPolicy, ...]:
    """Every currently-published policy -- the candidate set
    ``TaskExecutor`` (design spec §12) hands to
    :meth:`PolicyEngine.evaluate`, which filters to ``Active``
    itself."""
    with _lock:
        return tuple(_policies.values())


def policy_history(code: str) -> tuple[AgentPolicy, ...]:
    """Every prior version of ``code`` transitioned to ``Superseded``,
    oldest first."""
    with _lock:
        return tuple(_policy_history.get(code, ()))
