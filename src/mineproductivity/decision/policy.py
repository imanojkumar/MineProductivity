"""Business policies as versioned, governed artifacts (design spec §12).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseValueObject`` is reused verbatim as ``Policy``'s base, and
its ``MappingProxyType``-freezing convention (for ``rules``/
``thresholds``) is reused exactly as ``decision.result`` already
established in Phase 07.1 -- no new value-object base or mapping-
freezing mechanism is introduced.

``registry.Registry.register()`` was considered and rejected for
publishing/versioning ``Policy`` objects: it is deliberately,
unconditionally add-only (design spec AD-RG-04) -- rejecting *any*
re-registration under an existing key, identical or not. A ``Policy``'s
own lifecycle (§12, §29) requires the opposite: allowing a **new**
version of an **existing** code, gated on the prior ``Active`` version
transitioning to ``Superseded``. Reusing ``Registry.register()`` here
would mean fighting its own core invariant rather than reusing it, the
same reasoning ADR-0007 already recorded for why ``ActionPlanner``
does not reuse ``kpis.DependencyGraph``. A small, purpose-built,
version-aware publish function is therefore genuinely necessary --
implemented below as ``publish_policy``, using a private module-level
store (not ``registry.Registry``, since that class's add-only
contract cannot express this update-permitting semantics without being
bypassed).

``publish_policy`` is deliberately **not** re-exported from
``mineproductivity.decision``'s top-level ``__all__``: design spec §7's
public API list names ``Policy``/``DecisionStatus`` for this module,
but no publish/registration function -- the governance *behavior* is
specified in prose (§12, §29), not as a named public callable. Keeping
it as an internal, directly-importable module function (mirroring how
``analytics.statistics._mean`` is directly imported by that package's
own tests without being top-level public API) satisfies the behavioral
requirement without expanding the public surface beyond what design
spec §7 actually lists.
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType

from mineproductivity.core import BaseValueObject

from mineproductivity.decision._registry import REGISTRY
from mineproductivity.decision.exceptions import (
    DecisionModelNotFoundError,
    DecisionValidationError,
    PolicyConflictError,
)
from mineproductivity.decision.rules import Rule
from mineproductivity.decision.thresholds import Threshold

__all__ = ["DecisionStatus", "Policy"]

_policies: dict[str, Policy] = {}
_policy_history: dict[str, list[Policy]] = {}
_lock = threading.Lock()


class DecisionStatus(Enum):
    """The ``Policy`` lifecycle -- mirrors ``kpis.KPIStatus`` exactly,
    applied here to governed business artifacts rather than to
    individual computed results."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


@dataclasses.dataclass(frozen=True, slots=True)
class Policy(BaseValueObject):
    """A named, versioned bundle of :data:`~mineproductivity.decision.rules.Rule`\\ s,
    the :class:`~mineproductivity.decision.thresholds.Threshold`\\ s they
    reference, and which ``DecisionStrategy``/category they activate --
    the business-policy equivalent of ``kpis.KPIMetadata``'s governance
    weight.

    Examples
    --------
    >>> from mineproductivity.core import PredicateSpecification
    >>> policy = Policy(
    ...     code="AVAIL.LowFleetAvailability",
    ...     rules={"low_oee": PredicateSpecification(lambda ctx: True)},
    ...     strategy_code="STRATEGY.Threshold",
    ... )
    >>> policy.status
    <DecisionStatus.PROPOSED: 'proposed'>
    >>> policy.version
    '1.0.0'
    """

    code: str
    version: str = dataclasses.field(default="1.0.0", kw_only=True)
    status: DecisionStatus = dataclasses.field(
        default_factory=lambda: DecisionStatus.PROPOSED, kw_only=True
    )
    rules: Mapping[str, Rule] = dataclasses.field(kw_only=True)
    thresholds: Mapping[str, Threshold] = dataclasses.field(default_factory=dict, kw_only=True)
    strategy_code: str = dataclasses.field(kw_only=True)

    def _normalize(self) -> None:
        super(Policy, self)._normalize()
        object.__setattr__(self, "rules", MappingProxyType(dict(self.rules)))
        object.__setattr__(self, "thresholds", MappingProxyType(dict(self.thresholds)))

    def validate(self) -> None:
        if not self.code.strip():
            raise DecisionValidationError("Policy.code must not be empty")
        if not self.rules:
            raise DecisionValidationError(f"{self.code}: a Policy must declare at least one rule")


def publish_policy(policy: Policy) -> Policy:
    """Publish ``policy`` into the process-wide policy store, keyed by
    ``policy.code``.

    An ``Active`` policy is a public contract exactly as a KPI code is
    (design spec §12, §29): it is never edited in place. Publishing a
    same-version replacement whose ``rules``/``thresholds`` differ from
    the currently ``Active`` version raises :class:`PolicyConflictError`.
    Publishing a *new*, ``Active`` version correctly transitions the
    prior ``Active`` version to ``Superseded`` -- recorded in
    :func:`policy_history`, not merely computed and discarded -- so a
    caller never has to remember to do so as a second step.

    **Known limitation.** "Changed" is decided by ``Policy.rules !=``,
    which bottoms out at ``core.PredicateSpecification``'s dataclass-
    generated equality -- itself comparing the wrapped ``predicate``
    callable by ordinary Python equality. Two ``lambda``\\ s with
    identical bodies are never equal unless they are the same object,
    so a caller that reconstructs an unchanged ``Policy`` from source
    (e.g. on process restart, with fresh ``lambda`` literals) will see
    ``changed=True`` even though nothing semantically changed, and must
    bump the version to republish. This is an inherent consequence of
    reusing ``core.BaseSpecification``/``PredicateSpecification``
    verbatim (design spec §10, §11's own "no bespoke rule language"
    mandate) rather than a defect in this function -- solving it would
    require either a rule equality/hashing scheme keyed by predicate
    *source* (well beyond this phase's scope) or modifying the locked
    ``core.specification`` module, neither of which this phase attempts.

    Raises
    ------
    PolicyConflictError
        If an ``Active`` policy is already published under ``policy.code``
        and ``policy`` changes its ``rules``/``thresholds`` without a
        version bump.
    DecisionModelNotFoundError
        If ``policy`` is being published as ``Active`` while its
        ``strategy_code`` names no currently-registered ``DecisionModel``
        -- design spec §12's own rule: such a policy "fails validation
        at activation time..., not silently at first evaluation." A
        ``Proposed`` policy may still be published ahead of its
        strategy's registration (e.g. authored before a site pack is
        installed); the check gates *activation*, the moment the policy
        becomes an operational contract.
    """
    if policy.status is DecisionStatus.ACTIVE and policy.strategy_code not in REGISTRY:
        raise DecisionModelNotFoundError(
            f"Policy {policy.code!r} cannot be activated: strategy_code "
            f"{policy.strategy_code!r} names no registered DecisionModel"
        )
    with _lock:
        existing = _policies.get(policy.code)
        if existing is not None and existing.status is DecisionStatus.ACTIVE:
            changed = existing.rules != policy.rules or existing.thresholds != policy.thresholds
            if changed and policy.version == existing.version:
                raise PolicyConflictError(
                    f"Policy {policy.code!r} is Active at version {existing.version!r}; "
                    f"changing its rules/thresholds requires a new version, not re-publication"
                )
            if changed and policy.status is DecisionStatus.ACTIVE:
                superseded = existing.replace(status=DecisionStatus.SUPERSEDED)
                _policy_history.setdefault(policy.code, []).append(superseded)
        _policies[policy.code] = policy
        return policy


def published_policy(code: str) -> Policy | None:
    """Non-raising lookup of the currently-published ``Policy`` for
    ``code``, or ``None`` if none has been published."""
    with _lock:
        return _policies.get(code)


def policy_history(code: str) -> tuple[Policy, ...]:
    """Every prior version of ``code`` that :func:`publish_policy` has
    transitioned to ``Superseded``, oldest first. Empty if ``code`` has
    never been superseded."""
    with _lock:
        return tuple(_policy_history.get(code, ()))
