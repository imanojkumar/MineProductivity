"""Tests for mineproductivity.analytics.benchmarking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.kpis import Direction, KPIMetadata, KPIResult
from mineproductivity.registry import Registry

from mineproductivity.analytics._registry import REGISTRY
from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.benchmarking import BandBenchmarkModel, BenchmarkModel
from mineproductivity.analytics.metadata import AnalyticsCategory
from mineproductivity.analytics.result import AnalyticsResult, BenchmarkResult
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _metadata(**overrides: object) -> KPIMetadata:
    fields: dict[str, object] = {
        "code": "PROD.TestKpi",
        "name": "Test KPI",
        "official_name": "Test KPI",
        "business_purpose": "x",
        "operational_question": "x",
        "business_meaning": "x",
        "formula": "x",
        "unit": "t/h",
        "dimensions": ("Shift",),
        "required_events": ("CYCLE",),
        "direction": Direction.HIGHER_IS_BETTER,
        "benchmark_bands": {},
    }
    fields.update(overrides)
    return KPIMetadata(**fields)  # type: ignore[arg-type]


def _registry(metadata: KPIMetadata | None = None) -> Registry[str, type]:
    reg: Registry[str, type] = Registry(name="test-benchmarking")
    if metadata is not None:
        result = reg.register(metadata.code, object, metadata=metadata)
        assert result.is_ok
    return reg


def _context() -> AnalyticsContext:
    return AnalyticsContext(event_store=_InMemoryEventStore())


class TestBenchmarkModelIsAbstract:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BenchmarkModel()  # type: ignore[abstract]

    def test_is_an_analytics_model(self) -> None:
        assert issubclass(BenchmarkModel, AnalyticsModel)


class TestBandBenchmarkModelMetadata:
    def test_code_is_benchmark_band(self) -> None:
        assert BandBenchmarkModel.meta.code == "BENCHMARK.Band"

    def test_category_is_benchmark(self) -> None:
        assert BandBenchmarkModel.meta.category is AnalyticsCategory.BENCHMARK

    def test_is_a_benchmark_model(self) -> None:
        assert issubclass(BandBenchmarkModel, BenchmarkModel)

    def test_description_is_non_empty(self) -> None:
        assert BandBenchmarkModel.meta.description

    def test_repr_includes_kpi_code(self) -> None:
        model = BandBenchmarkModel(kpi_code="PROD.TPH")
        assert "PROD.TPH" in repr(model)


class TestBandBenchmarkModelIsRegistered:
    def test_code_is_in_the_registry(self) -> None:
        assert "BENCHMARK.Band" in REGISTRY

    def test_registry_get_returns_this_class(self) -> None:
        assert REGISTRY.get("BENCHMARK.Band") is BandBenchmarkModel

    def test_registry_metadata_matches_the_class_own_meta(self) -> None:
        assert REGISTRY.metadata_for("BENCHMARK.Band").unwrap() is BandBenchmarkModel.meta


class TestHigherIsBetter:
    def test_value_above_threshold_matches_top_band(self) -> None:
        metadata = _metadata(
            direction=Direction.HIGHER_IS_BETTER,
            benchmark_bands={"top_quartile": ">1200", "below_average": "<1000"},
        )
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=1250.0, unit="t/h")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == "top_quartile"
        assert classified.value == 1250.0
        assert classified.kpi_code == "PROD.TestKpi"
        assert classified.direction is Direction.HIGHER_IS_BETTER

    def test_value_below_threshold_matches_below_average(self) -> None:
        metadata = _metadata(
            direction=Direction.HIGHER_IS_BETTER,
            benchmark_bands={"top_quartile": ">1200", "below_average": "<1000"},
        )
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=900.0, unit="t/h")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == "below_average"


class TestLowerIsBetter:
    def test_direction_inverts_the_comparison(self) -> None:
        """For LOWER_IS_BETTER, a band authored as '<50' means 'this band
        applies when the value is *greater than* 50' -- the comparison is
        inverted relative to a HIGHER_IS_BETTER KPI using the same
        expression (design spec §13)."""
        metadata = _metadata(
            direction=Direction.LOWER_IS_BETTER,
            benchmark_bands={"excellent": "<50", "poor": ">100"},
        )
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")

        # value=30: inverted "<50" -> ">50" (False); inverted ">100" -> "<100" (True) -> "poor"
        low_value = KPIResult(code="PROD.TestKpi", value=30.0, unit="t/h")
        classified = model.benchmark(low_value, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == "poor"

        # value=150: inverted "<50" -> ">50" (True) -> "excellent"
        high_value = KPIResult(code="PROD.TestKpi", value=150.0, unit="t/h")
        classified_high = model.benchmark(high_value, registry=registry)
        assert isinstance(classified_high, BenchmarkResult)
        assert classified_high.band == "excellent"

    def test_direction_is_preserved_on_the_result(self) -> None:
        metadata = _metadata(
            direction=Direction.LOWER_IS_BETTER, benchmark_bands={"excellent": "<50"}
        )
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=200.0, unit="t/h")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.direction is Direction.LOWER_IS_BETTER


class TestTargetIsBest:
    def test_value_near_target_matches_near_target_band(self) -> None:
        metadata = _metadata(
            direction=Direction.TARGET_IS_BEST,
            benchmark_bands={"target": "100", "near_target": "<=10", "off_target": ">10"},
        )
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=105.0, unit="t")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == "near_target"

    def test_value_far_from_target_matches_off_target_band(self) -> None:
        metadata = _metadata(
            direction=Direction.TARGET_IS_BEST,
            benchmark_bands={"target": "100", "near_target": "<=10", "off_target": ">10"},
        )
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=50.0, unit="t")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == "off_target"

    def test_missing_target_entry_yields_a_warning_result(self) -> None:
        metadata = _metadata(
            direction=Direction.TARGET_IS_BEST, benchmark_bands={"near_target": "<=10"}
        )
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=100.0, unit="t")

        classified = model.benchmark(result, registry=registry)
        assert type(classified) is AnalyticsResult
        assert "target" in classified.warnings[0]

    def test_non_numeric_target_entry_yields_a_warning_result(self) -> None:
        metadata = _metadata(
            direction=Direction.TARGET_IS_BEST, benchmark_bands={"target": "not-a-number"}
        )
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=100.0, unit="t")

        classified = model.benchmark(result, registry=registry)
        assert type(classified) is AnalyticsResult
        assert classified.warnings

    def test_target_only_with_no_distance_bands_is_unclassified_with_a_warning(self) -> None:
        """A ``target`` entry with no accompanying distance bands is a
        legitimate, if unusual, configuration -- classification degrades
        to an empty ``band`` with a warning, never a crash."""
        metadata = _metadata(direction=Direction.TARGET_IS_BEST, benchmark_bands={"target": "100"})
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=105.0, unit="t")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == ""
        assert classified.warnings


class TestBoundaryValues:
    def test_value_exactly_on_a_strict_greater_than_boundary_does_not_match(self) -> None:
        metadata = _metadata(benchmark_bands={"top_quartile": ">1200"})
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=1200.0, unit="t/h")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == ""

    def test_value_exactly_on_a_greater_or_equal_boundary_matches(self) -> None:
        metadata = _metadata(benchmark_bands={"top_quartile": ">=1200"})
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=1200.0, unit="t/h")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == "top_quartile"


class TestInsideAndOutsideBand:
    def test_value_inside_a_band_is_classified(self) -> None:
        metadata = _metadata(benchmark_bands={"good": ">0.9"})
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=0.95, unit="ratio")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == "good"

    def test_value_outside_every_band_is_unclassified_with_a_warning(self) -> None:
        metadata = _metadata(benchmark_bands={"good": ">0.9"})
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=0.5, unit="ratio")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == ""
        assert classified.warnings

    def test_an_unparseable_band_expression_is_skipped_not_raised(self) -> None:
        """A malformed ``benchmark_bands`` entry (e.g. authored free text)
        must not crash classification -- it is simply never matched,
        the same "qualify, don't coerce" rule governing every other
        degenerate case in this module."""
        metadata = _metadata(benchmark_bands={"unparseable": "roughly nine tenths", "good": ">0.9"})
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=0.95, unit="ratio")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == "good"


class TestMissingBenchmarkBands:
    def test_empty_bands_yields_a_benchmark_result_with_empty_band_and_warning(self) -> None:
        metadata = _metadata(benchmark_bands={})
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=42.0, unit="t/h")

        classified = model.benchmark(result, registry=registry)
        assert isinstance(classified, BenchmarkResult)
        assert classified.band == ""
        assert classified.value == 42.0
        assert "benchmark bands" in classified.warnings[0]


class TestMissingMetadata:
    def test_unregistered_kpi_code_yields_a_bare_analytics_result(self) -> None:
        registry = _registry(None)
        model = BandBenchmarkModel(kpi_code="PROD.NotRegistered")
        result = KPIResult(code="PROD.NotRegistered", value=1.0, unit="x")

        classified = model.benchmark(result, registry=registry)
        assert type(classified) is AnalyticsResult
        assert not isinstance(classified, BenchmarkResult)
        assert "no registered KPI metadata" in classified.warnings[0]


class TestNoneValue:
    def test_uncomputable_kpi_result_yields_a_bare_analytics_result(self) -> None:
        metadata = _metadata(benchmark_bands={"good": ">0.9"})
        registry = _registry(metadata)
        model = BandBenchmarkModel(kpi_code="PROD.TestKpi")
        result = KPIResult(code="PROD.TestKpi", value=None, unit="ratio")

        classified = model.benchmark(result, registry=registry)
        assert type(classified) is AnalyticsResult
        assert not isinstance(classified, BenchmarkResult)
        assert classified.warnings


class TestRegistryLookup:
    def test_uses_the_explicitly_passed_registry_not_the_global_one(self) -> None:
        """A code registered in a throwaway ``Registry`` must not be
        found via a different, unrelated registry instance."""
        metadata = _metadata(code="PROD.LocalOnly", benchmark_bands={"good": ">0.9"})
        local_registry = _registry(metadata)
        other_registry: Registry[str, type] = Registry(name="other")
        model = BandBenchmarkModel(kpi_code="PROD.LocalOnly")
        result = KPIResult(code="PROD.LocalOnly", value=1.0, unit="ratio")

        assert isinstance(model.benchmark(result, registry=local_registry), BenchmarkResult)
        found_in_other = model.benchmark(result, registry=other_registry)
        assert type(found_in_other) is AnalyticsResult


class TestMetadataValidation:
    def test_kpimetadata_rejects_a_blank_official_name(self) -> None:
        with pytest.raises(Exception):
            _metadata(official_name="")

    def test_benchmark_bands_is_frozen_into_a_read_only_mapping(self) -> None:
        metadata = _metadata(benchmark_bands={"good": ">0.9"})
        with pytest.raises(TypeError):
            metadata.benchmark_bands["bad"] = "x"  # type: ignore[index]


class TestAnalyzeAdapter:
    def test_analyze_benchmarks_the_last_point_via_the_global_registry(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``_analyze`` bridges a bare ``TimeSeries`` (which carries no
        KPI code) to ``benchmark`` by using the constructor-supplied
        ``kpi_code`` and the module-level ``kpis.REGISTRY``.

        ``Registry`` is add-only/global with no unregister, so this test
        monkeypatches ``benchmarking.REGISTRY`` to a throwaway instance
        rather than polluting the real, process-wide ``kpis.REGISTRY``
        singleton every other test module also iterates."""
        code = "PROD.BenchmarkAnalyzeAdapter"
        fake_registry: Registry[str, type] = Registry(name="fake-global")
        metadata = _metadata(code=code, benchmark_bands={"top_quartile": ">1200"})
        registration = fake_registry.register(code, object, metadata=metadata)
        assert registration.is_ok
        monkeypatch.setattr("mineproductivity.analytics.benchmarking.REGISTRY", fake_registry)

        series = TimeSeries(
            points=(
                TimeSeriesPoint(timestamp=DAY_1, value=100.0),
                TimeSeriesPoint(timestamp=DAY_1 + timedelta(days=1), value=1250.0),
            )
        )
        model = BandBenchmarkModel(kpi_code=code)
        result = model.analyze(series, context=_context())
        assert isinstance(result, BenchmarkResult)
        assert result.value == 1250.0  # the *last* point, not the first
        assert result.band == "top_quartile"

    def test_analyze_is_an_analyticsmodel_contract_method(self) -> None:
        model = BandBenchmarkModel(kpi_code="PROD.AnyCode")
        assert isinstance(model, AnalyticsModel)


class TestPublicApiValidation:
    def test_benchmarkmodel_and_bandbenchmarkmodel_are_exported(self) -> None:
        import mineproductivity.analytics as analytics

        assert "BenchmarkModel" in analytics.__all__
        assert "BandBenchmarkModel" in analytics.__all__
        assert analytics.BenchmarkModel is BenchmarkModel
        assert analytics.BandBenchmarkModel is BandBenchmarkModel
