"""Tests for mineproductivity.analytics.forecasting.

Per design spec §35's testing philosophy for interface-only modules:
``ForecastingModel`` is tested only for its ABC contract (bare-ABC
instantiation raises ``TypeError``; a minimal test-only concrete
subclass satisfies the abstract method signatures) -- there is no
algorithmic-correctness test, since this package ships no forecasting
algorithm.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import ClassVar

import pytest

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.forecasting import ForecastingModel
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.result import AnalyticsResult, ConfidenceInterval, ForecastResult
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


def _series() -> TimeSeries:
    return TimeSeries(points=(TimeSeriesPoint(timestamp=DAY_1, value=1.0),))


class _FakeForecastingModel(ForecastingModel):
    """Minimal, test-only concrete subclass satisfying both abstract
    methods -- not a shipped algorithm, purely a contract-conformance
    fixture (design spec §35)."""

    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="FORECASTING.Fake",
        category=AnalyticsCategory.FORECASTING,
        description="Test-only fixture satisfying the ForecastingModel contract.",
        min_observations=0,
    )

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        return self._forecast(series, horizon=1, context=context)

    def _forecast(
        self, series: TimeSeries, *, horizon: int, context: AnalyticsContext
    ) -> ForecastResult:
        return ForecastResult(
            model_code=self.meta.code,
            horizon=horizon,
            predicted=tuple(0.0 for _ in range(horizon)),
            intervals=tuple(
                ConfidenceInterval(lower=0.0, upper=0.0, confidence=0.95, method="normal")
                for _ in range(horizon)
            ),
        )


class TestForecastingModelIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            ForecastingModel()  # type: ignore[abstract]

    def test_is_an_analytics_model(self) -> None:
        assert issubclass(ForecastingModel, AnalyticsModel)

    def test_both_analyze_and_forecast_remain_abstract(self) -> None:
        """``ForecastingModel`` does not override ``_analyze`` -- exactly
        like every other category base in this package (``TrendModel``,
        ``BaselineModel``, ``BenchmarkModel``), leaving that decision to
        a concrete subclass. No concrete subclass ships here."""
        assert ForecastingModel.__abstractmethods__ == frozenset({"_analyze", "_forecast"})

    def test_forecast_is_the_only_new_abstract_method(self) -> None:
        assert "_forecast" in ForecastingModel.__dict__
        assert getattr(ForecastingModel._forecast, "__isabstractmethod__", False)


class TestConcreteSubclassSatisfiesContract:
    def test_a_minimal_subclass_can_be_instantiated(self) -> None:
        model = _FakeForecastingModel()
        assert isinstance(model, ForecastingModel)

    def test_forecast_returns_a_forecastresult(self) -> None:
        model = _FakeForecastingModel()
        result = model._forecast(_series(), horizon=3, context=_context())
        assert isinstance(result, ForecastResult)
        assert result.horizon == 3
        assert len(result.predicted) == 3
        assert len(result.intervals) == 3

    def test_forecast_signature_accepts_horizon_and_context_as_keywords(self) -> None:
        model = _FakeForecastingModel()
        result = model._forecast(_series(), horizon=1, context=_context())
        assert isinstance(result, ForecastResult)

    def test_analyze_orchestration_still_applies(self) -> None:
        """``AnalyticsModel.analyze()``'s generic min_observations gate
        still governs a ``ForecastingModel`` subclass exactly as it
        governs every other concrete model in this package."""
        model = _FakeForecastingModel()
        result = model.analyze(_series(), context=_context())
        assert isinstance(result, ForecastResult)

    def test_insufficient_data_short_circuits_before_forecast_is_called(self) -> None:
        class _StrictFakeModel(_FakeForecastingModel):
            meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
                code="FORECASTING.Strict",
                category=AnalyticsCategory.FORECASTING,
                description="x",
                min_observations=5,
            )

        result = _StrictFakeModel().analyze(_series(), context=_context())
        assert type(result) is AnalyticsResult
        assert "insufficient data" in result.warnings[0]


class TestInterfacePurity:
    """Design spec §35's own "interface-purity proof": zero concrete,
    non-test subclasses of ``ForecastingModel`` ship inside
    ``forecasting.py`` itself (checklist §16 line item)."""

    def test_forecasting_module_defines_no_concrete_subclass(self) -> None:
        import mineproductivity.analytics.forecasting as forecasting_module

        concrete_subclasses = [
            member
            for _, member in inspect.getmembers(forecasting_module, inspect.isclass)
            if issubclass(member, ForecastingModel)
            and member is not ForecastingModel
            and not inspect.isabstract(member)
        ]
        assert concrete_subclasses == []

    def test_forecastingmodel_itself_is_the_only_class_defined_in_the_module(self) -> None:
        import mineproductivity.analytics.forecasting as forecasting_module

        classes_defined_here = [
            name
            for name, member in inspect.getmembers(forecasting_module, inspect.isclass)
            if member.__module__ == forecasting_module.__name__
        ]
        assert classes_defined_here == ["ForecastingModel"]


class TestPublicApiValidation:
    def test_forecastingmodel_is_exported(self) -> None:
        import mineproductivity.analytics as analytics

        assert "ForecastingModel" in analytics.__all__
        assert analytics.ForecastingModel is ForecastingModel

    def test_forecastresult_and_confidenceinterval_are_reused_not_duplicated(self) -> None:
        """No new result type was introduced -- ``ForecastResult`` and
        ``ConfidenceInterval`` already existed in ``result.py`` since
        the Foundation phase."""
        import mineproductivity.analytics.result as result_module

        assert ForecastResult.__module__ == result_module.__name__
        assert ConfidenceInterval.__module__ == result_module.__name__
