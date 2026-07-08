"""``TwinStateCache``: avoids redundant re-assembly of a twin's
evidence inputs across closely-spaced synchronization cycles (design
spec §22).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
Confirmed **not** a reuse of ``kpis.ResultCache``, whose cache key
shape -- ``(code, window, scope, event-store-version-fingerprint)`` --
is coupled to KPI-result semantics specifically, not to the
twin-evidence-bundle shape this cache holds (design spec §22, ADR-0008:
the third application of the "shape fits, coupling doesn't" reasoning
in this series, after ``decision.ActionPlanner`` declining
``kpis.DependencyGraph``). ``events.AsOf`` is reused verbatim as the
point-in-time half of the cache key -- it is already a frozen,
hashable value object, so no new key type is introduced.

This cache holds *inputs* to a synchronization cycle (the assembled
``TwinContext`` evidence), never the *output* (``TwinState``/``Twin``
itself) -- the current ``Twin`` always lives in ``TwinRepository``
(design spec §20, §31's recorded anti-pattern), so there is exactly one
authoritative place to look for "what is the twin's current state." A
cache miss is never an error: the caller falls back to re-assembling
evidence from ``kpis.KPIEngine``/``analytics.BatchAnalyticsRunner``/
``decision.BatchDecisionRunner`` directly -- a performance
optimization, never a correctness dependency.
"""

from __future__ import annotations

import threading

from mineproductivity.events import AsOf

from mineproductivity.digital_twin.abstractions import TwinContext

__all__ = ["TwinStateCache"]


class TwinStateCache:
    """Caches the ``TwinContext`` evidence gathered for one
    ``(twin_id, as_of)`` key (design spec §22).

    **Thread safety.** Reads/writes are keyed by ``(twin_id, as_of)``;
    independent keys never contend beyond the single internal lock's
    brief critical section, and writes to the same key serialize on it
    (design spec §30) -- the same one-lock posture
    ``decision.DecisionAuditTrail`` already takes for its own narrow
    mutable surface.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> class _FakeStore: ...
    >>> cache = TwinStateCache()
    >>> as_of = AsOf(utc=datetime(2026, 7, 8, tzinfo=timezone.utc))
    >>> cache.get("CONV-7", as_of) is None
    True
    >>> context = TwinContext(event_store=_FakeStore())
    >>> cache.put("CONV-7", as_of, context)
    >>> cache.get("CONV-7", as_of) is context
    True
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, AsOf], TwinContext] = {}
        self._lock = threading.Lock()

    def get(self, twin_id: str, as_of: AsOf) -> TwinContext | None:
        """The cached ``TwinContext`` for ``(twin_id, as_of)``, or
        ``None`` -- a miss is never an error (design spec §22)."""
        with self._lock:
            return self._entries.get((twin_id, as_of))

    def put(self, twin_id: str, as_of: AsOf, context: TwinContext) -> None:
        """Store ``context`` under ``(twin_id, as_of)``, replacing any
        previously-cached evidence for the same key."""
        with self._lock:
            self._entries[(twin_id, as_of)] = context

    def __repr__(self) -> str:
        with self._lock:
            return f"{type(self).__name__}(entries={len(self._entries)})"
