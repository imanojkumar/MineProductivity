"""``DecisionAuditTrail``: the append-only accountability record of
every ``DecisionResult`` ever produced by a ``DecisionPipeline`` run in
this process (design spec §27/§28).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseValueObject`` and the ``MappingProxyType``-freezing
convention for ``Mapping``-typed fields are reused verbatim for
``DecisionAuditEntry``, exactly as every other value object in this
package already does -- no new value-object base is introduced.
``DecisionResult`` (and every concrete subclass) already serializes via
``core.serialization`` with no bespoke per-type serializer (§28's own
"Serialization" note), which is what lets ``DecisionAuditEntry`` persist
any decision output uniformly without this module needing its own
per-result-type handling.

Thread safety, mirroring ``analytics.IncrementalAccumulator`` (spec 06
§29) exactly as §27's own "Thread safety" note requires: :meth:`~DecisionAuditTrail.record`
serializes concurrent appends internally via one ``threading.Lock``, so
``RealTimeDecisionSession`` (§25) and ``BatchDecisionRunner`` (§26) can
share one trail instance safely; :meth:`~DecisionAuditTrail.query` reads
a snapshot taken under the same lock, then filters outside it, so it
never blocks on a concurrent :meth:`~DecisionAuditTrail.record` call
beyond the snapshot itself.

Performance note (disclosed, not literally met): design spec §35 states
``query()`` "is expected to support scope-based filtering without a
full linear scan at production audit-trail sizes." This reference
implementation performs a linear scan over the current snapshot on
every call -- the same "do not assume small-N forever" aspiration spec
06 §36 already discloses for its own accumulators without requiring an
index in the reference implementation. A future phase may introduce a
scope-indexed structure (e.g. a ``Mapping[tuple[str, str], list[int]]``
posting list) without any change to this class's public API.
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Mapping, Sequence
from datetime import datetime
from types import MappingProxyType

from mineproductivity.core import BaseValueObject

from mineproductivity.decision.result import DecisionResult

__all__ = ["DecisionAuditEntry", "DecisionAuditTrail"]


@dataclasses.dataclass(frozen=True, slots=True)
class DecisionAuditEntry(BaseValueObject):
    """One append-only record: what was decided, for what scope, when,
    and (where traceable) from which raw events.

    ``source_event_ids`` is populated on a best-effort basis (§27's own
    "What 'traceable' means in practice" note) -- an empty tuple is not
    an error; ``result``, ``context_scope``, and ``recorded_at`` alone
    already satisfy this package's accountability objective.

    Examples
    --------
    >>> from datetime import timezone
    >>> from mineproductivity.decision.result import DecisionResult
    >>> entry = DecisionAuditEntry(
    ...     recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ...     result=DecisionResult(model_code="STRATEGY.Threshold"),
    ...     context_scope={"pit": "north"}, source_event_ids=(),
    ... )
    >>> dict(entry.context_scope)
    {'pit': 'north'}
    """

    recorded_at: datetime
    result: DecisionResult
    context_scope: Mapping[str, str]
    source_event_ids: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)

    def _normalize(self) -> None:
        super(DecisionAuditEntry, self)._normalize()
        object.__setattr__(self, "context_scope", MappingProxyType(dict(self.context_scope)))


class DecisionAuditTrail:
    """Append-only record of every ``DecisionResult`` ever produced by
    any ``DecisionPipeline`` run in this process -- the accountability
    mechanism a business-decision system requires that a purely
    statistical one (``analytics``) does not as urgently. Serializes via
    ``core.serialization`` exactly as every other value object in this
    platform does.

    Examples
    --------
    >>> from datetime import timezone
    >>> from mineproductivity.decision.result import DecisionResult
    >>> trail = DecisionAuditTrail()
    >>> trail.record(DecisionAuditEntry(
    ...     recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ...     result=DecisionResult(model_code="STRATEGY.Threshold"),
    ...     context_scope={"pit": "north"}, source_event_ids=(),
    ... ))
    >>> len(trail.query())
    1
    >>> len(trail.query(scope={"pit": "south"}))
    0
    """

    def __init__(self) -> None:
        self._entries: list[DecisionAuditEntry] = []
        self._lock = threading.Lock()

    def record(self, entry: DecisionAuditEntry) -> None:
        with self._lock:
            self._entries.append(entry)

    def query(self, *, scope: Mapping[str, str] | None = None) -> Sequence[DecisionAuditEntry]:
        with self._lock:
            snapshot = tuple(self._entries)
        if scope is None:
            return snapshot
        return tuple(
            entry
            for entry in snapshot
            if all(entry.context_scope.get(key) == value for key, value in scope.items())
        )

    def __repr__(self) -> str:
        with self._lock:
            return f"{type(self).__name__}(entries={len(self._entries)})"
