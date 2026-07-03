"""Tests for mineproductivity.kpis.categories._common."""

from __future__ import annotations

import pytest

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories._common import enforce_namespace
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


class TestEnforceNamespace:
    def test_matching_namespace_passes(self) -> None:
        class _Fixture(BaseKPI):
            meta = _meta("PROD.Fixture")

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        enforce_namespace(_Fixture, "PROD")  # must not raise

    def test_exact_namespace_with_no_dot_suffix_passes(self) -> None:
        """A bare ``code == namespace`` (no ``NAMESPACE.Name`` suffix) is
        accepted by ``enforce_namespace`` itself, per its own ``code ==
        namespace or code.startswith(...)`` check -- exercised here via a
        minimal stand-in ``meta``, since a real ``KPIMetadata`` can never
        carry such a code (``KPIMetadata.validate()`` requires at least
        one dot via ``parse_identifier``)."""

        class _FakeMeta:
            code = "PROD"

        class _Fixture(BaseKPI):
            meta = _FakeMeta()  # type: ignore[assignment]

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        enforce_namespace(_Fixture, "PROD")

    def test_mismatched_namespace_raises(self) -> None:
        class _Fixture(BaseKPI):
            meta = _meta("UTIL.Fixture")

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        with pytest.raises(KPIValidationError, match="must start with one of"):
            enforce_namespace(_Fixture, "PROD")

    def test_matches_any_of_several_namespaces(self) -> None:
        class _Fixture(BaseKPI):
            meta = _meta("CARBON.Fixture")

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        enforce_namespace(_Fixture, "ENERGY", "CARBON", "WATER")

    def test_prefix_collision_without_dot_is_rejected(self) -> None:
        """``DISP.Fixture`` must not satisfy a ``DI`` namespace check even
        though ``"DISP.Fixture".startswith("DI")`` is true -- the boundary
        must be the dot, not a bare string prefix. Both ``DI`` and ``DISP``
        are real controlled namespaces (design spec §20), so this is a
        genuine collision, not a contrived one."""

        class _Fixture(BaseKPI):
            meta = _meta("DISP.Fixture")

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        with pytest.raises(KPIValidationError):
            enforce_namespace(_Fixture, "DI")

    def test_abstract_intermediate_without_its_own_meta_is_skipped(self) -> None:
        class _AbstractIntermediate(BaseKPI):
            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        enforce_namespace(_AbstractIntermediate, "PROD")  # must not raise: no own `meta`
