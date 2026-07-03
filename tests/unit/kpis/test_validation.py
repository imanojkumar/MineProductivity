"""Tests for mineproductivity.kpis.validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis._registry import REGISTRY
from mineproductivity.kpis.categories.utilization_kpi import UtilizationKPI
from mineproductivity.kpis.composite import CompositeKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata
from mineproductivity.kpis.result import KPIResult
from mineproductivity.kpis.validation import CANONICAL_TIME_MODEL_TERMS, KPIValidator


def _util_meta(formula: str, aggregation: Aggregation = Aggregation.RATIO) -> KPIMetadata:
    return KPIMetadata(
        code="UTIL.ValidatorFixture",
        name="x",
        official_name="x",
        business_purpose="x",
        operational_question="x",
        business_meaning="x",
        formula=formula,
        unit="ratio",
        dimensions=("Shift",),
        required_events=("MAINTENANCE",),
        aggregation=aggregation,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L1_MANUAL,
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
    )


class TestCanonicalTimeModelTerms:
    def test_contains_the_full_ladder(self) -> None:
        assert CANONICAL_TIME_MODEL_TERMS == (
            "scheduled_h",
            "available_h",
            "operating_h",
            "calendar_h",
        )


class TestUtilizationKPIFormulaCheck:
    def test_formula_referencing_the_time_model_passes(self) -> None:
        class _GoodUtil(UtilizationKPI):
            meta: ClassVar[KPIMetadata] = _util_meta("available_h / scheduled_h")

            def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
                return None

        result = KPIValidator().validate(_GoodUtil)
        assert result.is_valid

    def test_formula_without_any_time_model_term_fails(self) -> None:
        class _BadUtil(UtilizationKPI):
            meta: ClassVar[KPIMetadata] = _util_meta("made_up_numerator / made_up_denominator")

            def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
                return None

        result = KPIValidator().validate(_BadUtil)
        assert not result.is_valid
        assert "time-model ladder" in result.errors[0]

    def test_non_utilization_kpi_is_not_subject_to_the_time_model_check(self) -> None:
        from mineproductivity.kpis.categories.production_kpi import ProductionKPI

        class _NotUtil(ProductionKPI):
            meta: ClassVar[KPIMetadata] = _util_meta("anything").replace(
                code="PROD.ValidatorFixture", aggregation=Aggregation.ADDITIVE
            )

            def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
                return None

        result = KPIValidator().validate(_NotUtil)
        assert result.is_valid


class TestDerivedReservedForComposite:
    def test_derived_aggregation_on_a_non_composite_fails(self) -> None:
        class _BadDerived(UtilizationKPI):
            meta: ClassVar[KPIMetadata] = _util_meta(
                "scheduled_h based", aggregation=Aggregation.DERIVED
            )

            def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
                return None

        result = KPIValidator().validate(_BadDerived)
        assert not result.is_valid
        assert any("DERIVED" in error for error in result.errors)

    def test_derived_aggregation_on_a_composite_passes_that_specific_check(self) -> None:
        class _GoodDerived(UtilizationKPI, CompositeKPI):
            meta: ClassVar[KPIMetadata] = _util_meta(
                "scheduled_h based", aggregation=Aggregation.DERIVED
            ).replace(dependencies=("UTIL.PA",))

            def _combine(self, component_results: Mapping[str, KPIResult]) -> float | None:
                return None

        result = KPIValidator().validate(_GoodDerived)
        assert result.is_valid


class TestCompositeRequiresDependencies:
    def test_composite_with_no_dependencies_fails(self) -> None:
        class _EmptyComposite(UtilizationKPI, CompositeKPI):
            meta: ClassVar[KPIMetadata] = _util_meta(
                "scheduled_h based", aggregation=Aggregation.DERIVED
            )

            def _combine(self, component_results: Mapping[str, KPIResult]) -> float | None:
                return None

        result = KPIValidator().validate(_EmptyComposite)
        assert not result.is_valid
        assert any("at least one dependency" in error for error in result.errors)


class TestRealStandardLibraryPasses:
    def test_every_registered_kpi_passes_validation(self) -> None:
        validator = KPIValidator()
        for code in REGISTRY:
            kpi_cls = REGISTRY.get(code)
            result = validator.validate(kpi_cls)
            assert result.is_valid, f"{code}: {result.errors}"
