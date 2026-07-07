"""Tests for mineproductivity.analytics.abstractions."""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timedelta, timezone
from typing import ClassVar

import pytest

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.result import AnalyticsResult, TrendResult
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.trend import LinearTrendModel

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
DAY_2 = datetime(2026, 1, 2, tzinfo=timezone.utc)


class _StubModel(AnalyticsModel):
    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="TREND.Stub",
        category=AnalyticsCategory.TREND,
        description="test-only",
        min_observations=2,
    )

    def __init__(self) -> None:
        self.analyze_calls = 0

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        self.analyze_calls += 1
        return AnalyticsResult(model_code=self.meta.code)


class TestAnalyticsContext:
    def test_construction_with_only_event_store(self) -> None:
        store = _InMemoryEventStore()
        context = AnalyticsContext(event_store=store)
        assert context.event_store is store
        assert context.kpi_engine is None
        assert context.backend is None

    def test_repr_includes_class_name(self) -> None:
        context = AnalyticsContext(event_store=_InMemoryEventStore())
        assert "AnalyticsContext" in repr(context)


class TestAnalyticsModel:
    def test_cannot_instantiate_abstract_base_directly(self) -> None:
        with pytest.raises(TypeError):
            AnalyticsModel()  # type: ignore[abstract]

    def test_analyze_delegates_to_analyze_impl_when_enough_data(self) -> None:
        model = _StubModel()
        context = AnalyticsContext(event_store=_InMemoryEventStore())
        series = TimeSeries(
            points=(
                TimeSeriesPoint(timestamp=DAY_1, value=1.0),
                TimeSeriesPoint(timestamp=DAY_2, value=2.0),
            )
        )

        result = model.analyze(series, context=context)

        assert model.analyze_calls == 1
        assert result.model_code == "TREND.Stub"
        assert result.warnings == ()

    def test_analyze_returns_warning_result_without_calling_analyze_impl_when_insufficient(
        self,
    ) -> None:
        model = _StubModel()
        context = AnalyticsContext(event_store=_InMemoryEventStore())
        series = TimeSeries(points=(TimeSeriesPoint(timestamp=DAY_1, value=1.0),))

        result = model.analyze(series, context=context)

        assert model.analyze_calls == 0
        assert result.model_code == "TREND.Stub"
        assert len(result.warnings) == 1
        assert "insufficient data" in result.warnings[0]


class TestAnalyticsModelStatelessConcurrency:
    """``AnalyticsModel``'s own class docstring: 'every subclass MUST be
    stateless across analyze() calls... so a single instance is safe to
    share and invoke concurrently from multiple threads.' Proven here
    against a real, already-implemented model (``LinearTrendModel``)
    rather than a synthetic stub -- ``_StubModel`` above deliberately
    mutates an ``analyze_calls`` counter to prove orchestration
    call-counting, which is the opposite of what this test needs;
    ``LinearTrendModel`` has no mutable instance state at all and a
    nontrivial per-call computation (an OLS fit), so a data race would
    show up as a wrong-slope result for one of the concurrent calls."""

    def test_shared_instance_produces_correct_independent_results_under_concurrent_analyze(
        self,
    ) -> None:
        model = LinearTrendModel()
        context = AnalyticsContext(event_store=_InMemoryEventStore())

        def _series_for(slope: float) -> TimeSeries:
            return TimeSeries(
                points=tuple(
                    TimeSeriesPoint(timestamp=DAY_1 + timedelta(seconds=i), value=slope * i)
                    for i in range(10)
                )
            )

        slopes = [float(i) for i in range(1, 21)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [
                pool.submit(model.analyze, _series_for(slope), context=context) for slope in slopes
            ]
            results = [future.result() for future in futures]

        for slope, result in zip(slopes, results, strict=True):
            assert isinstance(result, TrendResult)
            assert result.slope == pytest.approx(slope)
