"""Tests for mineproductivity.analytics.rolling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.analytics.rolling import rolling_apply, rolling_mean, rolling_std
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.windowing import RollingSpec
from mineproductivity.kpis import RollingWindow

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _series(values: list[float], *, step: timedelta = timedelta(days=1)) -> TimeSeries:
    return TimeSeries(
        points=tuple(
            TimeSeriesPoint(timestamp=DAY_1 + step * i, value=v) for i, v in enumerate(values)
        )
    )


class TestRollingMeanCountBased:
    def test_known_values(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0])
        result = rolling_mean(series, RollingSpec(periods=2, min_periods=2))
        assert result.values() == (1.5, 2.5, 3.5)

    def test_leading_points_below_min_periods_are_omitted_not_sentinel(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0])
        result = rolling_mean(series, RollingSpec(periods=2, min_periods=2))
        assert len(result) == 3
        assert len(result) < len(series)

    def test_min_periods_one_includes_every_point(self) -> None:
        series = _series([10.0, 20.0, 30.0])
        result = rolling_mean(series, RollingSpec(periods=2, min_periods=1))
        assert len(result) == len(series)
        assert result.values() == (10.0, 15.0, 25.0)

    def test_output_timestamps_match_input_timestamps(self) -> None:
        series = _series([1.0, 2.0, 3.0])
        result = rolling_mean(series, RollingSpec(periods=2, min_periods=1))
        assert [p.timestamp for p in result.points] == [p.timestamp for p in series.points]

    def test_scope_is_preserved_from_the_originating_point(self) -> None:
        series = TimeSeries(
            points=(
                TimeSeriesPoint(timestamp=DAY_1, value=1.0, scope={"pit": "north"}),
                TimeSeriesPoint(
                    timestamp=DAY_1 + timedelta(days=1), value=2.0, scope={"pit": "south"}
                ),
            )
        )
        result = rolling_mean(series, RollingSpec(periods=2, min_periods=1))
        assert result.points[0].scope["pit"] == "north"
        assert result.points[1].scope["pit"] == "south"


class TestRollingStdCountBased:
    def test_known_values(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0])
        result = rolling_std(series, RollingSpec(periods=2, min_periods=2))
        # Population std of any two consecutive integers is always 0.5.
        assert result.values() == (0.5, 0.5, 0.5)

    def test_single_point_window_has_zero_std(self) -> None:
        series = _series([5.0, 100.0, 7.0])
        result = rolling_std(series, RollingSpec(periods=1, min_periods=1))
        assert result.values() == (0.0, 0.0, 0.0)


class TestRollingApply:
    def test_custom_reduction_function(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0])
        result = rolling_apply(series, RollingSpec(periods=2, min_periods=2), max)
        assert result.values() == (2.0, 3.0, 4.0)

    def test_matches_rolling_mean_when_fn_is_mean_shaped(self) -> None:
        series = _series([2.0, 4.0, 6.0, 8.0])
        spec = RollingSpec(periods=3, min_periods=2)
        via_apply = rolling_apply(series, spec, lambda values: sum(values) / len(values))
        via_named = rolling_mean(series, spec)
        assert via_apply.values() == via_named.values()


class TestTimeBasedWindow:
    def test_spans_the_correct_trailing_duration(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0], step=timedelta(days=1))
        spec = RollingSpec(
            time_window=RollingWindow(kind="day", span=timedelta(days=2), step=timedelta(days=1)),
            min_periods=1,
        )
        result = rolling_mean(series, spec)
        # span=2 days is inclusive of the boundary: day1:[1]->1.0;
        # day2:[1,2]->1.5; day3:[1,2,3] (day1 is exactly 2 days back)->2.0;
        # day4:[2,3,4] (day1 is now 3 days back, excluded)->3.0.
        assert result.values() == (1.0, 1.5, 2.0, 3.0)

    def test_min_periods_omits_points_before_window_fills_with_time_based_spec(self) -> None:
        series = _series([1.0, 2.0, 3.0, 4.0], step=timedelta(days=1))
        spec = RollingSpec(
            time_window=RollingWindow(kind="day", span=timedelta(days=2), step=timedelta(days=1)),
            min_periods=2,
        )
        result = rolling_mean(series, spec)
        assert len(result) == 3
        assert result.values() == (1.5, 2.0, 3.0)


class TestBoundaryAndEdgeCases:
    def test_empty_series_returns_empty_series(self) -> None:
        result = rolling_mean(TimeSeries(points=()), RollingSpec(periods=2, min_periods=1))
        assert len(result) == 0

    def test_single_point_series_with_min_periods_one(self) -> None:
        series = _series([42.0])
        result = rolling_mean(series, RollingSpec(periods=5, min_periods=1))
        assert result.values() == (42.0,)

    def test_window_larger_than_the_series_still_uses_all_available_points(self) -> None:
        series = _series([1.0, 2.0, 3.0])
        result = rolling_mean(series, RollingSpec(periods=100, min_periods=1))
        # Every point's window is clamped to "everything seen so far".
        assert result.values() == (1.0, 1.5, 2.0)

    def test_min_periods_exceeding_series_length_yields_empty_result(self) -> None:
        series = _series([1.0, 2.0, 3.0])
        result = rolling_mean(series, RollingSpec(periods=100, min_periods=10))
        assert len(result) == 0

    def test_min_periods_equal_to_series_length_yields_exactly_one_point(self) -> None:
        series = _series([1.0, 2.0, 3.0])
        result = rolling_mean(series, RollingSpec(periods=3, min_periods=3))
        assert len(result) == 1
        assert result.values() == (2.0,)

    def test_periods_of_one_is_a_pass_through_for_mean(self) -> None:
        series = _series([5.0, 10.0, 15.0])
        result = rolling_mean(series, RollingSpec(periods=1, min_periods=1))
        assert result.values() == series.values()

    def test_reduction_function_is_never_called_on_a_below_threshold_window(self) -> None:
        """The "absent point, not a sentinel" rule means ``fn`` must not
        even be invoked for a point whose window hasn't filled -- not
        just that its result gets discarded afterward."""
        calls: list[tuple[float, ...]] = []

        def _spy(values: list[float]) -> float:
            calls.append(tuple(values))
            return sum(values)

        series = _series([1.0, 2.0, 3.0])
        rolling_apply(series, RollingSpec(periods=2, min_periods=2), _spy)
        assert all(len(call) >= 2 for call in calls)

    def test_non_positive_periods_yields_empty_result_without_raising(self) -> None:
        """``RollingSpec`` itself only validates that exactly one of
        ``time_window``/``periods`` is set, not that ``periods`` is
        positive -- a non-positive value degrades gracefully to "no
        window is ever big enough" rather than crashing."""
        series = _series([1.0, 2.0, 3.0])
        result = rolling_mean(series, RollingSpec(periods=0, min_periods=1))
        assert len(result) == 0
