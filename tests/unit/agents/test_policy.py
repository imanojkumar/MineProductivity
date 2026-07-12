"""Tests for mineproductivity.agents.policy (design spec §10): the
three-outcome contract, the never-executed rule string, and the
publish/supersede governance."""

from __future__ import annotations

import uuid

import pytest

from mineproductivity.agents.capability import AgentCapabilitySet, Permission
from mineproductivity.agents.exceptions import (
    AgentValidationError,
    PermissionDeniedError,
    PolicyConflictError,
)
from mineproductivity.agents.policy import (
    AgentPolicy,
    PolicyEngine,
    PolicyStatus,
    _ApprovalRequired,
    policy_history,
    publish_policy,
    published_policy,
)
from mineproductivity.agents.state import TaskState
from mineproductivity.agents.task import Task


def _task(*required: str) -> Task:
    attributes: dict[str, object] = {"provisioned": True}
    if required:
        attributes["required_capabilities"] = required
    return Task(
        id=f"TASK-{uuid.uuid4().hex[:8]}",
        goal_code="GOAL.PolicyTest",
        agent_code="FLEET.PolicyFixture",
        state=TaskState(attributes=attributes),
    )


def _caps(*capabilities: str) -> AgentCapabilitySet:
    return AgentCapabilitySet(
        agent_code="FLEET.PolicyFixture",
        permissions=tuple(Permission(capability=c) for c in capabilities),
    )


def _policy(**overrides: object) -> AgentPolicy:
    kwargs: dict[str, object] = {
        "code": f"POLICY.Fixture{uuid.uuid4().hex[:8]}",
        "rule": "capability=approve_shutdown -> require_approval",
        "status": PolicyStatus.ACTIVE,
    }
    kwargs.update(overrides)
    return AgentPolicy(**kwargs)  # type: ignore[arg-type]


class TestPolicyStatus:
    def test_exactly_the_four_members(self) -> None:
        assert {member.value for member in PolicyStatus} == {
            "proposed",
            "active",
            "superseded",
            "retired",
        }


class TestAgentPolicyValidation:
    def test_empty_code_raises(self) -> None:
        with pytest.raises(AgentValidationError, match="code"):
            AgentPolicy(code=" ", rule="x")

    def test_empty_rule_raises(self) -> None:
        with pytest.raises(AgentValidationError, match="rule"):
            AgentPolicy(code="POLICY.X", rule="  ")

    def test_defaults(self) -> None:
        policy = AgentPolicy(code="POLICY.X", rule="x")
        assert policy.version == "1.0.0"
        assert policy.status is PolicyStatus.PROPOSED
        assert policy.requires_approval is False
        assert policy.denies is False


class TestThreeOutcomeContract:
    def test_cleared_task_proceeds(self) -> None:
        outcome = PolicyEngine().evaluate(_task(), capabilities=_caps(), policies=())
        assert outcome.is_ok
        assert outcome.value is None

    def test_missing_capability_is_denied(self) -> None:
        outcome = PolicyEngine().evaluate(
            _task("approve_shutdown"), capabilities=_caps(), policies=()
        )
        assert outcome.is_err
        assert isinstance(outcome.error, PermissionDeniedError)

    def test_denies_policy_is_denied_even_when_capability_is_held(self) -> None:
        outcome = PolicyEngine().evaluate(
            _task("approve_shutdown"),
            capabilities=_caps("approve_shutdown"),
            policies=(_policy(rule="capability=approve_shutdown -> deny", denies=True),),
        )
        assert outcome.is_err
        assert isinstance(outcome.error, PermissionDeniedError)

    def test_requires_approval_policy_routes_to_the_approval_marker(self) -> None:
        outcome = PolicyEngine().evaluate(
            _task("approve_shutdown"),
            capabilities=_caps("approve_shutdown"),
            policies=(_policy(requires_approval=True),),
        )
        assert outcome.is_err
        assert isinstance(outcome.error, _ApprovalRequired)

    def test_never_a_fourth_outcome(self) -> None:
        """Design spec §28: mechanically proven over a scripted
        matrix of capability/policy combinations."""
        engine = PolicyEngine()
        tasks = (_task(), _task("approve_shutdown"))
        capability_sets = (_caps(), _caps("approve_shutdown"))
        policy_sets: tuple[tuple[AgentPolicy, ...], ...] = (
            (),
            (_policy(requires_approval=True),),
            (_policy(rule="capability=approve_shutdown -> deny", denies=True),),
            (_policy(status=PolicyStatus.RETIRED, denies=True),),
        )
        for task in tasks:
            for capabilities in capability_sets:
                for policies in policy_sets:
                    outcome = engine.evaluate(task, capabilities=capabilities, policies=policies)
                    if outcome.is_ok:
                        assert outcome.value is None
                    else:
                        assert isinstance(outcome.error, (PermissionDeniedError, _ApprovalRequired))

    def test_denial_dominates_approval(self) -> None:
        outcome = PolicyEngine().evaluate(
            _task("approve_shutdown"),
            capabilities=_caps("approve_shutdown"),
            policies=(
                _policy(requires_approval=True),
                _policy(rule="capability=approve_shutdown -> deny", denies=True),
            ),
        )
        assert isinstance(outcome.error, PermissionDeniedError)


class TestRuleIsNeverExecuted:
    def test_non_active_policies_never_gate(self) -> None:
        for status in (PolicyStatus.PROPOSED, PolicyStatus.SUPERSEDED, PolicyStatus.RETIRED):
            outcome = PolicyEngine().evaluate(
                _task(),
                capabilities=_caps(),
                policies=(_policy(rule="always", status=status, denies=True),),
            )
            assert outcome.is_ok

    def test_capability_scoped_rule_does_not_apply_to_an_unrelated_task(self) -> None:
        outcome = PolicyEngine().evaluate(
            _task(),  # requires nothing
            capabilities=_caps(),
            policies=(_policy(rule="capability=approve_shutdown -> deny", denies=True),),
        )
        assert outcome.is_ok

    def test_rule_text_is_treated_as_data_never_evaluated(self) -> None:
        """Design spec §10: a rule carrying executable-looking text
        gates purely via its flags -- nothing is executed."""
        marker: list[str] = []
        rule = "__import__('sys') or marker.append('executed')"
        outcome = PolicyEngine().evaluate(
            _task(),
            capabilities=_caps(),
            policies=(_policy(rule=rule, requires_approval=True),),
        )
        assert marker == []
        assert isinstance(outcome.error, _ApprovalRequired)


class TestGovernance:
    def test_publish_and_lookup(self) -> None:
        policy = _policy()
        assert publish_policy(policy) is policy
        assert published_policy(policy.code) is policy
        assert published_policy(f"POLICY.NoSuch{uuid.uuid4().hex}") is None

    def test_active_policy_is_never_edited_in_place(self) -> None:
        """Design spec §10, §26, §34: a changed rule without a version
        bump is a conflict, raised at publication time."""
        code = f"POLICY.Conflict{uuid.uuid4().hex[:8]}"
        publish_policy(_policy(code=code, rule="capability=a -> deny", denies=True))
        with pytest.raises(PolicyConflictError, match="version"):
            publish_policy(_policy(code=code, rule="capability=b -> deny", denies=True))

    def test_new_version_supersedes_the_prior_active_version(self) -> None:
        code = f"POLICY.Supersede{uuid.uuid4().hex[:8]}"
        first = _policy(code=code, rule="capability=a -> deny", denies=True)
        publish_policy(first)
        second = _policy(code=code, rule="capability=b -> deny", denies=True, version="2.0.0")
        publish_policy(second)
        assert published_policy(code) is second
        history = policy_history(code)
        assert [p.version for p in history] == ["1.0.0"]
        assert history[0].status is PolicyStatus.SUPERSEDED

    def test_metadata_and_policy_versions_vary_independently(self) -> None:
        """Design spec §26: no code path derives one from the other --
        republishing a policy never touches any registered type's
        metadata version."""
        code = f"POLICY.Axis{uuid.uuid4().hex[:8]}"
        published = publish_policy(_policy(code=code, version="3.1.4"))
        assert published.version == "3.1.4"
