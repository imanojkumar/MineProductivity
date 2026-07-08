"""Tests for mineproductivity.decision.policy."""

from __future__ import annotations

import uuid

import pytest

from mineproductivity.core import PredicateSpecification

from mineproductivity.decision.exceptions import (
    DecisionModelNotFoundError,
    DecisionValidationError,
    PolicyConflictError,
)
from mineproductivity.decision.policy import (
    DecisionStatus,
    Policy,
    policy_history,
    publish_policy,
    published_policy,
)
from mineproductivity.decision.thresholds import Threshold

_ALWAYS_TRUE = PredicateSpecification(lambda ctx: True)


def _unique_code() -> str:
    """A fresh, never-before-published Policy code -- keeps each
    publish_policy test isolated from the process-wide policy store's
    state left behind by every other test."""
    return f"TEST.Policy.{uuid.uuid4().hex}"


def _policy(**overrides: object) -> Policy:
    fields: dict[str, object] = {
        "code": "TEST.Policy",
        "rules": {"always": _ALWAYS_TRUE},
        "strategy_code": "STRATEGY.Threshold",
    }
    fields.update(overrides)
    return Policy(**fields)  # type: ignore[arg-type]


class TestDecisionStatus:
    def test_members(self) -> None:
        assert {member.value for member in DecisionStatus} == {
            "proposed",
            "active",
            "superseded",
            "retired",
        }


class TestPolicyConstruction:
    def test_minimal_valid_construction(self) -> None:
        policy = _policy()
        assert policy.code == "TEST.Policy"
        assert policy.version == "1.0.0"
        assert policy.status is DecisionStatus.PROPOSED
        assert policy.thresholds == {}

    def test_explicit_thresholds(self) -> None:
        threshold = Threshold(field="value", comparator="<", limit=0.65)
        policy = _policy(thresholds={"low_oee": threshold})
        assert policy.thresholds["low_oee"] is threshold

    def test_rules_is_frozen_into_a_read_only_mapping(self) -> None:
        policy = _policy()
        with pytest.raises(TypeError):
            policy.rules["new"] = _ALWAYS_TRUE  # type: ignore[index]

    def test_thresholds_is_frozen_into_a_read_only_mapping(self) -> None:
        policy = _policy(thresholds={"x": Threshold(field="value", comparator="<", limit=1.0)})
        with pytest.raises(TypeError):
            policy.thresholds["y"] = Threshold(field="value", comparator=">", limit=2.0)  # type: ignore[index]

    def test_strategy_code_is_a_required_keyword_field(self) -> None:
        with pytest.raises(TypeError):
            Policy(code="TEST.Policy", rules={"always": _ALWAYS_TRUE})  # type: ignore[call-arg]

    def test_rules_is_a_required_keyword_field(self) -> None:
        with pytest.raises(TypeError):
            Policy(code="TEST.Policy", strategy_code="STRATEGY.Threshold")  # type: ignore[call-arg]


class TestPolicyValidate:
    def test_valid_policy_passes(self) -> None:
        _policy()  # must not raise

    def test_empty_code_raises(self) -> None:
        with pytest.raises(DecisionValidationError, match="code must not be empty"):
            _policy(code="")

    def test_zero_rules_raises(self) -> None:
        with pytest.raises(DecisionValidationError, match="at least one rule"):
            _policy(rules={})


class TestPolicyReplace:
    def test_replace_reruns_validate(self) -> None:
        policy = _policy()
        replaced = policy.replace(version="2.0.0")
        assert replaced.version == "2.0.0"
        assert replaced.code == policy.code

    def test_replace_to_zero_rules_raises(self) -> None:
        policy = _policy()
        with pytest.raises(DecisionValidationError):
            policy.replace(rules={})


class TestPublishPolicy:
    def test_first_publication_succeeds(self) -> None:
        code = _unique_code()
        policy = _policy(code=code)
        assert publish_policy(policy) is policy
        assert published_policy(code) is policy

    def test_lookup_of_unpublished_code_returns_none(self) -> None:
        assert published_policy(_unique_code()) is None

    def test_republishing_an_identical_proposed_policy_is_allowed(self) -> None:
        code = _unique_code()
        policy = _policy(code=code)
        publish_policy(policy)
        publish_policy(policy)  # must not raise -- PROPOSED, not ACTIVE
        assert published_policy(code) is policy

    def test_changing_rules_of_an_active_policy_at_the_same_version_raises(self) -> None:
        code = _unique_code()
        active = _policy(code=code, status=DecisionStatus.ACTIVE)
        publish_policy(active)

        changed = _policy(
            code=code, status=DecisionStatus.ACTIVE, rules={"different": _ALWAYS_TRUE}
        )
        with pytest.raises(PolicyConflictError, match="requires a new version"):
            publish_policy(changed)

    def test_changing_thresholds_of_an_active_policy_at_the_same_version_raises(self) -> None:
        code = _unique_code()
        active = _policy(code=code, status=DecisionStatus.ACTIVE)
        publish_policy(active)

        changed = _policy(
            code=code,
            status=DecisionStatus.ACTIVE,
            thresholds={"x": Threshold(field="value", comparator="<", limit=1.0)},
        )
        with pytest.raises(PolicyConflictError):
            publish_policy(changed)

    def test_publishing_a_new_version_supersedes_the_prior_active_version(self) -> None:
        code = _unique_code()
        v1 = _policy(code=code, version="1.0.0", status=DecisionStatus.ACTIVE)
        publish_policy(v1)

        v2 = _policy(
            code=code,
            version="2.0.0",
            status=DecisionStatus.ACTIVE,
            rules={"different": _ALWAYS_TRUE},
        )
        publish_policy(v2)

        assert published_policy(code) is v2
        history = policy_history(code)
        assert len(history) == 1
        assert history[0].version == "1.0.0"
        assert history[0].status is DecisionStatus.SUPERSEDED

    def test_publishing_an_unchanged_new_version_does_not_raise(self) -> None:
        code = _unique_code()
        v1 = _policy(code=code, version="1.0.0", status=DecisionStatus.ACTIVE)
        publish_policy(v1)

        v2 = _policy(code=code, version="2.0.0", status=DecisionStatus.ACTIVE)
        publish_policy(v2)  # same rules/thresholds -- not a conflict
        assert published_policy(code) is v2

    def test_changing_rules_while_prior_is_not_active_does_not_raise(self) -> None:
        code = _unique_code()
        proposed = _policy(code=code, status=DecisionStatus.PROPOSED)
        publish_policy(proposed)

        changed = _policy(
            code=code, status=DecisionStatus.ACTIVE, rules={"different": _ALWAYS_TRUE}
        )
        publish_policy(changed)  # must not raise -- prior was never Active
        assert published_policy(code) is changed


class TestPublishPolicyActivationGate:
    """Design spec §12: a ``Policy`` referencing a ``strategy_code`` for
    which no ``DecisionModel`` is currently registered "fails validation
    at activation time (``DecisionModelNotFoundError``), not silently at
    first evaluation." The gate applies to *activation* only -- a
    ``Proposed`` policy may still be authored and published ahead of its
    strategy's registration."""

    def test_activating_with_an_unregistered_strategy_code_raises(self) -> None:
        policy = _policy(
            code=_unique_code(),
            status=DecisionStatus.ACTIVE,
            strategy_code="STRATEGY.NotARegisteredStrategy",
        )
        with pytest.raises(DecisionModelNotFoundError):
            publish_policy(policy)

    def test_failed_activation_publishes_nothing(self) -> None:
        code = _unique_code()
        policy = _policy(
            code=code,
            status=DecisionStatus.ACTIVE,
            strategy_code="STRATEGY.NotARegisteredStrategy",
        )
        with pytest.raises(DecisionModelNotFoundError):
            publish_policy(policy)
        assert published_policy(code) is None

    def test_proposed_policy_may_reference_a_not_yet_registered_strategy(self) -> None:
        policy = _policy(code=_unique_code(), strategy_code="STRATEGY.NotYetInstalledSitePack")
        published = publish_policy(policy)
        assert published is policy
        assert published.status is DecisionStatus.PROPOSED

    def test_activating_with_a_registered_strategy_code_succeeds(self) -> None:
        policy = _policy(code=_unique_code(), status=DecisionStatus.ACTIVE)
        assert publish_policy(policy) is policy


class TestPolicyHistory:
    def test_never_superseded_code_has_empty_history(self) -> None:
        assert policy_history(_unique_code()) == ()

    def test_republishing_an_unchanged_proposed_policy_does_not_add_history(self) -> None:
        code = _unique_code()
        policy = _policy(code=code, status=DecisionStatus.PROPOSED)
        publish_policy(policy)
        publish_policy(policy)
        assert policy_history(code) == ()

    def test_multiple_supersessions_accumulate_oldest_first(self) -> None:
        code = _unique_code()
        v1 = _policy(code=code, version="1.0.0", status=DecisionStatus.ACTIVE)
        publish_policy(v1)
        v2 = _policy(
            code=code,
            version="2.0.0",
            status=DecisionStatus.ACTIVE,
            rules={"different_a": _ALWAYS_TRUE},
        )
        publish_policy(v2)
        v3 = _policy(
            code=code,
            version="3.0.0",
            status=DecisionStatus.ACTIVE,
            rules={"different_b": _ALWAYS_TRUE},
        )
        publish_policy(v3)

        history = policy_history(code)
        assert [entry.version for entry in history] == ["1.0.0", "2.0.0"]
        assert all(entry.status is DecisionStatus.SUPERSEDED for entry in history)
        assert published_policy(code) is v3
