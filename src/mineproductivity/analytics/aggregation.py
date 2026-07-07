"""``AggregationEngine``: group-and-reduce over raw numeric series or over
``kpis.KPIResult`` series, delegating correctly to ``kpis.KPIEngine``
whenever the underlying KPI's ``Aggregation`` semantics require it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, cast

from mineproductivity.core import Result
from mineproductivity.kpis import (
    REGISTRY,
    Aggregation,
    KPIEngine,
    KPIMetadata,
    KPINotFoundError,
    KPIResult,
)
from mineproductivity.kpis.backends import ExecutionBackend

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.result import AnalyticsResult
from mineproductivity.analytics.statistics import describe
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

__all__ = ["AggregationEngine", "GroupBySpec"]

#: ``Aggregation`` kinds whose combined value is a direct sum of already-
#: computed ``KPIResult.value``\\ s -- correct because summing sums (or
#: cumulative running totals) is associative across the combined scope.
#: Every other kind (``RATIO``, ``AVERAGE``, ``WEIGHTED_AVERAGE``,
#: ``ROLLING``, ``DERIVED``) re-derives via ``KPIEngine.execute`` instead
#: (design spec §10, §34) -- the safe default for any kind not proven
#: associative under direct summation.
_DIRECTLY_SUMMABLE = (Aggregation.ADDITIVE, Aggregation.CUMULATIVE)


class GroupBySpec:
    """Which field(s) to group a ``TimeSeries`` by before reduction, e.g.
    ``("equipment_id",)`` or ``("pit", "shift")``.

    Examples
    --------
    >>> GroupBySpec(("pit", "shift")).by
    ('pit', 'shift')
    """

    def __init__(self, by: tuple[str, ...]) -> None:
        self.by = by

    def __repr__(self) -> str:
        return f"{type(self).__name__}(by={self.by!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GroupBySpec):
            return NotImplemented
        return self.by == other.by

    def __hash__(self) -> int:
        return hash(self.by)


class AggregationEngine:
    """Group-and-reduce over raw numeric series or over ``KPIResult``
    series, delegating correctly to ``kpis.KPIEngine`` whenever the
    underlying KPI's ``Aggregation`` semantics require it.

    ``backend`` is accepted and stored for constructor-shape consistency
    with ``kpis.KPIEngine`` (design spec §36's "accepts an optional
    ExecutionBackend, falls back to a plain-Python reference path when
    none is supplied"), but neither :meth:`reduce` nor
    :meth:`reduce_kpi_results` reads it: ``reduce_kpi_results`` delegates
    to its own ``engine`` parameter's already-configured backend instead,
    and ``reduce`` deliberately never needs one --
    ``kpis.backends.ExecutionBackend.group_and_aggregate`` is keyed by
    ``kpis.Aggregation`` (``ADDITIVE``/``RATIO``/``AVERAGE``/...), which
    has no ``"median"`` member and is inherently a *KPI* aggregation
    vocabulary; ``reduce`` is explicitly "no KPI semantics involved"
    (see its own docstring), so bridging its ``sum``/``mean``/``median``
    vocabulary onto ``Aggregation`` would force an artificial, partly
    impossible correspondence rather than genuine reuse. ``reduce`` is
    therefore always the plain-Python reference path, satisfying §36's
    fallback requirement unconditionally rather than conditionally.
    """

    def __init__(self, *, backend: ExecutionBackend | None = None) -> None:
        self._backend = backend

    def reduce(
        self,
        series: TimeSeries,
        by: GroupBySpec,
        *,
        reduction: Literal["sum", "mean", "median"],
    ) -> Mapping[tuple[str, ...], AnalyticsResult]:
        """Pure statistical reduction over a series of plain numeric
        observations -- no KPI semantics involved. Safe for any input
        that is not itself a ``KPIResult`` series.

        Groups ``series.points`` by the scope values named in ``by.by``
        (a point missing any of those scope keys is excluded from every
        group -- "qualify, don't coerce": it cannot be classified, so it
        is silently left out rather than mis-grouped under a fabricated
        key), then reuses :func:`~mineproductivity.analytics.statistics.describe`
        verbatim over each group's own sub-series. No new numerical
        computation is introduced.

        This was previously deferred because no existing
        ``AnalyticsResult`` subtype appeared to expose ``reduction``'s
        three named values individually. Re-examined for this phase:
        ``describe()``'s own ``_DEFAULT_PERCENTILES`` constant is fixed
        at ``(50, 90, 99)`` (not caller-configurable), so
        ``StatisticalSummary.percentiles[50]`` is *guaranteed*, not
        merely likely, present for every non-empty group -- the earlier
        concern about relying on an "undocumented," possibly-absent key
        no longer applies once that guarantee is stated explicitly
        (as it now is, here). Each of ``reduction``'s three values is
        therefore always exactly derivable from the one returned
        ``StatisticalSummary`` per group:

        - ``"mean"`` -- ``summary.mean`` directly.
        - ``"median"`` -- ``summary.percentiles[50]``.
        - ``"sum"`` -- ``summary.mean * summary.n`` (an algebraic
          identity, not a second summation pass over the group).

        The full ``StatisticalSummary`` is returned rather than a bare
        float so a caller reading more than the one field they asked
        for is never worse off, and so this method needs no result
        shape narrower than the one ``statistics.py`` already provides
        -- avoiding both a new result type and a second, parallel
        "just the one number" abstraction next to the descriptive one
        this package already has.
        """
        groups: dict[tuple[str, ...], list[TimeSeriesPoint]] = {}
        for point in series.points:
            if not all(field in point.scope for field in by.by):
                continue
            key = tuple(point.scope[field] for field in by.by)
            groups.setdefault(key, []).append(point)

        return {key: describe(TimeSeries(points=tuple(points))) for key, points in groups.items()}

    def reduce_kpi_results(
        self,
        results: Sequence[KPIResult],
        *,
        engine: KPIEngine,
        window: str,
        combined_scope: Mapping[str, str],
    ) -> Result[KPIResult]:
        """Group-and-reduce over ``KPIResult`` observations, respecting
        ``KPIMetadata.aggregation`` (kpis spec §10.2, §19's "RATIO-never-
        averaged" rule) one layer up from where ``kpis`` itself enforces
        it.

        For ``ADDITIVE``/``CUMULATIVE``-aggregation KPIs, this is a
        direct sum. For every other aggregation kind (``RATIO``,
        ``AVERAGE``, ``WEIGHTED_AVERAGE``, ``ROLLING``, ``DERIVED``),
        this method does **not** average ``results``' already-computed
        ``.value``\\ s -- it re-invokes
        ``engine.execute(code, window=window, scope=combined_scope)``
        over the union scope, exactly reusing ``kpis``' own engine-level
        ratio-correctness guarantee instead of re-deriving (and risking
        getting wrong) the same rule a second time (§34).

        A ``window`` keyword-only parameter is added beyond the design
        spec's own illustrative signature: ``KPIEngine.execute`` requires
        one and no other parameter here can supply it -- a necessary,
        minimal, disclosed correction (the same kind already applied to
        ``TimeSeries.from_kpi_results``' ``timestamps`` parameter in the
        Analytics Foundation phase).

        Raises
        ------
        AnalyticsValidationError
            If ``results`` is empty, or if ``results`` mix more than one
            KPI ``code`` (combining different metrics has no meaning).
        """
        if not results:
            raise AnalyticsValidationError("reduce_kpi_results requires at least one KPIResult")
        code = results[0].code
        if any(result.code != code for result in results):
            raise AnalyticsValidationError(
                "reduce_kpi_results requires every KPIResult to share the same code"
            )

        metadata_lookup = REGISTRY.metadata_for(code)
        if metadata_lookup.is_nothing:
            return Result.err(KPINotFoundError(f"no registered KPI metadata for code {code!r}"))
        metadata = cast(KPIMetadata, metadata_lookup.unwrap())

        if metadata.aggregation in _DIRECTLY_SUMMABLE:
            return Result.ok(self._direct_sum(results, code=code, combined_scope=combined_scope))
        return engine.execute(code, window=window, scope=combined_scope)

    @staticmethod
    def _direct_sum(
        results: Sequence[KPIResult], *, code: str, combined_scope: Mapping[str, str]
    ) -> KPIResult:
        total_n = sum(result.n for result in results)
        if any(result.value is None for result in results):
            return KPIResult(
                code=code,
                value=None,
                unit=results[0].unit,
                n=total_n,
                scope=combined_scope,
                warnings=("one or more source KPIResults had no computable value",),
            )
        total_value = sum(cast(float, result.value) for result in results)
        return KPIResult(
            code=code, value=total_value, unit=results[0].unit, n=total_n, scope=combined_scope
        )
