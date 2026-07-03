"""Tests for mineproductivity.kpis._registry."""

from __future__ import annotations

import pytest

from mineproductivity.registry import Registry, UnregisteredLookupError

from mineproductivity.kpis._registry import REGISTRY, register
from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories.production_kpi import ProductionKPI
from mineproductivity.kpis.dependency_graph import DependencyGraph
from mineproductivity.kpis.exceptions import (
    KPICircularDependencyError,
    KPIValidationError,
    KPIVersionConflictError,
)
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata


def _meta(code: str, **overrides: object) -> KPIMetadata:
    fields: dict[str, object] = {
        "code": code,
        "name": code,
        "official_name": code,
        "business_purpose": "x",
        "operational_question": "x",
        "business_meaning": "x",
        "formula": "x",
        "unit": "x",
        "dimensions": ("Shift",),
        "required_events": ("CYCLE",),
        "aggregation": Aggregation.ADDITIVE,
        "direction": Direction.HIGHER_IS_BETTER,
        "min_maturity": DigitalMaturity.L1_MANUAL,
        "leading_or_lagging": "lagging",
        "operational_or_strategic": "operational",
    }
    fields.update(overrides)
    return KPIMetadata(**fields)  # type: ignore[arg-type]


class TestBuiltInFlagshipsRegisteredByDefault:
    @pytest.mark.parametrize(
        "code",
        [
            "PROD.TPH",
            "UTIL.PA",
            "UTIL.UA",
            "UTIL.Performance",
            "UTIL.OEE",
            "MAINT.MTTR",
            "HAUL.TruckCycleTime",
            "DISP.TotalDelayHours",
            "ENERGY.FuelConsumed",
            "QUAL.OreProportion",
            "COST.FuelPerTonne",
            "SAFE.SpeedViolationCount",
        ],
    )
    def test_flagship_registered(self, code: str) -> None:
        assert code in REGISTRY

    def test_registry_get_returns_the_registered_class(self) -> None:
        from mineproductivity.kpis.standard_library.production import TonnesPerHour

        assert REGISTRY.get("PROD.TPH") is TonnesPerHour


class TestRegistryGetUnknownCode:
    def test_raises_unregistered_lookup_error(self) -> None:
        with pytest.raises(UnregisteredLookupError):
            REGISTRY.get("NOT.AReal.Code")


class TestRegisterDecorator:
    def test_registers_a_new_kpi(self) -> None:
        @register
        class _FixtureKPI(ProductionKPI):
            meta = _meta("PROD.RegistryFixtureNew")

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        assert REGISTRY.get("PROD.RegistryFixtureNew") is _FixtureKPI

    def test_returns_the_class_unchanged(self) -> None:
        class _Fixture(ProductionKPI):
            meta = _meta("PROD.RegistryFixtureUnchanged")

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        decorated = register(_Fixture)
        assert decorated is _Fixture

    def test_empty_code_raises_kpi_validation_error(self) -> None:
        """A real ``KPIMetadata`` can never carry an empty ``code`` (its
        own ``validate()`` rejects it via ``parse_identifier`` before
        ``register`` is ever reached), so ``register``'s own defensive
        empty-code guard is exercised here via a minimal ``meta`` stand
        -in that bypasses ``KPIMetadata`` construction, subclassing
        ``BaseKPI`` directly (not a category base, which would itself
        reject an empty code first via ``enforce_namespace``)."""

        class _FakeMeta:
            code = ""

        class _Fixture(BaseKPI):
            meta = _FakeMeta()  # type: ignore[assignment]

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        with pytest.raises(KPIValidationError):
            register(_Fixture)  # type: ignore[arg-type]

    def test_duplicate_code_raises_version_conflict(self) -> None:
        class _Fixture(ProductionKPI):
            meta = _meta("PROD.TPH")  # already registered by the standard library

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        with pytest.raises(KPIVersionConflictError):
            register(_Fixture)

    def test_registering_a_cycle_raises_circular_dependency_error(self) -> None:
        fake_registry: Registry[str, type] = Registry(name="kpi-registry-cycle-fixture")

        class _A(ProductionKPI):
            meta = _meta("PROD.CycleA", dependencies=("PROD.CycleB",))

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        class _B(ProductionKPI):
            meta = _meta("PROD.CycleB", dependencies=("PROD.CycleA",))

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        fake_registry.register("PROD.CycleA", _A, metadata=_A.meta)
        fake_registry.register("PROD.CycleB", _B, metadata=_B.meta)
        graph = DependencyGraph(fake_registry)
        with pytest.raises(KPICircularDependencyError):
            graph.topological_order("PROD.CycleA")

    def test_registration_invalidates_the_module_level_dependency_graph_cache(self) -> None:
        from mineproductivity.kpis import _registry as registry_module

        @register
        class _Fixture(ProductionKPI):
            meta = _meta("PROD.RegistryFixtureInvalidation")

            def _compute(self, rows: object) -> float | None:  # type: ignore[override]
                return None

        # If invalidate() were skipped, a stale cached order (from before
        # this KPI existed) would raise looking it up here.
        order = registry_module._GRAPH.topological_order("PROD.RegistryFixtureInvalidation")
        assert order == ("PROD.RegistryFixtureInvalidation",)
