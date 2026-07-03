"""``KPIEngine``: orchestration only -- holds no metric logic (design
spec AD-KP-01).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from typing import Any

from mineproductivity.core import Result, to_dict
from mineproductivity.events import EventQuery, EventStore
from mineproductivity.ontology import Shift
from mineproductivity.registry import Registry

from mineproductivity.kpis.backends.base_backend import ExecutionBackend
from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.caching import ResultCache
from mineproductivity.kpis.composite import CompositeKPI
from mineproductivity.kpis.dependency_graph import DependencyGraph
from mineproductivity.kpis.exceptions import KPICircularDependencyError
from mineproductivity.kpis.result import KPIResult

__all__ = ["KPIEngine"]

#: Per event_type_code, the semantic alias a leaf KPI's own ``_compute``
#: reads (matching the design spec's own ``TonnesPerHour`` worked
#: example's literal ``"operating_h"`` row key) -- the generic
#: ``duration_h`` key (from ``BaseEvent.duration_h()``) is always present
#: too, for KPIs that don't care about the event-type-specific alias.
_DURATION_ALIAS_BY_EVENT_TYPE: Mapping[str, str] = {
    "CYCLE": "operating_h",
    "DELAY": "delay_h",
}


class KPIEngine:
    """Orchestration ONLY -- holds no metric-specific logic (design spec
    §3.2, AD-KP-01). Resolves a requested KPI's dependency graph,
    assembles exactly the rows each node needs, executes leaves before
    composites, and returns the final :class:`KPIResult`.

    ``shifts`` is an optional, injectable lookup of known
    :class:`~mineproductivity.ontology.Shift` instances -- when
    ``scope["shift"]`` names a known shift, its
    ``start_utc``/``end_utc`` resolve the query window directly (a
    genuine integration with ``ontology``, not a placeholder). Without a
    matching shift, ``scope["since"]``/``scope["until"]`` (ISO-8601
    strings) are used as a direct escape hatch; resolving a
    ``"day"``/``"week"``/``"month"`` window label against a site's
    calendar is Future Work (this reference engine's ``ontology``
    integration is scoped to shift-level resolution for v0.7.0).
    """

    def __init__(
        self,
        store: EventStore[Any],
        registry: Registry[str, type[BaseKPI]],
        backend: ExecutionBackend,
        cache: ResultCache,
        *,
        shifts: Mapping[str, Shift] | None = None,
    ) -> None:
        self._store = store
        self._registry = registry
        self._backend = backend
        self._cache = cache
        self._shifts = shifts if shifts is not None else {}
        self._graph = DependencyGraph(registry)

    def execute(self, code: str, *, window: str, scope: Mapping[str, str]) -> Result[KPIResult]:
        """The ``.by(grouping)`` execution path (Cookbook Part I, Ch. 4)."""
        try:
            order = self._graph.topological_order(code)
        except KPICircularDependencyError as exc:
            return Result.err(exc)

        computed: dict[str, KPIResult] = {}
        for step_code in order:
            computed[step_code] = self._execute_step(step_code, computed, window, scope)
        return Result.ok(computed[code])

    def summary(
        self, codes: Sequence[str], *, window: str, scope: Mapping[str, str]
    ) -> Result[Mapping[str, KPIResult]]:
        """Batched multi-KPI execution (the ``mine.summary(...)``
        equivalent): scans the event store once per distinct
        ``required_events`` set shared across the requested KPIs and
        their transitive dependencies, rather than once per KPI (design
        spec §22)."""
        all_steps: list[str] = []
        seen: set[str] = set()
        for code in codes:
            try:
                order = self._graph.topological_order(code)
            except KPICircularDependencyError as exc:
                return Result.err(exc)
            for step_code in order:
                if step_code not in seen:
                    seen.add(step_code)
                    all_steps.append(step_code)

        computed: dict[str, KPIResult] = {}
        rows_by_required_events: dict[tuple[str, ...], tuple[Sequence[Mapping[str, Any]], int]] = {}
        for step_code in all_steps:
            computed[step_code] = self._execute_step(
                step_code, computed, window, scope, rows_by_required_events=rows_by_required_events
            )
        return Result.ok({code: computed[code] for code in codes})

    def rows_for(
        self, kpi: BaseKPI, window: str, scope: Mapping[str, str]
    ) -> tuple[Sequence[Mapping[str, Any]], int]:
        """Assembles exactly the rows ``kpi`` needs: an :class:`EventQuery`
        scoped to ``kpi.meta.required_events`` and the window/scope, with
        every envelope flattened into a row dict and round-tripped
        through the active :class:`~mineproductivity.kpis.backends.base_backend.ExecutionBackend`
        (``assemble`` then ``to_rows``) -- this is the mechanical proof
        that ``BaseKPI._compute`` implementations are truly
        backend-independent (design spec §29's backend parity tests):
        swapping the backend never changes the row *data*, only how it
        was vectorized in transit.

        Returns ``(rows, fingerprint)`` -- ``fingerprint`` is the
        matching envelope count, the cheap "has anything changed" proxy
        :class:`~mineproductivity.kpis.caching.ResultCache` keys on
        (design spec §22).
        """
        query = self._build_query(kpi, window, scope)
        envelopes = list(self._store.query(query))
        scheduled_h = self._resolve_scheduled_h(scope)
        raw_rows = [
            self._flatten(envelope.payload, scheduled_h=scheduled_h) for envelope in envelopes
        ]
        if not raw_rows:
            return raw_rows, 0
        # The union of keys across all rows, not just the first row's --
        # required_events may name more than one event type, and
        # different event types flatten to different field sets.
        columns = tuple(dict.fromkeys(key for row in raw_rows for key in row))
        table = self._backend.assemble(raw_rows, columns)
        rows = self._backend.to_rows(table)
        return rows, len(envelopes)

    def _execute_step(
        self,
        step_code: str,
        computed: Mapping[str, KPIResult],
        window: str,
        scope: Mapping[str, str],
        *,
        rows_by_required_events: dict[tuple[str, ...], tuple[Sequence[Mapping[str, Any]], int]]
        | None = None,
    ) -> KPIResult:
        kpi_cls = self._registry.get(step_code)
        kpi = kpi_cls()
        if isinstance(kpi, CompositeKPI):
            dependency_results = {
                dependency: computed[dependency] for dependency in kpi.meta.dependencies
            }
            return kpi.combine(dependency_results)

        if rows_by_required_events is not None:
            key = kpi.meta.required_events
            if key not in rows_by_required_events:
                rows_by_required_events[key] = self.rows_for(kpi, window, scope)
            rows, fingerprint = rows_by_required_events[key]
        else:
            rows, fingerprint = self.rows_for(kpi, window, scope)

        return self._cache.get_or_compute(
            step_code, window, scope, fingerprint, self._compute_closure(kpi, rows, window)
        )

    @staticmethod
    def _compute_closure(
        kpi: BaseKPI, rows: Sequence[Mapping[str, Any]], window: str
    ) -> Callable[[], KPIResult]:
        def _compute() -> KPIResult:
            return kpi.compute(rows, window)

        return _compute

    def _build_query(self, kpi: BaseKPI, window: str, scope: Mapping[str, str]) -> EventQuery:
        since_utc, until_utc = self._resolve_window(window, scope)
        return EventQuery(
            event_types=kpi.meta.required_events,
            equipment_ids=(scope["equipment_id"],) if "equipment_id" in scope else None,
            shift_ids=(scope["shift"],) if "shift" in scope else None,
            since_utc=since_utc,
            until_utc=until_utc,
        )

    def _resolve_window(
        self, window: str, scope: Mapping[str, str]
    ) -> tuple[datetime | None, datetime | None]:
        shift_id = scope.get("shift")
        if shift_id is not None and shift_id in self._shifts:
            shift = self._shifts[shift_id]
            return shift.start_utc, shift.end_utc
        since_raw = scope.get("since")
        until_raw = scope.get("until")
        since = datetime.fromisoformat(since_raw) if since_raw else None
        until = datetime.fromisoformat(until_raw) if until_raw else None
        return since, until

    def _resolve_scheduled_h(self, scope: Mapping[str, str]) -> float | None:
        shift_id = scope.get("shift")
        if shift_id is not None and shift_id in self._shifts:
            return self._shifts[shift_id].scheduled_h
        return None

    def _flatten(self, payload: Any, *, scheduled_h: float | None) -> Mapping[str, Any]:
        row = dict(to_dict(payload))
        row["event_type_code"] = payload.event_type_code
        duration_h = payload.duration_h()
        row["duration_h"] = duration_h
        alias = _DURATION_ALIAS_BY_EVENT_TYPE.get(payload.event_type_code)
        if alias is not None:
            row[alias] = duration_h
        if scheduled_h is not None:
            row["scheduled_h"] = scheduled_h
        return row
