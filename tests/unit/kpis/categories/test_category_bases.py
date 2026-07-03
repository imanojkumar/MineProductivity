"""Tests for the nine KPI category base classes
(mineproductivity.kpis.categories.*)."""

from __future__ import annotations

import pytest

from mineproductivity.kpis.categories import (
    CostKPI,
    DelayKPI,
    EnergyKPI,
    HaulageKPI,
    MaintenanceKPI,
    ProductionKPI,
    QualityKPI,
    SafetyKPI,
    UtilizationKPI,
)
from mineproductivity.kpis.exceptions import KPIValidationError
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata


def _meta(code: str) -> KPIMetadata:
    return KPIMetadata(
        code=code,
        name=code,
        official_name=code,
        business_purpose="x",
        operational_question="x",
        business_meaning="x",
        formula="x",
        unit="x",
        dimensions=("Shift",),
        required_events=("CYCLE",),
        aggregation=Aggregation.ADDITIVE,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L1_MANUAL,
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
    )


CATEGORY_CASES = [
    (ProductionKPI, "PROD.Fixture", "UTIL.Fixture"),
    (UtilizationKPI, "UTIL.Fixture", "PROD.Fixture"),
    (MaintenanceKPI, "MAINT.Fixture", "PROD.Fixture"),
    (HaulageKPI, "HAUL.Fixture", "PROD.Fixture"),
    (DelayKPI, "DISP.Fixture", "PROD.Fixture"),
    (CostKPI, "COST.Fixture", "PROD.Fixture"),
]

MULTI_NAMESPACE_CATEGORY_CASES = [
    (EnergyKPI, ["ENERGY.Fixture", "CARBON.Fixture", "WATER.Fixture"], "PROD.Fixture"),
    (QualityKPI, ["QUAL.Fixture", "GRADE.Fixture"], "PROD.Fixture"),
    (SafetyKPI, ["SAFE.Fixture", "AUTO.Fixture"], "PROD.Fixture"),
]


class TestSingleNamespaceCategories:
    @pytest.mark.parametrize(("base", "good_code", "bad_code"), CATEGORY_CASES)
    def test_matching_code_is_accepted(self, base: type, good_code: str, bad_code: str) -> None:
        class _Fixture(base):  # type: ignore[misc, valid-type]
            meta = _meta(good_code)

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        assert _Fixture.meta.code == good_code

    @pytest.mark.parametrize(("base", "good_code", "bad_code"), CATEGORY_CASES)
    def test_mismatched_code_is_rejected_at_class_definition_time(
        self, base: type, good_code: str, bad_code: str
    ) -> None:
        with pytest.raises(KPIValidationError):

            class _Fixture(base):  # type: ignore[misc, valid-type]
                meta = _meta(bad_code)

                def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                    return None


class TestMultiNamespaceCategories:
    @pytest.mark.parametrize(("base", "good_codes", "bad_code"), MULTI_NAMESPACE_CATEGORY_CASES)
    def test_each_declared_namespace_is_accepted(
        self, base: type, good_codes: list[str], bad_code: str
    ) -> None:
        for code in good_codes:

            class _Fixture(base):  # type: ignore[misc, valid-type]
                meta = _meta(code)

                def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                    return None

            assert _Fixture.meta.code == code

    @pytest.mark.parametrize(("base", "good_codes", "bad_code"), MULTI_NAMESPACE_CATEGORY_CASES)
    def test_a_foreign_namespace_is_rejected(
        self, base: type, good_codes: list[str], bad_code: str
    ) -> None:
        with pytest.raises(KPIValidationError):

            class _Fixture(base):  # type: ignore[misc, valid-type]
                meta = _meta(bad_code)

                def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                    return None


class TestAbstractBasesAreNotInstantiable:
    @pytest.mark.parametrize(
        "base",
        [
            ProductionKPI,
            UtilizationKPI,
            MaintenanceKPI,
            HaulageKPI,
            DelayKPI,
            EnergyKPI,
            QualityKPI,
            CostKPI,
            SafetyKPI,
        ],
    )
    def test_cannot_instantiate_a_category_base_directly(self, base: type) -> None:
        with pytest.raises(TypeError):
            base()
