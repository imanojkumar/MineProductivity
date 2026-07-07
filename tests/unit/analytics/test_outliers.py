"""Tests for mineproductivity.analytics.outliers.

Per design spec §35's testing philosophy for interface-only modules:
``OutlierDetector`` is tested only for its ABC contract (bare-ABC
instantiation raises ``TypeError``; a minimal test-only concrete
subclass satisfies the abstract method signatures) -- there is no
algorithmic-correctness test, since this package ships no
outlier-detection algorithm.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import ClassVar

import pytest

from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.outliers import OutlierDetector
from mineproductivity.analytics.result import AnalyticsResult, DistributionSummary, OutlierFlag
from mineproductivity.analytics.statistics import distribution
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

from .conftest import assert_stub_method_body

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


def _series() -> TimeSeries:
    return TimeSeries(
        points=(
            TimeSeriesPoint(timestamp=DAY_1, value=10.0),
            TimeSeriesPoint(timestamp=DAY_1, value=11.0),
            TimeSeriesPoint(timestamp=DAY_1, value=9.0),
            TimeSeriesPoint(timestamp=DAY_1, value=500.0),
        )
    )


class _FakeOutlierDetector(OutlierDetector):
    """Minimal, test-only concrete subclass satisfying both abstract
    methods -- not a shipped algorithm, purely a contract-conformance
    fixture (design spec §35). Reuses ``statistics.distribution()``
    (rather than hand-crafting a fake ``DistributionSummary``) to
    demonstrate the exact composition design spec §18/§19 describe:
    a future detector is built on primitives this package already
    ships."""

    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="OUTLIER.Fake",
        category=AnalyticsCategory.OUTLIER,
        description="Test-only fixture satisfying the OutlierDetector contract.",
        min_observations=0,
    )

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        summary = distribution(series.values())
        flags = self._detect(series, distribution=summary, context=context)
        return AnalyticsResult(
            model_code=self.meta.code, warnings=(f"{len(flags)} outliers flagged",)
        )

    def _detect(
        self, series: TimeSeries, *, distribution: DistributionSummary, context: AnalyticsContext
    ) -> tuple[OutlierFlag, ...]:
        threshold = distribution.mean + 3 * distribution.std
        return tuple(
            OutlierFlag(index=index, value=point.value, method_hint="z-score")
            for index, point in enumerate(series.points)
            if point.value > threshold
        )


class TestOutlierDetectorIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            OutlierDetector()  # type: ignore[abstract]

    def test_is_an_analytics_model(self) -> None:
        assert issubclass(OutlierDetector, AnalyticsModel)

    def test_both_analyze_and_detect_remain_abstract(self) -> None:
        """``OutlierDetector`` does not override ``_analyze`` -- exactly
        like every other category base in this package (``TrendModel``,
        ``BaselineModel``, ``BenchmarkModel``, ``ForecastingModel``,
        ``AnomalyDetector``), leaving that decision to a concrete
        subclass. No concrete subclass ships here."""
        assert OutlierDetector.__abstractmethods__ == frozenset({"_analyze", "_detect"})

    def test_detect_is_the_only_new_abstract_method(self) -> None:
        assert "_detect" in OutlierDetector.__dict__
        assert getattr(OutlierDetector._detect, "__isabstractmethod__", False)


class TestConcreteSubclassSatisfiesContract:
    def test_a_minimal_subclass_can_be_instantiated(self) -> None:
        detector = _FakeOutlierDetector()
        assert isinstance(detector, OutlierDetector)

    def test_detect_returns_a_sequence_of_outlierflags(self) -> None:
        """Uses a hand-authored ``DistributionSummary`` (mean=10, std=1)
        rather than one derived from ``_series()`` itself -- deriving it
        from the same small, skewed sample would make the 500.0 point
        pull the mean/std up enough to mask itself, which is a
        small-sample statistics quirk unrelated to what this test is
        actually verifying: that ``_detect`` returns well-shaped
        ``OutlierFlag`` instances. No claim is made about detection
        *correctness* -- per §35, this package ships no algorithm."""
        detector = _FakeOutlierDetector()
        summary = DistributionSummary(
            mean=10.0, std=1.0, skewness=0.0, kurtosis=3.0, percentiles={50: 10.0}
        )
        flags = detector._detect(_series(), distribution=summary, context=_context())
        assert all(isinstance(flag, OutlierFlag) for flag in flags)
        assert any(flag.index == 3 for flag in flags)  # 500.0 > 10.0 + 3*1.0

    def test_distribution_parameter_is_mandatory_not_optional(self) -> None:
        """Distinct from ``AnomalyDetector._detect``'s optional
        ``baseline`` -- design spec §19's own signature has no
        ``| None`` on ``distribution``. Confirmed via the live type hint
        rather than merely by convention."""
        hints = inspect.signature(OutlierDetector._detect).parameters
        assert hints["distribution"].annotation == "DistributionSummary"
        assert hints["distribution"].default is inspect.Parameter.empty

    def test_analyze_orchestration_still_applies(self) -> None:
        """``AnalyticsModel.analyze()``'s generic min_observations gate
        still governs an ``OutlierDetector`` subclass exactly as it
        governs every other concrete model in this package. The exact
        flagged count is not asserted here (that would be an
        algorithmic-correctness claim, out of scope per §35) -- only
        that orchestration produces a well-formed result."""
        detector = _FakeOutlierDetector()
        result = detector.analyze(_series(), context=_context())
        assert isinstance(result, AnalyticsResult)
        assert "outliers flagged" in result.warnings[0]

    def test_insufficient_data_short_circuits_before_detect_is_called(self) -> None:
        class _StrictFakeDetector(_FakeOutlierDetector):
            meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
                code="OUTLIER.Strict",
                category=AnalyticsCategory.OUTLIER,
                description="x",
                min_observations=5,
            )

        result = _StrictFakeDetector().analyze(_series(), context=_context())
        assert type(result) is AnalyticsResult
        assert "insufficient data" in result.warnings[0]


class TestInterfacePurity:
    """Design spec §35's own "interface-purity proof": zero concrete,
    non-test subclasses of ``OutlierDetector`` ship inside
    ``outliers.py`` itself (checklist §19 line item)."""

    def test_outliers_module_defines_no_concrete_subclass(self) -> None:
        import mineproductivity.analytics.outliers as outliers_module

        concrete_subclasses = [
            member
            for _, member in inspect.getmembers(outliers_module, inspect.isclass)
            if issubclass(member, OutlierDetector)
            and member is not OutlierDetector
            and not inspect.isabstract(member)
        ]
        assert concrete_subclasses == []

    def test_outlierdetector_itself_is_the_only_class_defined_in_the_module(self) -> None:
        import mineproductivity.analytics.outliers as outliers_module

        classes_defined_here = [
            name
            for name, member in inspect.getmembers(outliers_module, inspect.isclass)
            if member.__module__ == outliers_module.__name__
        ]
        assert classes_defined_here == ["OutlierDetector"]

    def test_no_algorithmic_behavior_beyond_orchestration(self) -> None:
        """The abstract method's body is a docstring only -- no
        computation, branching, or return of any kind is embedded in
        the interface itself."""
        assert_stub_method_body(OutlierDetector._detect)


class TestPublicApiValidation:
    def test_outlierdetector_is_exported(self) -> None:
        import mineproductivity.analytics as analytics

        assert "OutlierDetector" in analytics.__all__
        assert analytics.OutlierDetector is OutlierDetector

    def test_outlierflag_and_distributionsummary_are_reused_not_duplicated(self) -> None:
        """No new result type was introduced -- ``OutlierFlag`` and
        ``DistributionSummary`` already existed in ``result.py`` since
        the Foundation phase; ``distribution()`` already existed in
        ``statistics.py`` since the Statistical Primitives phase."""
        import mineproductivity.analytics.result as result_module
        import mineproductivity.analytics.statistics as statistics_module

        assert OutlierFlag.__module__ == result_module.__name__
        assert DistributionSummary.__module__ == result_module.__name__
        assert distribution.__module__ == statistics_module.__name__

    def test_outliers_module_public_api_matches_spec_exactly(self) -> None:
        import mineproductivity.analytics.outliers as outliers_module

        assert outliers_module.__all__ == ["OutlierDetector"]
