"""Tests for mineproductivity.kpis.certification."""

from __future__ import annotations

import pytest

from mineproductivity.kpis.certification import (
    CertificationFixture,
    _reference_fixtures,
    register_fixture,
    run_certification_fixture,
)
from mineproductivity.kpis.standard_library.production import TonnesPerHour


class TestCertificationFixture:
    def test_construction(self) -> None:
        fixture = CertificationFixture(
            kpi_code="PROD.TPH",
            rows=[{"payload_t": 100.0, "operating_h": 1.0}],
            expected_value=100.0,
        )
        assert fixture.tolerance == 1e-6


class TestRegisterFixture:
    def test_registers_and_returns_the_fixture_unchanged(self) -> None:
        fixture = CertificationFixture(
            kpi_code="PROD.CertificationRegisterFixture",
            rows=[{"payload_t": 100.0, "operating_h": 1.0}],
            expected_value=100.0,
        )
        returned = register_fixture(fixture)
        assert returned is fixture
        assert _reference_fixtures["PROD.CertificationRegisterFixture"] is fixture


class TestRunCertificationFixture:
    def test_matching_value_within_tolerance_passes(self) -> None:
        fixture = CertificationFixture(
            kpi_code="PROD.TPH",
            rows=[
                {"payload_t": 15600.0, "operating_h": 12.0},
                {"payload_t": 6600.0, "operating_h": 6.0},
            ],
            expected_value=1233.333333,
            tolerance=1e-3,
        )
        result = run_certification_fixture(TonnesPerHour(), fixture)
        assert result.value is not None

    def test_mismatched_value_raises_assertion_error(self) -> None:
        fixture = CertificationFixture(
            kpi_code="PROD.TPH",
            rows=[{"payload_t": 100.0, "operating_h": 1.0}],
            expected_value=999.0,
        )
        with pytest.raises(AssertionError):
            run_certification_fixture(TonnesPerHour(), fixture)

    def test_expected_none_and_actual_none_passes(self) -> None:
        fixture = CertificationFixture(
            kpi_code="PROD.TPH", rows=[{"payload_t": 0.0, "operating_h": 0.0}], expected_value=None
        )
        result = run_certification_fixture(TonnesPerHour(), fixture)
        assert result.value is None

    def test_expected_none_but_actual_has_a_value_raises(self) -> None:
        fixture = CertificationFixture(
            kpi_code="PROD.TPH",
            rows=[{"payload_t": 100.0, "operating_h": 1.0}],
            expected_value=None,
        )
        with pytest.raises(AssertionError):
            run_certification_fixture(TonnesPerHour(), fixture)

    def test_expected_a_value_but_actual_is_none_raises(self) -> None:
        fixture = CertificationFixture(
            kpi_code="PROD.TPH", rows=[{"payload_t": 0.0, "operating_h": 0.0}], expected_value=100.0
        )
        with pytest.raises(AssertionError):
            run_certification_fixture(TonnesPerHour(), fixture)
