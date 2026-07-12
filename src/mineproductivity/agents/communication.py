"""``AgentMessage``/``DelegationRequest``: inter-agent messaging and
delegation (design spec §18).

Reuse audit: ``core.BaseValueObject`` and the
``MappingProxyType``-freezing convention reused verbatim. Transport
composes ``events.EventBus`` directly -- a message is wrapped in an
``events.EventEnvelope`` and published via ``EventBus.publish`` by the
sending side, exactly as ``digital_twin.TwinSynchronizer`` (spec 08
§11) and ``decision.RealTimeDecisionSession`` (spec 07 §25) already
compose the bus -- **no new message bus is defined here** (§18, §34).
Delegation is expressed as an ordinary ``AgentMessage`` whose
``content`` carries a ``DelegationRequest`` -- no separate
delegation-transport mechanism exists -- and the delegation chain
(which agent handed a task to which) is carried in
``Task.state.attributes`` as an open-mapping entry, never a new typed
field on ``Task`` (§18).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

__all__ = ["AgentMessage", "DelegationRequest"]


@dataclasses.dataclass(frozen=True, slots=True)
class AgentMessage(BaseValueObject):
    """A structured message exchanged between two agents, or between
    an agent and a human supervisor (design spec §18). ``content`` is
    an open ``Mapping[str, Any]``, never a closed schema, since a
    message's shape depends entirely on the sending ``Agent``'s own
    category.

    Examples
    --------
    >>> from datetime import timezone
    >>> message = AgentMessage(
    ...     from_agent_code="SHIFT_SUPERVISOR.NightShift",
    ...     to_agent_code="FLEET.ReassignmentAdvisor",
    ...     task_id="TASK-1", content={"kind": "delegation"},
    ...     sent_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    ... )
    >>> message.content["kind"]
    'delegation'
    """

    from_agent_code: str
    to_agent_code: str
    task_id: str
    content: Mapping[str, Any]
    sent_at: datetime

    def _normalize(self) -> None:
        super(AgentMessage, self)._normalize()
        object.__setattr__(self, "content", MappingProxyType(dict(self.content)))


@dataclasses.dataclass(frozen=True, slots=True)
class DelegationRequest(BaseValueObject):
    """One agent's request that another take over (or assist with) a
    ``Task``, carrying the reason for delegation for the eventual
    audit trail (design spec §18, §21).

    Examples
    --------
    >>> DelegationRequest(
    ...     task_id="TASK-1", from_agent_code="SHIFT_SUPERVISOR.NightShift",
    ...     to_agent_code="FLEET.ReassignmentAdvisor", reason="fleet expertise required",
    ... ).reason
    'fleet expertise required'
    """

    task_id: str
    from_agent_code: str
    to_agent_code: str
    reason: str
