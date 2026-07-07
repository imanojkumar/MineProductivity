"""Tests for mineproductivity.analytics.statistics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.result import (
    ConfidenceInterval,
    DistributionSummary,
    Histogram,
    StatisticalSummary,
)
from mineproductivity.analytics.statistics import (
    confidence_interval,
    describe,
    distribution,
    histogram,
    percentile,
)
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _series(values: list[float]) -> TimeSeries:
    return TimeSeries(
        points=tuple(
            TimeSeriesPoint(timestamp=DAY_1 + timedelta(days=i), value=v)
            for i, v in enumerate(values)
        )
    )


class TestPercentile:
    def test_median_of_odd_length(self) -> None:
        assert percentile([3.0, 1.0, 2.0], 50) == 2.0

    def test_median_of_even_length_interpolates(self) -> None:
        assert percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.5

    def test_q_zero_is_the_minimum(self) -> None:
        assert percentile([4.0, 1.0, 3.0, 2.0], 0) == 1.0

    def test_q_hundred_is_the_maximum(self) -> None:
        assert percentile([4.0, 1.0, 3.0, 2.0], 100) == 4.0

    def test_single_value_returns_that_value_for_any_q(self) -> None:
        assert percentile([7.0], 37) == 7.0

    def test_matches_known_numpy_linear_interpolation_values(self) -> None:
        # numpy.percentile([10, 20, 30, 40, 50], 25) == 20.0 (method="linear", numpy's default).
        assert percentile([10.0, 20.0, 30.0, 40.0, 50.0], 25) == 20.0

    def test_empty_sequence_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="at least one"):
            percentile([], 50)

    def test_q_below_zero_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="0 <= q <= 100"):
            percentile([1.0], -1)

    def test_q_above_hundred_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="0 <= q <= 100"):
            percentile([1.0], 101)


class TestDescribe:
    def test_known_values(self) -> None:
        summary = describe(_series([1.0, 2.0, 3.0]))
        assert isinstance(summary, StatisticalSummary)
        assert summary.n == 3
        assert summary.mean == 2.0
        assert summary.minimum == 1.0
        assert summary.maximum == 3.0
        # Population variance of [1, 2, 3] about mean 2: (1+0+1)/3 = 0.6667.
        assert summary.std == pytest.approx((2.0 / 3.0) ** 0.5)

    def test_default_percentile_keys_are_50_90_99(self) -> None:
        summary = describe(_series([float(i) for i in range(1, 101)]))
        assert set(summary.percentiles) == {50, 90, 99}

    def test_single_point_series(self) -> None:
        summary = describe(_series([5.0]))
        assert summary.n == 1
        assert summary.mean == 5.0
        assert summary.std == 0.0

    def test_empty_series_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="at least one"):
            describe(TimeSeries(points=()))


class TestHistogram:
    def test_equal_width_bins_known_counts(self) -> None:
        result = histogram([1.0, 2.0, 3.0, 4.0], bins=2)
        assert isinstance(result, Histogram)
        assert result.bin_edges == (1.0, 2.5, 4.0)
        assert result.counts == (2, 2)

    def test_every_value_is_counted_exactly_once(self) -> None:
        values = [float(i) for i in range(1, 21)]
        result = histogram(values, bins=4)
        assert sum(result.counts) == len(values)

    def test_caller_supplied_edges(self) -> None:
        result = histogram([1.0, 2.0, 3.0], bins=[1.0, 2.0, 3.0])
        assert result.bin_edges == (1.0, 2.0, 3.0)
        assert result.counts == (1, 2)

    def test_value_exactly_on_an_interior_edge_belongs_to_the_upper_bin(self) -> None:
        result = histogram([0.0, 1.0, 2.0], bins=[0.0, 1.0, 2.0])
        assert result.counts == (1, 2)

    def test_degenerate_all_identical_values(self) -> None:
        """When min == max, equal-width bin edges collapse to a single
        point; every value must still land somewhere, not raise or
        silently vanish."""
        result = histogram([5.0, 5.0, 5.0], bins=3)
        assert sum(result.counts) == 3

    def test_single_bin(self) -> None:
        result = histogram([1.0, 2.0, 3.0], bins=1)
        assert result.bin_edges == (1.0, 3.0)
        assert result.counts == (3,)

    def test_empty_values_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="at least one"):
            histogram([], bins=2)

    def test_bins_less_than_one_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="bins >= 1"):
            histogram([1.0, 2.0], bins=0)

    def test_too_few_explicit_edges_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="at least 2 bin edges"):
            histogram([1.0], bins=[1.0])

    def test_decreasing_explicit_edges_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="non-decreasing"):
            histogram([1.0, 2.0], bins=[2.0, 1.0])


class TestDistribution:
    def test_returns_distribution_summary(self) -> None:
        result = distribution([1.0, 2.0, 3.0, 4.0, 5.0])
        assert isinstance(result, DistributionSummary)
        assert result.mean == 3.0

    def test_symmetric_data_has_zero_skewness(self) -> None:
        result = distribution([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result.skewness == pytest.approx(0.0, abs=1e-9)

    def test_right_skewed_data_has_positive_skewness(self) -> None:
        # Hand-computed: mean=22, population std=sqrt(1522), third moment/n=88920.
        result = distribution([1.0, 2.0, 3.0, 4.0, 100.0])
        assert result.mean == 22.0
        assert result.std == pytest.approx(1522.0**0.5)
        assert result.skewness == pytest.approx(88920.0 / (1522.0**0.5) ** 3)
        assert result.skewness > 0.0

    def test_zero_variance_data_has_zero_skewness_and_kurtosis(self) -> None:
        result = distribution([3.0, 3.0, 3.0])
        assert result.skewness == 0.0
        assert result.kurtosis == 0.0

    def test_default_percentile_keys_are_50_90_99(self) -> None:
        result = distribution([float(i) for i in range(1, 101)])
        assert set(result.percentiles) == {50, 90, 99}

    def test_empty_values_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="at least one"):
            distribution([])


class TestConfidenceInterval:
    def test_returns_confidence_interval_result(self) -> None:
        result = confidence_interval([1.0, 2.0, 3.0, 4.0, 5.0])
        assert isinstance(result, ConfidenceInterval)
        assert result.method == "t"
        assert result.confidence == 0.95

    def test_interval_is_centered_on_the_sample_mean(self) -> None:
        result = confidence_interval([1.0, 2.0, 3.0, 4.0, 5.0], method="normal")
        assert (result.lower + result.upper) / 2 == pytest.approx(3.0)

    def test_normal_matches_known_z_critical_value(self) -> None:
        # 95% normal CI half-width = 1.959964 * sample_std / sqrt(n).
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        n = len(values)
        mean = sum(values) / n
        sample_std = (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5
        expected_margin = 1.9599639845400536 * sample_std / n**0.5
        result = confidence_interval(values, confidence=0.95, method="normal")
        assert result.upper - mean == pytest.approx(expected_margin)

    def test_t_matches_known_t_table_critical_value(self) -> None:
        # t(0.975, df=4) = 2.776 (standard published t-table value).
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        n, mean = len(values), 3.0
        sample_std = (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5
        expected_margin = 2.776 * sample_std / n**0.5
        result = confidence_interval(values, confidence=0.95, method="t")
        assert result.upper - mean == pytest.approx(expected_margin, abs=1e-3)

    def test_t_matches_known_t_table_value_at_a_lower_confidence_level(self) -> None:
        # t(0.90, df=9) = 1.383 -- a different (df, confidence) region of the
        # incomplete-beta computation than the other t-method tests exercise.
        values = [float(i) for i in range(1, 11)]
        n, mean = len(values), sum(values) / 10
        sample_std = (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5
        expected_margin = 1.383 * sample_std / n**0.5
        result = confidence_interval(values, confidence=0.80, method="t")
        assert result.upper - mean == pytest.approx(expected_margin, abs=1e-3)

    def test_t_interval_is_wider_than_normal_for_small_samples(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        normal_result = confidence_interval(values, method="normal")
        t_result = confidence_interval(values, method="t")
        assert (t_result.upper - t_result.lower) > (normal_result.upper - normal_result.lower)

    def test_t_and_normal_converge_for_large_samples(self) -> None:
        values = [float(i) for i in range(1, 1001)]
        normal_result = confidence_interval(values, method="normal")
        t_result = confidence_interval(values, method="t")
        assert t_result.lower == pytest.approx(normal_result.lower, rel=1e-3)
        assert t_result.upper == pytest.approx(normal_result.upper, rel=1e-3)

    def test_empty_values_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="at least one"):
            confidence_interval([])

    def test_single_value_raises_for_either_method(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="at least 2 observations"):
            confidence_interval([1.0], method="t")
        with pytest.raises(AnalyticsValidationError, match="at least 2 observations"):
            confidence_interval([1.0], method="normal")

    def test_confidence_at_or_below_zero_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="0 < confidence < 1"):
            confidence_interval([1.0, 2.0], confidence=0.0)

    def test_confidence_at_or_above_one_raises(self) -> None:
        with pytest.raises(AnalyticsValidationError, match="0 < confidence < 1"):
            confidence_interval([1.0, 2.0], confidence=1.0)
