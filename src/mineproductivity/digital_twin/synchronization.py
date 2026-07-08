"""``TwinSynchronizer``/``SyncPolicy``: the general synchronization
mechanism (design spec §11) and its event-integration elaboration
(§15).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``events.EventBus.subscribe``/``EventStore.replay``/``EventStore.query``
are reused verbatim for live, cold-start, and scheduled-pull
synchronization respectively (design spec §15) -- nothing here
reimplements event querying, filtering, or subscription;
``SyncPolicy.event_filter`` is a plain ``events.EventFilter``
(``= core.BaseSpecification[EventEnvelope[Any]]``), composed with
``&``/``|``/``~`` exactly as ``decision.RuleEngine`` already composes
rules. The "current pointer for this id" swap lives in
``TwinRepository`` (§20) via its own ``remove``/``add`` contract --
this module concentrates no mutation of its own beyond a small,
lock-guarded consecutive-failure counter backing §10's
``Degraded``-on-repeated-failures transition, mirroring how
``registry.Registry``, ``analytics.IncrementalAccumulator``, and
``decision.DecisionAuditTrail`` each concentrate their one mutable
operation in a single, narrow place.

``SyncPolicy`` is deliberately NOT a ``decision.Policy`` (spec 07 §12)
-- it governs *when and how a twin's state is refreshed*, an
operational/deployment-config concern, not a versioned business
rule/threshold artifact (design spec §11, §31).
"""

from __future__ import annotations

import threading
from collections.abc import Sequence
from datetime import timedelta
from typing import Literal

from mineproductivity.core import DuplicateError, NotFoundError
from mineproductivity.events import BaseEvent, EventFilter

from mineproductivity.digital_twin.abstractions import Twin, TwinContext
from mineproductivity.digital_twin.caching import TwinStateCache
from mineproductivity.digital_twin.exceptions import (
    TwinNotFoundError,
    TwinStateConflictError,
    TwinSyncError,
)
from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.persistence import TwinRepository
from mineproductivity.digital_twin.result import SyncResult

__all__ = ["SyncPolicy", "TwinSynchronizer"]

#: Consecutive ``_apply`` failures for one twin id after which the twin
#: is marked ``Degraded`` (design spec §10's "repeated _apply()
#: failures" transition). The spec prescribes "repeated," not a number;
#: two-in-a-row is the smallest reading of "repeated," fixed and
#: disclosed here rather than made a constructor knob nothing yet needs.
_DEGRADED_AFTER_CONSECUTIVE_FAILURES = 2


class SyncPolicy:
    """Declares how a ``Twin`` should be kept current: real-time
    (subscribe to ``EventBus``) vs. scheduled-pull (periodic
    ``EventStore.query``), and the ``EventFilter`` selecting which
    events matter to this twin (design spec §11). The filter is
    expected to narrow delivery to only the event types a given twin
    category's ``_apply`` actually reads -- never a blanket
    "every event" subscription (§33).

    Examples
    --------
    >>> from mineproductivity.core import PredicateSpecification
    >>> policy = SyncPolicy(
    ...     mode="realtime",
    ...     event_filter=PredicateSpecification(lambda envelope: True),
    ... )
    >>> policy.mode
    'realtime'
    >>> policy.poll_interval is None
    True
    """

    def __init__(
        self,
        *,
        mode: Literal["realtime", "scheduled"],
        event_filter: EventFilter,
        poll_interval: timedelta | None = None,
    ) -> None:
        self.mode = mode
        self.event_filter = event_filter
        self.poll_interval = poll_interval

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(mode={self.mode!r}, "
            f"event_filter={self.event_filter!r}, poll_interval={self.poll_interval!r})"
        )


class TwinSynchronizer:
    """Orchestrates one ``Twin``'s update: fetches the current instance
    from a ``TwinRepository``, folds new events through ``Twin._apply``,
    writes the resulting new instance back (the per-id swap and its
    concurrency contract live in the repository, design spec §29), and
    returns a ``SyncResult`` -- the digital-twin-layer counterpart of
    ``decision.RealTimeDecisionSession``/``analytics.StreamingAnalyticsSession``'s
    orchestration role (spec 07 §25, spec 06 §27), one layer up.

    :meth:`synchronize` never mutates the ``Twin`` instance it reads --
    it computes a replacement via ``with_state()`` and hands that
    replacement to the repository (§11). The optional ``cache`` stores
    the *evidence inputs* (``TwinContext``) per ``(twin_id, as_of)`` so
    closely-spaced cycles can skip re-assembly; it is never treated as
    authoritative for the twin's current state -- only the repository
    is (§22, §31).
    """

    def __init__(self, *, repository: TwinRepository, cache: TwinStateCache | None = None) -> None:
        self._repository = repository
        self._cache = cache
        self._consecutive_failures: dict[str, int] = {}
        self._failures_lock = threading.Lock()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(repository={self._repository!r}, cache={self._cache!r})"

    def synchronize(
        self, twin_id: str, events: Sequence[BaseEvent], *, context: TwinContext
    ) -> SyncResult:
        """Fold ``events`` into the twin stored under ``twin_id``.

        A legitimately-empty ``events`` batch, or a batch whose fold
        leaves the state value-unchanged, returns a warning-carrying
        ``SyncResult`` -- never raises (design spec §24). A retired
        twin is never folded further: ``Retired`` is terminal (§10).

        Raises
        ------
        TwinNotFoundError
            If no twin is stored under ``twin_id``.
        TwinSyncError
            If ``_apply`` raised for a batch that should have been
            structurally valid. After
            ``_DEGRADED_AFTER_CONSECUTIVE_FAILURES`` consecutive
            failures for the same id, the stored twin is additionally
            marked ``Degraded`` (§10) before raising.
        TwinStateConflictError
            If the repository's per-id write serialization contract
            (design spec §29) was violated by a concurrent writer
            mid-swap -- never under normal operation.
        """
        maybe_twin = self._repository.find(twin_id)
        if maybe_twin.is_nothing:
            raise TwinNotFoundError(f"No twin is stored under id {twin_id!r}")
        twin = maybe_twin.unwrap()

        if twin.status is TwinStatus.RETIRED:
            return SyncResult(
                twin_id=twin_id,
                warnings=("twin is retired; synchronization skipped (Retired is terminal)",),
                previous_status=TwinStatus.RETIRED,
                new_status=TwinStatus.RETIRED,
                events_applied=0,
            )

        if not events:
            return SyncResult(
                twin_id=twin_id,
                warnings=("no events to apply; state unchanged",),
                previous_status=twin.status,
                new_status=twin.status,
                events_applied=0,
            )

        try:
            next_state = twin._apply(events, context=context)
        except Exception as exc:
            degraded = self._record_failure(twin_id)
            if degraded:
                self._replace(twin_id, twin.with_state(twin.state, status=TwinStatus.DEGRADED))
            raise TwinSyncError(
                f"Twin {twin_id!r}._apply raised for a structurally-valid batch of "
                f"{len(events)} event(s): {exc}"
            ) from exc

        self._clear_failures(twin_id)
        warnings: tuple[str, ...] = ()
        if next_state == twin.state:
            warnings = ("events applied left the state value-unchanged",)

        replacement = twin.with_state(next_state, status=TwinStatus.SYNCHRONIZED)
        self._replace(twin_id, replacement)

        if self._cache is not None and context.as_of is not None:
            self._cache.put(twin_id, context.as_of, context)

        return SyncResult(
            twin_id=twin_id,
            warnings=warnings,
            previous_status=twin.status,
            new_status=TwinStatus.SYNCHRONIZED,
            events_applied=len(events),
        )

    def _replace(self, twin_id: str, replacement: Twin) -> None:
        """The repository-mediated "current pointer" swap (design spec
        §11, §29): ``remove`` then ``add`` under ``BaseRepository``'s
        own contract. A ``NotFoundError``/``DuplicateError`` here --
        after the twin was already found -- means a concurrent writer
        raced past the repository's per-id serialization contract."""
        try:
            self._repository.remove(twin_id)
            self._repository.add(replacement)
        except (NotFoundError, DuplicateError) as exc:
            raise TwinStateConflictError(
                f"Concurrent synchronize() calls for twin {twin_id!r} raced past the "
                f"repository's per-id write serialization contract (design spec §29)"
            ) from exc

    def _record_failure(self, twin_id: str) -> bool:
        """Record one ``_apply`` failure; ``True`` once failures for
        ``twin_id`` reach the disclosed 'repeated' threshold (§10)."""
        with self._failures_lock:
            count = self._consecutive_failures.get(twin_id, 0) + 1
            self._consecutive_failures[twin_id] = count
            return count >= _DEGRADED_AFTER_CONSECUTIVE_FAILURES

    def _clear_failures(self, twin_id: str) -> None:
        with self._failures_lock:
            self._consecutive_failures.pop(twin_id, None)
