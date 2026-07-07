"""Tests for mineproductivity.analytics.trend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics._registry import REGISTRY
from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.metadata import AnalyticsCategory
from mineproductivity.analytics.result import AnalyticsResult, TrendResult
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.trend import LinearTrendModel, TrendModel
from mineproductivity.analytics.windowing import RollingSpec

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


def _series(
    values: list[float], *, step: timedelta = timedelta(seconds=1), start: datetime = DAY_1
) -> TimeSeries:
    return TimeSeries(
        points=tuple(
            TimeSeriesPoint(timestamp=start + step * i, value=v) for i, v in enumerate(values)
        )
    )


class TestTrendModelIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            TrendModel()  # type: ignore[abstract]

    def test_is_an_analytics_model(self) -> None:
        assert issubclass(TrendModel, AnalyticsModel)


class TestLinearTrendModelMetadata:
    def test_code_is_trend_linear(self) -> None:
        assert LinearTrendModel.meta.code == "TREND.Linear"

    def test_min_observations_is_two(self) -> None:
        assert LinearTrendModel.meta.min_observations == 2

    def test_is_a_trend_model(self) -> None:
        assert issubclass(LinearTrendModel, TrendModel)

    def test_category_is_trend(self) -> None:
        assert LinearTrendModel.meta.category is AnalyticsCategory.TREND

    def test_description_is_non_empty(self) -> None:
        assert LinearTrendModel.meta.description


class TestLinearTrendModelIsRegistered:
    def test_code_is_in_the_registry(self) -> None:
        assert "TREND.Linear" in REGISTRY

    def test_registry_get_returns_this_class(self) -> None:
        assert REGISTRY.get("TREND.Linear") is LinearTrendModel

    def test_registry_metadata_matches_the_class_own_meta(self) -> None:
        assert REGISTRY.metadata_for("TREND.Linear").unwrap() is LinearTrendModel.meta


class TestLinearTrendModelNumericalCorrectness:
    def test_exact_hand_computed_fit(self) -> None:
        # x = [0, 1, 2, 3, 4] seconds, y = [2, 4, 5, 4, 5].
        # Hand-computed OLS: slope=0.6, intercept=2.8, r_squared=0.6.
        series = _series([2.0, 4.0, 5.0, 4.0, 5.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.slope == pytest.approx(0.6)
        assert result.intercept == pytest.approx(2.8)
        assert result.r_squared == pytest.approx(0.6)
        assert result.direction == "increasing"

    def test_perfect_linear_fit_has_r_squared_of_one(self) -> None:
        series = _series([0.0, 2.0, 4.0, 6.0, 8.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.slope == pytest.approx(2.0)
        assert result.r_squared == pytest.approx(1.0)

    def test_window_records_the_number_of_points_fitted(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.window == RollingSpec(periods=4)

    def test_model_code_is_attached_to_the_result(self) -> None:
        series = _series([1.0, 2.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert result.model_code == "TREND.Linear"


class TestDirectionPositive:
    def test_strictly_increasing_values(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.direction == "increasing"
        assert result.slope > 0.0


class TestDirectionNegative:
    def test_strictly_decreasing_values(self) -> None:
        series = _series([5.0, 4.0, 3.0, 2.0, 1.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.direction == "decreasing"
        assert result.slope < 0.0


class TestDirectionFlat:
    def test_constant_values(self) -> None:
        series = _series([7.0, 7.0, 7.0, 7.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.direction == "flat"
        assert result.slope == 0.0
        assert result.intercept == 7.0
        assert result.r_squared == 1.0


class TestNoisyTrend:
    def test_overall_increasing_with_noise_yields_positive_slope_and_imperfect_fit(self) -> None:
        # Clear upward trend with added noise that doesn't reverse the sign.
        series = _series([1.0, 3.0, 2.0, 5.0, 4.0, 7.0, 6.0, 9.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.direction == "increasing"
        assert result.slope > 0.0
        assert 0.0 < result.r_squared < 1.0

    def test_overall_decreasing_with_noise_yields_negative_slope_and_imperfect_fit(self) -> None:
        series = _series([9.0, 6.0, 7.0, 4.0, 5.0, 2.0, 3.0, 1.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.direction == "decreasing"
        assert result.slope < 0.0
        assert 0.0 < result.r_squared < 1.0


class TestDegenerateSameTimestamp:
    def test_all_points_at_the_same_timestamp_reports_a_flat_undefined_trend(self) -> None:
        series = TimeSeries(
            points=(
                TimeSeriesPoint(timestamp=DAY_1, value=1.0),
                TimeSeriesPoint(timestamp=DAY_1, value=5.0),
                TimeSeriesPoint(timestamp=DAY_1, value=3.0),
            )
        )
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.slope == 0.0
        assert result.r_squared == 0.0
        assert result.direction == "flat"
        assert len(result.warnings) == 1
        assert "same timestamp" in result.warnings[0]

    def test_intercept_is_the_mean_when_timestamps_are_degenerate(self) -> None:
        series = TimeSeries(
            points=(
                TimeSeriesPoint(timestamp=DAY_1, value=2.0),
                TimeSeriesPoint(timestamp=DAY_1, value=4.0),
            )
        )
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.intercept == 3.0


class TestInsufficientData:
    def test_single_point_series_returns_a_warning_result_not_a_trend_result(self) -> None:
        series = _series([1.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert not isinstance(result, TrendResult)
        assert type(result) is AnalyticsResult
        assert "insufficient data" in result.warnings[0]

    def test_empty_series_returns_a_warning_result(self) -> None:
        result = LinearTrendModel().analyze(TimeSeries(points=()), context=_context())
        assert not isinstance(result, TrendResult)
        assert "insufficient data" in result.warnings[0]

    def test_two_points_is_sufficient(self) -> None:
        """Exactly ``min_observations`` (2) must be enough to fit a line --
        and any two distinct-x points are always fit perfectly (a line
        has exactly two degrees of freedom)."""
        series = _series([1.0, 2.0])
        result = LinearTrendModel().analyze(series, context=_context())
        assert isinstance(result, TrendResult)
        assert result.r_squared == pytest.approx(1.0)
