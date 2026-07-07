"""Tests for mineproductivity.analytics.baseline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics._registry import REGISTRY
from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.baseline import BaselineModel, RollingBaselineModel
from mineproductivity.analytics.metadata import AnalyticsCategory
from mineproductivity.analytics.result import AnalyticsResult, Baseline
from mineproductivity.analytics.rolling import rolling_mean, rolling_std
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.windowing import RollingSpec
from mineproductivity.kpis import RollingWindow

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


def _series(values: list[float], *, step: timedelta = timedelta(days=1)) -> TimeSeries:
    return TimeSeries(
        points=tuple(
            TimeSeriesPoint(timestamp=DAY_1 + step * i, value=v) for i, v in enumerate(values)
        )
    )


class TestBaselineModelIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaselineModel()  # type: ignore[abstract]

    def test_is_an_analytics_model(self) -> None:
        assert issubclass(BaselineModel, AnalyticsModel)


class TestRollingBaselineModelMetadata:
    def test_code_is_baseline_rolling(self) -> None:
        assert RollingBaselineModel.meta.code == "BASELINE.Rolling"

    def test_category_is_baseline(self) -> None:
        assert RollingBaselineModel.meta.category is AnalyticsCategory.BASELINE

    def test_min_observations_is_one(self) -> None:
        assert RollingBaselineModel.meta.min_observations == 1

    def test_is_a_baseline_model(self) -> None:
        assert issubclass(RollingBaselineModel, BaselineModel)

    def test_description_is_non_empty(self) -> None:
        assert RollingBaselineModel.meta.description

    def test_repr_includes_spec_and_k(self) -> None:
        model = RollingBaselineModel(spec=RollingSpec(periods=3, min_periods=3), k=3.0)
        assert "RollingSpec" in repr(model)
        assert "3.0" in repr(model)


class TestRollingBaselineModelIsRegistered:
    def test_code_is_in_the_registry(self) -> None:
        assert "BASELINE.Rolling" in REGISTRY

    def test_registry_get_returns_this_class(self) -> None:
        assert REGISTRY.get("BASELINE.Rolling") is RollingBaselineModel

    def test_registry_metadata_matches_the_class_own_meta(self) -> None:
        assert REGISTRY.metadata_for("BASELINE.Rolling").unwrap() is RollingBaselineModel.meta


class TestConstantBaseline:
    def test_zero_std_and_collapsed_band(self) -> None:
        series = _series([10.0, 10.0, 10.0, 10.0, 10.0])
        model = RollingBaselineModel(spec=RollingSpec(periods=3, min_periods=3))
        result = model.analyze(series, context=_context())
        assert isinstance(result, Baseline)
        assert result.mean == 10.0
        assert result.std == 0.0
        assert result.lower == 10.0
        assert result.upper == 10.0


class TestIncreasingBaseline:
    def test_reflects_the_trailing_window_not_the_whole_series(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0, 5.0])
        spec = RollingSpec(periods=2, min_periods=2)
        model = RollingBaselineModel(spec=spec)
        result = model.analyze(series, context=_context())
        assert isinstance(result, Baseline)
        # Trailing window ending at the last point: [4.0, 5.0] -> mean=4.5.
        assert result.mean == pytest.approx(4.5)
        assert result.mean != pytest.approx(3.0)  # not the whole-series mean

    def test_band_widens_with_larger_k(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0, 5.0])
        spec = RollingSpec(periods=3, min_periods=3)
        narrow = RollingBaselineModel(spec=spec, k=1.0).analyze(series, context=_context())
        wide = RollingBaselineModel(spec=spec, k=3.0).analyze(series, context=_context())
        assert isinstance(narrow, Baseline)
        assert isinstance(wide, Baseline)
        assert (wide.upper - wide.lower) > (narrow.upper - narrow.lower)


class TestDecreasingBaseline:
    def test_reflects_the_trailing_window(self) -> None:
        series = _series([5.0, 4.0, 3.0, 2.0, 1.0])
        spec = RollingSpec(periods=2, min_periods=2)
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)
        # Trailing window ending at the last point: [2.0, 1.0] -> mean=1.5.
        assert result.mean == pytest.approx(1.5)


class TestNoisyData:
    def test_positive_std_and_band_brackets_the_mean(self) -> None:
        series = _series([10.0, 12.0, 9.0, 11.0, 10.5, 13.0])
        spec = RollingSpec(periods=4, min_periods=4)
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)
        assert result.std > 0.0
        assert result.lower < result.mean < result.upper


class TestRollingBaselineCorrectness:
    def test_matches_rolling_mean_and_rolling_std_directly(self) -> None:
        """The returned mean/std must be exactly the last point of
        ``rolling_mean``/``rolling_std`` over the same series and spec --
        proof that no separate moving-average logic was reimplemented."""
        series = _series([2.0, 4.0, 6.0, 8.0, 10.0, 3.0])
        spec = RollingSpec(periods=3, min_periods=3)
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)

        expected_mean = rolling_mean(series, spec).values()[-1]
        expected_std = rolling_std(series, spec).values()[-1]
        assert result.mean == expected_mean
        assert result.std == expected_std
        assert result.lower == pytest.approx(expected_mean - 2.0 * expected_std)
        assert result.upper == pytest.approx(expected_mean + 2.0 * expected_std)

    def test_spec_is_attached_to_the_result(self) -> None:
        spec = RollingSpec(periods=3, min_periods=3)
        series = _series([1.0, 2.0, 3.0, 4.0])
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)
        assert result.spec == spec

    def test_default_k_is_two(self) -> None:
        series = _series([1.0, 2.0, 3.0])
        spec = RollingSpec(periods=3, min_periods=3)
        explicit = RollingBaselineModel(spec=spec, k=2.0).analyze(series, context=_context())
        default = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(explicit, Baseline)
        assert isinstance(default, Baseline)
        assert default.lower == explicit.lower
        assert default.upper == explicit.upper

    def test_time_based_spec_reflects_the_trailing_duration(self) -> None:
        """``RollingBaselineModel`` must handle a ``time_window``-based
        spec exactly like a count-based one -- it never branches on
        which kind of ``RollingSpec`` it was given itself, only
        ``rolling_mean``/``rolling_std`` do."""
        series = _series([1.0, 2.0, 3.0, 4.0], step=timedelta(days=1))
        spec = RollingSpec(
            time_window=RollingWindow(kind="day", span=timedelta(days=1), step=timedelta(days=1)),
            min_periods=2,
        )
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)
        # Trailing 1-day window ending at day4: [day3=3.0, day4=4.0] -> mean=3.5.
        assert result.mean == pytest.approx(3.5)


class TestComparisonAgainstBaseline:
    def test_a_typical_observation_falls_within_the_band(self) -> None:
        history = _series([98.0, 102.0, 99.0, 101.0, 100.0, 100.5, 99.5, 101.5])
        spec = RollingSpec(periods=6, min_periods=6)
        baseline = RollingBaselineModel(spec=spec).analyze(history, context=_context())
        assert isinstance(baseline, Baseline)

        typical_observation = 100.0
        assert baseline.lower <= typical_observation <= baseline.upper

    def test_an_extreme_observation_falls_outside_the_band(self) -> None:
        history = _series([98.0, 102.0, 99.0, 101.0, 100.0, 100.5, 99.5, 101.5])
        spec = RollingSpec(periods=6, min_periods=6)
        baseline = RollingBaselineModel(spec=spec).analyze(history, context=_context())
        assert isinstance(baseline, Baseline)

        extreme_observation = 1000.0
        assert not (baseline.lower <= extreme_observation <= baseline.upper)


class TestEmptySeries:
    def test_returns_a_warning_result_via_the_generic_min_observations_check(self) -> None:
        model = RollingBaselineModel(spec=RollingSpec(periods=3, min_periods=3))
        result = model.analyze(TimeSeries(points=()), context=_context())
        assert not isinstance(result, Baseline)
        assert type(result) is AnalyticsResult
        assert "insufficient data" in result.warnings[0]


class TestSingleObservation:
    def test_single_point_with_a_periods_one_spec_produces_a_degenerate_baseline(self) -> None:
        series = _series([42.0])
        spec = RollingSpec(periods=1, min_periods=1)
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)
        assert result.mean == 42.0
        assert result.std == 0.0
        assert result.lower == result.upper == 42.0

    def test_single_point_reaches_analyze_because_min_observations_is_one(self) -> None:
        """Unlike ``LinearTrendModel`` (which needs 2+ points for OLS),
        a rolling baseline is well-defined for a single observation, so
        ``min_observations=1`` lets it through to ``_analyze`` instead of
        the generic insufficient-data short circuit."""
        series = _series([1.0])
        spec = RollingSpec(periods=1, min_periods=1)
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)


class TestInsufficientHistory:
    def test_spec_min_periods_never_satisfied_falls_back_with_a_warning(self) -> None:
        """A series long enough to pass the generic ``min_observations``
        check can still be too short for the *rolling spec's own*
        ``min_periods`` -- a distinct, model-specific insufficiency."""
        series = _series([1.0, 2.0, 3.0])
        spec = RollingSpec(periods=10, min_periods=10)
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)
        assert len(result.warnings) == 1
        assert "insufficient" in result.warnings[0] or "trailing history" in result.warnings[0]

    def test_fallback_uses_whole_series_statistics(self) -> None:
        series = _series([1.0, 2.0, 3.0])
        spec = RollingSpec(periods=10, min_periods=10)
        result = RollingBaselineModel(spec=spec).analyze(series, context=_context())
        assert isinstance(result, Baseline)
        assert result.mean == pytest.approx(2.0)
