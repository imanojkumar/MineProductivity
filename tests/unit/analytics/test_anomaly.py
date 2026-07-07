"""Tests for mineproductivity.analytics.anomaly.

Per design spec §35's testing philosophy for interface-only modules:
``AnomalyDetector`` is tested only for its ABC contract (bare-ABC
instantiation raises ``TypeError``; a minimal test-only concrete
subclass satisfies the abstract method signatures) -- there is no
algorithmic-correctness test, since this package ships no
anomaly-detection algorithm.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import ClassVar

import pytest

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.anomaly import AnomalyDetector
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.result import AnalyticsResult, AnomalyFlag, Baseline
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.windowing import RollingSpec

from .conftest import assert_stub_method_body

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


def _series() -> TimeSeries:
    return TimeSeries(
        points=(
            TimeSeriesPoint(timestamp=DAY_1, value=10.0),
            TimeSeriesPoint(timestamp=DAY_1, value=500.0),
        )
    )


def _baseline() -> Baseline:
    return Baseline(mean=10.0, std=1.0, lower=8.0, upper=12.0, spec=RollingSpec(periods=5))


class _FakeAnomalyDetector(AnomalyDetector):
    """Minimal, test-only concrete subclass satisfying both abstract
    methods -- not a shipped algorithm, purely a contract-conformance
    fixture (design spec §35)."""

    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="ANOMALY.Fake",
        category=AnalyticsCategory.ANOMALY,
        description="Test-only fixture satisfying the AnomalyDetector contract.",
        min_observations=0,
    )

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        flags = self._detect(series, baseline=None, context=context)
        return AnalyticsResult(
            model_code=self.meta.code, warnings=(f"{len(flags)} anomalies flagged",)
        )

    def _detect(
        self, series: TimeSeries, *, baseline: Baseline | None, context: AnalyticsContext
    ) -> tuple[AnomalyFlag, ...]:
        expected = baseline.mean if baseline is not None else None
        return tuple(
            AnomalyFlag(
                timestamp=point.timestamp,
                observed_value=point.value,
                expected_value=expected,
                severity="high" if expected is not None and point.value > expected * 10 else "low",
            )
            for point in series.points
        )


class TestAnomalyDetectorIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            AnomalyDetector()  # type: ignore[abstract]

    def test_is_an_analytics_model(self) -> None:
        assert issubclass(AnomalyDetector, AnalyticsModel)

    def test_both_analyze_and_detect_remain_abstract(self) -> None:
        """``AnomalyDetector`` does not override ``_analyze`` -- exactly
        like every other category base in this package (``TrendModel``,
        ``BaselineModel``, ``BenchmarkModel``, ``ForecastingModel``),
        leaving that decision to a concrete subclass. No concrete
        subclass ships here."""
        assert AnomalyDetector.__abstractmethods__ == frozenset({"_analyze", "_detect"})

    def test_detect_is_the_only_new_abstract_method(self) -> None:
        assert "_detect" in AnomalyDetector.__dict__
        assert getattr(AnomalyDetector._detect, "__isabstractmethod__", False)


class TestConcreteSubclassSatisfiesContract:
    def test_a_minimal_subclass_can_be_instantiated(self) -> None:
        detector = _FakeAnomalyDetector()
        assert isinstance(detector, AnomalyDetector)

    def test_detect_returns_a_sequence_of_anomalyflags(self) -> None:
        detector = _FakeAnomalyDetector()
        flags = detector._detect(_series(), baseline=None, context=_context())
        assert len(flags) == 2
        assert all(isinstance(flag, AnomalyFlag) for flag in flags)

    def test_detect_accepts_an_explicit_baseline_reference(self) -> None:
        """``baseline`` reuses the existing ``Baseline`` result type
        (produced by ``baseline.py``'s ``RollingBaselineModel``) rather
        than a new reference shape -- design spec §18's own point."""
        detector = _FakeAnomalyDetector()
        flags = detector._detect(_series(), baseline=_baseline(), context=_context())
        assert flags[0].expected_value == 10.0
        assert flags[0].severity == "low"
        assert flags[1].severity == "high"  # 500.0 >> 10.0 * 10

    def test_detect_accepts_baseline_none(self) -> None:
        """``baseline`` is optional -- a future detector may compute its
        own reference internally."""
        detector = _FakeAnomalyDetector()
        flags = detector._detect(_series(), baseline=None, context=_context())
        assert all(flag.expected_value is None for flag in flags)

    def test_analyze_orchestration_still_applies(self) -> None:
        """``AnalyticsModel.analyze()``'s generic min_observations gate
        still governs an ``AnomalyDetector`` subclass exactly as it
        governs every other concrete model in this package."""
        detector = _FakeAnomalyDetector()
        result = detector.analyze(_series(), context=_context())
        assert isinstance(result, AnalyticsResult)
        assert "2 anomalies flagged" in result.warnings[0]

    def test_insufficient_data_short_circuits_before_detect_is_called(self) -> None:
        class _StrictFakeDetector(_FakeAnomalyDetector):
            meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
                code="ANOMALY.Strict",
                category=AnalyticsCategory.ANOMALY,
                description="x",
                min_observations=5,
            )

        result = _StrictFakeDetector().analyze(_series(), context=_context())
        assert type(result) is AnalyticsResult
        assert "insufficient data" in result.warnings[0]


class TestInterfacePurity:
    """Design spec §35's own "interface-purity proof": zero concrete,
    non-test subclasses of ``AnomalyDetector`` ship inside ``anomaly.py``
    itself (checklist §18 line item)."""

    def test_anomaly_module_defines_no_concrete_subclass(self) -> None:
        import mineproductivity.analytics.anomaly as anomaly_module

        concrete_subclasses = [
            member
            for _, member in inspect.getmembers(anomaly_module, inspect.isclass)
            if issubclass(member, AnomalyDetector)
            and member is not AnomalyDetector
            and not inspect.isabstract(member)
        ]
        assert concrete_subclasses == []

    def test_anomalydetector_itself_is_the_only_class_defined_in_the_module(self) -> None:
        import mineproductivity.analytics.anomaly as anomaly_module

        classes_defined_here = [
            name
            for name, member in inspect.getmembers(anomaly_module, inspect.isclass)
            if member.__module__ == anomaly_module.__name__
        ]
        assert classes_defined_here == ["AnomalyDetector"]

    def test_no_algorithmic_behavior_beyond_orchestration(self) -> None:
        """The abstract method's body is a docstring only -- no
        computation, branching, or return of any kind is embedded in
        the interface itself."""
        assert_stub_method_body(AnomalyDetector._detect)


class TestPublicApiValidation:
    def test_anomalydetector_is_exported(self) -> None:
        import mineproductivity.analytics as analytics

        assert "AnomalyDetector" in analytics.__all__
        assert analytics.AnomalyDetector is AnomalyDetector

    def test_anomalyflag_and_baseline_are_reused_not_duplicated(self) -> None:
        """No new result type was introduced -- ``AnomalyFlag`` and
        ``Baseline`` already existed in ``result.py`` since the
        Foundation/Baseline phases."""
        import mineproductivity.analytics.result as result_module

        assert AnomalyFlag.__module__ == result_module.__name__
        assert Baseline.__module__ == result_module.__name__

    def test_anomaly_module_public_api_matches_spec_exactly(self) -> None:
        import mineproductivity.analytics.anomaly as anomaly_module

        assert anomaly_module.__all__ == ["AnomalyDetector"]
