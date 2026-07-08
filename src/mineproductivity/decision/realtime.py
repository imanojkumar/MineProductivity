"""``RealTimeDecisionSession``: a long-lived session that subscribes to
an ``events.EventBus`` and, on each new relevant envelope, refreshes the
necessary ``kpis.KPIEngine``/``analytics.BatchAnalyticsRunner`` outputs
and re-runs a ``DecisionPipeline`` over the refreshed ``DecisionContext``
(design spec §25) -- the live-operations-center counterpart of
``batch.BatchDecisionRunner`` (§26), mirroring
``analytics.StreamingAnalyticsSession``'s role one layer down (spec 06
§27).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``events.EventBus``/``Subscription`` are reused verbatim -- no new
subscription/cancellation concept is introduced; :meth:`~RealTimeDecisionSession.start`
returns the exact ``Subscription`` handle ``EventBus.subscribe()``
already returns. ``core.PredicateSpecification`` is reused as the
"match every envelope" filter ``subscribe()`` requires, exactly as
``analytics.StreamingAnalyticsSession.start()`` already does, rather
than defining a new trivial ``BaseSpecification`` subclass for a one-line
predicate. ``kpis.KPIEngine.execute()`` is reused verbatim to refresh
KPI evidence -- this module never recomputes a KPI itself.
``analytics.TimeSeries.from_kpi_results`` is reused verbatim to bridge
freshly refreshed ``KPIResult``\\ s into the ``TimeSeries``
``analytics.BatchAnalyticsRunner.run()`` requires, rather than
constructing a second, ad hoc series representation.
``decision.pipeline.DecisionPipeline.run()`` performs the actual
rule-evaluation-and-decide orchestration (including re-evaluating
``RuleEngine`` via whatever ``RuleEngineStage`` the injected pipeline
composes) -- this module composes ``KPIEngine``/``BatchAnalyticsRunner``/
``DecisionPipeline`` rather than recomputing anything itself (§3.2).

The design spec's own §25 pseudocode constructor lists ``bus``,
``pipeline``, ``kpi_engine``, ``analytics_runner`` only. Two additive,
required keyword parameters, ``kpi_codes`` and ``window``, are the
smallest necessary extension: ``KPIEngine.execute(code, *, window,
scope)`` cannot be called at all without knowing which KPI codes are
"relevant" (§25's own prose) and which window label to request -- no
information the four listed collaborators alone supply. A third,
optional ``audit_trail: DecisionAuditTrail | None = None`` parameter is
added for the identical, disclosed reason ``batch.BatchDecisionRunner``
adds one: §33's anti-pattern list forbids bypassing
``DecisionAuditTrail`` for an operationally-actionable
``DecisionPipeline`` run, and this class has no other way to honor that
rule.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from mineproductivity.analytics import BatchAnalyticsRunner, TimeSeries
from mineproductivity.core import PredicateSpecification
from mineproductivity.events import EventBus, EventEnvelope, Subscription
from mineproductivity.kpis import KPIEngine

from mineproductivity.decision.abstractions import DecisionContext
from mineproductivity.decision.audit import DecisionAuditEntry, DecisionAuditTrail
from mineproductivity.decision.pipeline import DecisionPipeline
from mineproductivity.decision.result import DecisionResult

__all__ = ["RealTimeDecisionSession"]


class RealTimeDecisionSession:
    """A long-lived session that subscribes to an ``events.EventBus``
    and, on each new relevant envelope, refreshes the necessary
    ``kpis.KPIEngine``/``analytics.BatchAnalyticsRunner`` outputs and
    re-runs a ``DecisionPipeline`` over the refreshed
    ``DecisionContext`` -- the live-operations-center counterpart of
    ``BatchDecisionRunner`` (§26), mirroring
    ``analytics.StreamingAnalyticsSession``'s role one layer down (spec
    06 §27). Composes ``KPIEngine``/``BatchAnalyticsRunner`` rather than
    recomputing anything itself (§3.2).

    **Thread safety.** Mirrors ``analytics.StreamingAnalyticsSession``:
    the Event Framework's own concurrency contract makes no guarantee
    about which thread a subscriber's handler runs on, so ``_latest`` is
    guarded by one ``threading.Lock`` shared across every scope --
    independent scopes serialize on this single lock, an intentionally
    simple posture for a per-process session object, not a
    high-throughput shared cache. Because a handler's own refresh work
    (``KPIEngine.execute``, ``BatchAnalyticsRunner.run``,
    ``DecisionPipeline.run``) happens *outside* the lock, two concurrent
    deliveries for the same scope could otherwise finish out of order and
    let an older envelope's slower handler overwrite a newer one's
    already-stored result -- caught during this phase's own QA review.
    ``_latest`` therefore stores each scope's envelope
    ``event_time_utc`` alongside its ``DecisionResult`` and only
    overwrites when the new envelope's ``event_time_utc`` is not older
    than what is already stored, reusing ``event_time_utc`` as the
    already-canonical "calculation basis" ordering signal
    (``EventEnvelope``'s own docstring, events spec 01) rather than
    inventing a second sequencing concept.

    Examples
    --------
    ``kpi_engine``/``analytics_runner`` are duck-typed fakes below,
    mirroring ``analytics.AnalyticsContext``'s own doctest precedent
    (its ``_FakeStore`` stand-in for ``event_store: EventStore[Any]``)
    -- this keeps the example focused on ``RealTimeDecisionSession``'s
    own refresh-and-decide wiring rather than a full ``KPIEngine``
    dependency graph.

    >>> from typing import ClassVar
    >>> from datetime import datetime, timezone
    >>> from mineproductivity.core import Result
    >>> from mineproductivity.decision.abstractions import DecisionModel
    >>> from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
    >>> from mineproductivity.decision.pipeline import ModelStage
    >>> from mineproductivity.events.bus import _InMemoryEventBus
    >>> from mineproductivity.events.canonical import CycleEvent
    >>> from mineproductivity.events.envelope import EventEnvelope, EventMetadata
    >>> from mineproductivity.events.identifier import EventID
    >>> from mineproductivity.events.versioning import EventVersion
    >>> from mineproductivity.kpis import KPIResult
    >>> class _Model(DecisionModel):
    ...     meta: ClassVar[DecisionMetadata] = DecisionMetadata(
    ...         code="STRATEGY.Doctest", category=DecisionCategory.STRATEGY, description="x",
    ...     )
    ...     def _decide(self, context):
    ...         return DecisionResult(model_code="TEST")
    >>> class _FakeKPIEngine:
    ...     def execute(self, code, *, window, scope):
    ...         return Result.ok(KPIResult(code=code, value=1.0, unit="t/h", scope=scope))
    >>> class _FakeAnalyticsRunner:
    ...     def run(self, series):
    ...         return Result.err("no analytics configured for this doctest")
    >>> pipeline = DecisionPipeline(stages=(ModelStage(_Model()),))
    >>> bus = _InMemoryEventBus()
    >>> session = RealTimeDecisionSession(
    ...     bus=bus, pipeline=pipeline, kpi_engine=_FakeKPIEngine(),
    ...     analytics_runner=_FakeAnalyticsRunner(), kpi_codes=("PROD.TPH",), window="shift",
    ... )
    >>> subscription = session.start()
    >>> now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    >>> envelope = EventEnvelope(
    ...     event_id=EventID.generate(), version=EventVersion(),
    ...     payload=CycleEvent(equipment_id="HT-1", shift_id="A", queue_min=1.0,
    ...                         spot_min=0.5, load_min=2.0, haul_min=8.0, dump_min=1.0,
    ...                         return_min=6.0, payload_t=220.0),
    ...     event_time_utc=now, processing_time_utc=now, ingestion_time_utc=now,
    ...     metadata=EventMetadata(name="cycle", source_system="test"),
    ... )
    >>> bus.publish(envelope)
    >>> session.latest({"equipment_id": "HT-1", "shift": "A"}).model_code
    'TEST'
    >>> subscription.cancel()
    """

    def __init__(
        self,
        *,
        bus: EventBus,
        pipeline: DecisionPipeline,
        kpi_engine: KPIEngine,
        analytics_runner: BatchAnalyticsRunner,
        kpi_codes: Sequence[str],
        window: str,
        audit_trail: DecisionAuditTrail | None = None,
    ) -> None:
        self._bus = bus
        self._pipeline = pipeline
        self._kpi_engine = kpi_engine
        self._analytics_runner = analytics_runner
        self._kpi_codes = tuple(kpi_codes)
        self._window = window
        self._audit_trail = audit_trail
        self._latest: dict[tuple[tuple[str, str], ...], tuple[datetime, DecisionResult]] = {}
        self._lock = threading.Lock()

    def start(self) -> Subscription:
        """Subscribes to ``bus``; each published ``EventEnvelope``
        refreshes evidence for its scope and re-runs ``pipeline``."""
        return self._bus.subscribe(PredicateSpecification(lambda envelope: True), self._on_envelope)

    def latest(self, scope: Mapping[str, str]) -> DecisionResult | None:
        """The most recent ``DecisionResult`` produced for ``scope``,
        served without re-running the pipeline."""
        with self._lock:
            stored = self._latest.get(self._scope_key(scope))
            return stored[1] if stored is not None else None

    def _on_envelope(self, envelope: EventEnvelope[Any]) -> None:
        scope = self._scope_for(envelope)
        kpi_results = []
        for code in self._kpi_codes:
            kpi_result = self._kpi_engine.execute(code, window=self._window, scope=scope)
            if kpi_result.is_ok:
                kpi_results.append(kpi_result.unwrap())
        timestamps = [envelope.event_time_utc] * len(kpi_results)
        series = TimeSeries.from_kpi_results(kpi_results, timestamps=timestamps)
        analytics_result = self._analytics_runner.run(series)
        analytics_results = (analytics_result.unwrap(),) if analytics_result.is_ok else ()

        context = DecisionContext(
            kpi_results=tuple(kpi_results), analytics_results=analytics_results, scope=scope
        )
        decision_result = self._pipeline.run(context)
        if not decision_result.is_ok:
            return
        outcome = decision_result.unwrap()
        key = self._scope_key(scope)
        with self._lock:
            stored = self._latest.get(key)
            if stored is None or envelope.event_time_utc >= stored[0]:
                self._latest[key] = (envelope.event_time_utc, outcome)
        if self._audit_trail is not None:
            self._audit_trail.record(
                DecisionAuditEntry(
                    recorded_at=datetime.now(timezone.utc),
                    result=outcome,
                    context_scope=scope,
                    source_event_ids=(envelope.event_id.value,),
                )
            )

    @staticmethod
    def _scope_for(envelope: EventEnvelope[Any]) -> Mapping[str, str]:
        payload = envelope.payload
        scope: dict[str, str] = {}
        equipment_id = getattr(payload, "equipment_id", None)
        if equipment_id is not None:
            scope["equipment_id"] = str(equipment_id)
        shift_id = getattr(payload, "shift_id", None)
        if shift_id is not None:
            scope["shift"] = str(shift_id)
        return scope

    @staticmethod
    def _scope_key(scope: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(scope.items()))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(kpi_codes={self._kpi_codes!r}, window={self._window!r})"
