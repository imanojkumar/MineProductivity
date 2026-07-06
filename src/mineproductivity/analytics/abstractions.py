"""``AnalyticsModel``: the "Analytics-as-object" root every registrable
analytics strategy implements, and ``AnalyticsContext``, the collaborator
bundle a concrete model may need.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from mineproductivity.events import EventStore
from mineproductivity.kpis import KPIEngine
from mineproductivity.kpis.backends import ExecutionBackend

from mineproductivity.analytics.metadata import AnalyticsMetadata
from mineproductivity.analytics.result import AnalyticsResult
from mineproductivity.analytics.timeseries import TimeSeries

__all__ = ["AnalyticsContext", "AnalyticsModel"]


class AnalyticsContext:
    """Bundles the collaborators an ``AnalyticsModel`` may need -- the
    analytics-layer counterpart to ``KPIEngine``'s own constructor
    bundle. Every field is optional except ``event_store`` because some
    models (e.g. a pure statistical summary over an already-fetched
    ``TimeSeries``) need nothing else.

    Examples
    --------
    >>> class _FakeStore: ...
    >>> ctx = AnalyticsContext(event_store=_FakeStore())
    >>> ctx.kpi_engine is None
    True
    """

    def __init__(
        self,
        *,
        event_store: EventStore[Any],
        kpi_engine: KPIEngine | None = None,
        backend: ExecutionBackend | None = None,
    ) -> None:
        self.event_store = event_store
        self.kpi_engine = kpi_engine
        self.backend = backend

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(event_store={self.event_store!r}, "
            f"kpi_engine={self.kpi_engine!r}, backend={self.backend!r})"
        )


class AnalyticsModel(ABC):
    """The root of every registrable analytics strategy -- 'Analytics-
    as-object,' the direct one-layer-up counterpart of ``kpis.BaseKPI``.
    A concrete leaf declares ``meta: ClassVar[AnalyticsMetadata]`` and
    implements :meth:`_analyze`; everything else (input validation,
    result envelope wrapping) is inherited, mirroring ``BaseKPI``/
    ``_compute`` exactly.

    ``AnalyticsModel`` is deliberately not split into category families
    the way ``kpis.BaseKPI`` is split by mining-domain namespace --
    Analytics organizes by *analytical function* (trend, baseline,
    benchmark, forecasting, anomaly, outlier), not by mining domain
    namespace, so every category shares this one abstraction.

    **Thread safety.** Every ``AnalyticsModel`` subclass MUST be
    stateless across :meth:`analyze` calls -- no instance attribute is
    mutated by :meth:`_analyze` -- so a single instance is safe to share
    and invoke concurrently from multiple threads.
    """

    meta: ClassVar[AnalyticsMetadata]

    @abstractmethod
    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        """Pure function: a ``TimeSeries`` (of raw values or
        ``KPIResult``\\ s) plus ``context`` in, one ``AnalyticsResult``
        out. MUST NOT raise for a legitimately un-analyzable input (e.g.
        fewer observations than the model requires) -- return an
        ``AnalyticsResult`` carrying a warning instead, the same
        "qualify, don't coerce" rule ``kpis.BaseKPI`` already
        establishes."""

    def analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        """Non-overridden orchestration: checks ``series`` has the
        minimum number of observations this model declares needing
        (``meta.min_observations``), then calls :meth:`_analyze`."""
        if len(series) < self.meta.min_observations:
            return AnalyticsResult(
                model_code=self.meta.code,
                warnings=(
                    f"insufficient data: {len(series)} observations, "
                    f"{self.meta.min_observations} required",
                ),
            )
        return self._analyze(series, context=context)
