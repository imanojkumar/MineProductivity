"""Tests for mineproductivity.analytics.result."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.core import BaseValueObject
from mineproductivity.core.serialization import DataclassSerializer, to_dict
from mineproductivity.kpis import Direction

from mineproductivity.analytics.result import (
    AnalyticsResult,
    AnomalyFlag,
    Baseline,
    BenchmarkResult,
    ConfidenceInterval,
    DataQualityScore,
    DistributionSummary,
    ForecastResult,
    Histogram,
    OutlierFlag,
    StatisticalSummary,
    TrendResult,
)
from mineproductivity.analytics.windowing import RollingSpec


class TestAnalyticsResult:
    def test_defaults(self) -> None:
        result = AnalyticsResult()
        assert result.model_code == ""
        assert result.warnings == ()
        assert result.computed_at.tzinfo is not None

    def test_explicit_fields(self) -> None:
        result = AnalyticsResult(model_code="TREND.Linear", warnings=("low n",))
        assert result.model_code == "TREND.Linear"
        assert result.warnings == ("low n",)

    def test_equality_is_value_based(self) -> None:
        now = datetime(2026, 6, 25, tzinfo=timezone.utc)
        first = AnalyticsResult(model_code="TREND.Linear", computed_at=now)
        second = AnalyticsResult(model_code="TREND.Linear", computed_at=now)
        assert first == second


class TestStatisticalSummary:
    def test_construction(self) -> None:
        summary = StatisticalSummary(
            n=3, mean=2.0, std=1.0, minimum=1.0, maximum=3.0, percentiles={50: 2.0}
        )
        assert summary.n == 3
        assert summary.percentiles[50] == 2.0
        assert isinstance(summary, AnalyticsResult)

    def test_percentiles_is_frozen_into_a_read_only_mapping(self) -> None:
        summary = StatisticalSummary(
            n=3, mean=2.0, std=1.0, minimum=1.0, maximum=3.0, percentiles={50: 2.0}
        )
        with pytest.raises(TypeError):
            summary.percentiles[90] = 3.0  # type: ignore[index]


class TestTrendResult:
    def test_construction(self) -> None:
        result = TrendResult(
            slope=1.5,
            intercept=0.0,
            r_squared=0.98,
            direction="increasing",
            window=RollingSpec(periods=7),
        )
        assert result.direction == "increasing"
        assert isinstance(result, AnalyticsResult)


class TestBenchmarkResult:
    def test_construction(self) -> None:
        result = BenchmarkResult(
            kpi_code="PROD.TPH",
            value=1200.0,
            band="top_quartile",
            direction=Direction.HIGHER_IS_BETTER,
        )
        assert result.band == "top_quartile"
        assert isinstance(result, AnalyticsResult)


class TestBaseline:
    def test_construction(self) -> None:
        baseline = Baseline(
            mean=100.0, std=5.0, lower=90.0, upper=110.0, spec=RollingSpec(periods=14)
        )
        assert baseline.lower == 90.0
        assert baseline.upper == 110.0
        assert isinstance(baseline, AnalyticsResult)


class TestDistributionSummary:
    def test_construction(self) -> None:
        dist = DistributionSummary(
            mean=1.0, std=0.5, skewness=0.1, kurtosis=3.0, percentiles={50: 1.0}
        )
        assert dist.skewness == 0.1
        assert isinstance(dist, AnalyticsResult)

    def test_percentiles_is_frozen_into_a_read_only_mapping(self) -> None:
        dist = DistributionSummary(
            mean=1.0, std=0.5, skewness=0.1, kurtosis=3.0, percentiles={50: 1.0}
        )
        with pytest.raises(TypeError):
            dist.percentiles[90] = 3.0  # type: ignore[index]


class TestHistogram:
    def test_construction(self) -> None:
        hist = Histogram(bin_edges=(0.0, 1.0, 2.0), counts=(3, 5))
        assert len(hist.counts) == len(hist.bin_edges) - 1
        assert isinstance(hist, AnalyticsResult)


class TestConfidenceInterval:
    def test_construction(self) -> None:
        ci = ConfidenceInterval(lower=9.5, upper=10.5, confidence=0.95, method="t")
        assert ci.confidence == 0.95
        assert isinstance(ci, AnalyticsResult)


class TestDataQualityScore:
    def test_construction(self) -> None:
        score = DataQualityScore(
            completeness=1.0, validity=0.9, overall_score=0.9, reasons=("2 rows out of range",)
        )
        assert score.overall_score == 0.9
        assert isinstance(score, AnalyticsResult)


class TestForecastResult:
    def test_construction(self) -> None:
        forecast = ForecastResult(
            horizon=1,
            predicted=(105.0,),
            intervals=(
                ConfidenceInterval(lower=100.0, upper=110.0, confidence=0.95, method="normal"),
            ),
        )
        assert forecast.horizon == 1
        assert len(forecast.intervals) == 1
        assert isinstance(forecast, AnalyticsResult)


class TestAnomalyFlag:
    def test_construction(self) -> None:
        flag = AnomalyFlag(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            observed_value=500.0,
            expected_value=100.0,
            severity="high",
        )
        assert flag.severity == "high"

    def test_is_not_an_analytics_result(self) -> None:
        """Deliberate: one flagged observation, not a summary result."""
        assert not issubclass(AnomalyFlag, AnalyticsResult)
        assert issubclass(AnomalyFlag, BaseValueObject)


class TestOutlierFlag:
    def test_construction(self) -> None:
        flag = OutlierFlag(index=42, value=999.0, method_hint="iqr")
        assert flag.method_hint == "iqr"

    def test_is_not_an_analytics_result(self) -> None:
        assert not issubclass(OutlierFlag, AnalyticsResult)
        assert issubclass(OutlierFlag, BaseValueObject)


class TestSerialization:
    """Design spec §30: 'Every result type serializes via
    core.serialization (DataclassSerializer/to_dict) with no bespoke
    per-type serializer.' Confirmed directly here: none of these classes
    defines its own ``to_dict()`` method, so the free ``to_dict()``
    function always takes the generic dataclass-recursion path
    (``_asdict_recursive``), never the ``SupportsToDict`` short-circuit
    -- the same generic mechanism every other domain package's result
    types (e.g. ``kpis.KPIResult``) already rely on."""

    _INSTANCES: tuple[AnalyticsResult | AnomalyFlag | OutlierFlag, ...] = (
        AnalyticsResult(model_code="TREND.Linear", warnings=("low n",)),
        StatisticalSummary(n=3, mean=2.0, std=1.0, minimum=1.0, maximum=3.0, percentiles={50: 2.0}),
        TrendResult(
            slope=1.5,
            intercept=0.0,
            r_squared=0.98,
            direction="increasing",
            window=RollingSpec(periods=7),
        ),
        BenchmarkResult(
            kpi_code="PROD.TPH",
            value=1200.0,
            band="top_quartile",
            direction=Direction.HIGHER_IS_BETTER,
        ),
        Baseline(mean=100.0, std=5.0, lower=90.0, upper=110.0, spec=RollingSpec(periods=14)),
        DistributionSummary(mean=1.0, std=0.5, skewness=0.1, kurtosis=3.0, percentiles={50: 1.0}),
        Histogram(bin_edges=(0.0, 1.0, 2.0), counts=(3, 5)),
        ConfidenceInterval(lower=9.5, upper=10.5, confidence=0.95, method="t"),
        DataQualityScore(
            completeness=1.0, validity=0.9, overall_score=0.9, reasons=("2 rows out of range",)
        ),
        ForecastResult(
            horizon=1,
            predicted=(105.0,),
            intervals=(
                ConfidenceInterval(lower=100.0, upper=110.0, confidence=0.95, method="normal"),
            ),
        ),
        AnomalyFlag(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            observed_value=500.0,
            expected_value=100.0,
            severity="high",
        ),
        OutlierFlag(index=42, value=999.0, method_hint="iqr"),
    )

    @pytest.mark.parametrize("instance", _INSTANCES)
    def test_to_dict_works_generically_for_every_result_type(
        self, instance: AnalyticsResult | AnomalyFlag | OutlierFlag
    ) -> None:
        data = to_dict(instance)
        assert isinstance(data, dict)
        assert data

    @pytest.mark.parametrize("instance", _INSTANCES)
    def test_no_result_type_defines_its_own_to_dict_method(
        self, instance: AnalyticsResult | AnomalyFlag | OutlierFlag
    ) -> None:
        assert "to_dict" not in type(instance).__dict__


class TestDataclassSerializerRoundTrip:
    """Round-trips flat (no nested-dataclass-field) result types through
    ``DataclassSerializer`` -- ``deserialize`` reconstructs via
    ``target_type(**data)`` directly (its own docstring's ``Point``
    example), which is correct for a flat dataclass but would pass a
    plain ``dict`` where a nested-dataclass field (e.g.
    ``TrendResult.window: RollingSpec``) expects a ``RollingSpec``
    instance -- that one-level scope is a property of
    ``DataclassSerializer`` itself (design spec §30 does not ask for
    deep reconstruction), not something this package works around."""

    def test_analytics_result_round_trips(self) -> None:
        serializer = DataclassSerializer(AnalyticsResult)
        original = AnalyticsResult(model_code="TREND.Linear", warnings=("low n",))
        assert serializer.deserialize(serializer.serialize(original)) == original

    def test_statistical_summary_round_trips(self) -> None:
        serializer = DataclassSerializer(StatisticalSummary)
        original = StatisticalSummary(
            n=3, mean=2.0, std=1.0, minimum=1.0, maximum=3.0, percentiles={50: 2.0, 90: 2.8}
        )
        assert serializer.deserialize(serializer.serialize(original)) == original

    def test_benchmark_result_round_trips(self) -> None:
        serializer = DataclassSerializer(BenchmarkResult)
        original = BenchmarkResult(
            kpi_code="PROD.TPH",
            value=1200.0,
            band="top_quartile",
            direction=Direction.HIGHER_IS_BETTER,
        )
        assert serializer.deserialize(serializer.serialize(original)) == original
