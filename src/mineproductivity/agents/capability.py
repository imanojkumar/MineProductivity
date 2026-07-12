"""``Permission``/``AgentCapabilitySet``: authorization for autonomous
action (design spec §9).

Reuse audit: ``core.BaseValueObject`` and the
``MappingProxyType``-freezing convention reused verbatim; ``scope``
carries the same ontology-expressed vocabulary (equipment, pit, shift)
``digital_twin.Twin.scope`` already carries (spec 08 §9), held as
plain strings per Documentation Governance Rule #005. Genuinely new to
this series: no package below ``agents`` models authorization, since
none of them acts autonomously in the first place.

Governance: an ``AgentCapabilitySet`` is always an explicit, authored,
and governed artifact -- never inferred from an ``Agent`` subclass's
own code at runtime (design spec §9). :func:`publish_capabilities`/
:func:`published_capabilities` mirror ``optimization.publish_problem``'s
process-wide governed store, keyed by ``agent_code``; neither is
re-exported from the package's top-level ``__all__`` (design spec §7
names ``Permission``/``AgentCapabilitySet`` only).
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Mapping
from types import MappingProxyType

from mineproductivity.core import BaseValueObject

__all__ = ["AgentCapabilitySet", "Permission"]

_capabilities: dict[str, AgentCapabilitySet] = {}
_lock = threading.Lock()


@dataclasses.dataclass(frozen=True, slots=True)
class Permission(BaseValueObject):
    """One capability a registered ``Agent`` is authorized to
    exercise, scoped the same way ``digital_twin.Twin.scope`` already
    is (design spec §9).

    Examples
    --------
    >>> Permission(capability="approve_shutdown", scope={"pit": "north"}).capability
    'approve_shutdown'
    """

    capability: str
    scope: Mapping[str, str] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        super(Permission, self)._normalize()
        object.__setattr__(self, "scope", MappingProxyType(dict(self.scope)))


@dataclasses.dataclass(frozen=True, slots=True)
class AgentCapabilitySet(BaseValueObject):
    """The full set of ``Permission``\\ s a registered ``Agent`` type
    carries -- authored and governed, never inferred from an agent's
    own code (design spec §9).

    Examples
    --------
    >>> caps = AgentCapabilitySet(
    ...     agent_code="FLEET.ReassignmentAdvisor",
    ...     permissions=(Permission(capability="reassign_truck"),),
    ... )
    >>> caps.permissions[0].capability
    'reassign_truck'
    """

    agent_code: str
    permissions: tuple[Permission, ...]


def publish_capabilities(capabilities: AgentCapabilitySet) -> AgentCapabilitySet:
    """Publish ``capabilities`` into the process-wide governed store,
    keyed by ``capabilities.agent_code`` (design spec §9, §31) -- the
    explicit authoring step that makes a capability grant a
    reviewable artifact."""
    with _lock:
        _capabilities[capabilities.agent_code] = capabilities
        return capabilities


def published_capabilities(agent_code: str) -> AgentCapabilitySet | None:
    """Non-raising lookup of the currently-published capability set
    for ``agent_code``, or ``None`` -- an agent with no published set
    holds no permissions at all."""
    with _lock:
        return _capabilities.get(agent_code)
