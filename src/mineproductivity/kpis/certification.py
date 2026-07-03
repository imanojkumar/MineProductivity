"""Certification hooks: the mechanism ``tests/certification/`` uses to
run flagship KPIs against the Learning & Benchmark Suite's golden
datasets (design spec §30).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.result import KPIResult

__all__ = ["CertificationFixture", "register_fixture", "run_certification_fixture"]


@dataclasses.dataclass(frozen=True, slots=True)
class CertificationFixture:
    """One golden-dataset certification case: input rows plus the
    published expected value, to a documented tolerance."""

    kpi_code: str
    rows: Sequence[Mapping[str, Any]]
    expected_value: float | None
    tolerance: float = 1e-6


#: Internal binding to the Learning & Benchmark Suite's golden-dataset
#: fixtures (design spec §9) -- not part of the public contract; consumed
#: only by ``tests/certification/``.
_reference_fixtures: dict[str, CertificationFixture] = {}


def register_fixture(fixture: CertificationFixture) -> CertificationFixture:
    """Register ``fixture`` into the internal certification fixture
    table, keyed by ``kpi_code``. Returns ``fixture`` unchanged, so it
    can be used as a decorator-free "define and register in one
    expression" call at module load time."""
    _reference_fixtures[fixture.kpi_code] = fixture
    return fixture


def run_certification_fixture(kpi: BaseKPI, fixture: CertificationFixture) -> KPIResult:
    """Compute ``kpi`` against ``fixture.rows`` and assert the result
    matches ``fixture.expected_value`` to within ``fixture.tolerance``
    (or is ``None``, if ``fixture.expected_value`` is ``None``)."""
    result = kpi.compute(fixture.rows)
    if fixture.expected_value is None:
        assert result.value is None, f"{fixture.kpi_code}: expected None, got {result.value}"
    else:
        assert result.value is not None, f"{fixture.kpi_code}: expected a value, got None"
        assert abs(result.value - fixture.expected_value) <= fixture.tolerance, (
            f"{fixture.kpi_code}: expected {fixture.expected_value} (+/- {fixture.tolerance}), "
            f"got {result.value}"
        )
    return result
