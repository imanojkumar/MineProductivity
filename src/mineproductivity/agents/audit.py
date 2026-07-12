"""``AgentAuditTrail``/``AgentAuditEntry``: accountability for
autonomous action (design spec §21), mirroring
``decision.DecisionAuditTrail``'s pattern and rationale (spec 07 §27)
-- the accountability mechanism an autonomous-action system requires
even more urgently than a purely recommending one does.

Thread safety (design spec §32): :meth:`AgentAuditTrail.record`
serializes concurrent appends internally via one ``threading.Lock``,
so many concurrently-executing ``Task``\\ s can share one trail
instance safely; :meth:`AgentAuditTrail.query` reads a snapshot taken
under the same lock, then filters outside it, so it never blocks on a
concurrent ``record()`` beyond the snapshot itself. Every
``AgentResult``'s ``explanation`` and every ``ToolInvocation`` it
carries are preserved verbatim in the recorded entry -- an agent's
audit record is never a summary, always the full, structured outcome.
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Mapping, Sequence
from datetime import datetime
from types import MappingProxyType

from mineproductivity.core import BaseValueObject

from mineproductivity.agents.result import AgentResult

__all__ = ["AgentAuditEntry", "AgentAuditTrail"]


@dataclasses.dataclass(frozen=True, slots=True)
class AgentAuditEntry(BaseValueObject):
    """One append-only record: which agent produced which result, for
    what scope, when (design spec §21).

    Examples
    --------
    >>> from datetime import timezone
    >>> entry = AgentAuditEntry(
    ...     recorded_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    ...     result=AgentResult(task_id="TASK-1"),
    ...     agent_code="FLEET.ReassignmentAdvisor", scope={"pit": "north"},
    ... )
    >>> dict(entry.scope)
    {'pit': 'north'}
    """

    recorded_at: datetime
    result: AgentResult
    agent_code: str
    scope: Mapping[str, str]

    def _normalize(self) -> None:
        super(AgentAuditEntry, self)._normalize()
        object.__setattr__(self, "scope", MappingProxyType(dict(self.scope)))


class AgentAuditTrail:
    """Append-only record of every terminal ``AgentResult`` produced
    by any ``TaskExecutor`` run in this process (design spec §21).
    Serializes via ``core.serialization`` exactly as every other value
    object in this platform does.

    Examples
    --------
    >>> from datetime import timezone
    >>> trail = AgentAuditTrail()
    >>> trail.record(AgentAuditEntry(
    ...     recorded_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    ...     result=AgentResult(task_id="TASK-1"),
    ...     agent_code="FLEET.ReassignmentAdvisor", scope={"pit": "north"},
    ... ))
    >>> len(trail.query())
    1
    >>> len(trail.query(scope={"pit": "south"}))
    0
    """

    def __init__(self) -> None:
        self._entries: list[AgentAuditEntry] = []
        self._lock = threading.Lock()

    def record(self, entry: AgentAuditEntry) -> None:
        with self._lock:
            self._entries.append(entry)

    def query(self, *, scope: Mapping[str, str] | None = None) -> Sequence[AgentAuditEntry]:
        with self._lock:
            snapshot = tuple(self._entries)
        if scope is None:
            return snapshot
        return tuple(
            entry
            for entry in snapshot
            if all(entry.scope.get(key) == value for key, value in scope.items())
        )

    def __repr__(self) -> str:
        with self._lock:
            return f"{type(self).__name__}(entries={len(self._entries)})"
