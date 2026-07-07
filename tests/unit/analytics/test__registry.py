"""Tests for mineproductivity.analytics._registry.

Mirrors ``tests/unit/kpis/test_kpi_registry.py``'s scope exactly, minus
the ``DependencyGraph``/circular-dependency tests -- ``AnalyticsMetadata``
has no ``dependencies`` field, so there is no cycle-detection behavior to
exercise here (see ``_registry.py``'s own module docstring). Entry-point
discovery/isolation against real installed plugin packages is already
covered generically, once, in
``tests/integration/test_registry_plugin_discovery.py`` -- the mechanism
(``EntryPointDiscovery``/``EntryPointSpec``) is identical regardless of
which ``Registry`` it targets, so a second, Analytics-specific copy of
that same test would add no incremental coverage (the same reasoning
that keeps ``kpis`` from having its own copy either).
"""

from __future__ import annotations

import pytest

from mineproductivity.registry import UnregisteredLookupError

from mineproductivity.analytics._registry import REGISTRY, register
from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.exceptions import (
    AnalyticsValidationError,
    AnalyticsVersionConflictError,
)
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.result import AnalyticsResult
from mineproductivity.analytics.timeseries import TimeSeries


def _meta(code: str, **overrides: object) -> AnalyticsMetadata:
    fields: dict[str, object] = {
        "code": code,
        "category": AnalyticsCategory.TREND,
        "description": "x",
    }
    fields.update(overrides)
    return AnalyticsMetadata(**fields)  # type: ignore[arg-type]


class _FixtureModel(AnalyticsModel):
    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        return AnalyticsResult(model_code=self.meta.code)


class TestBuiltInModelsRegisteredByDefault:
    @pytest.mark.parametrize("code", ["TREND.Linear", "BASELINE.Rolling", "BENCHMARK.Band"])
    def test_registered(self, code: str) -> None:
        assert code in REGISTRY

    def test_registry_get_returns_the_registered_class(self) -> None:
        from mineproductivity.analytics.trend import LinearTrendModel

        assert REGISTRY.get("TREND.Linear") is LinearTrendModel

    def test_metadata_for_matches_the_class_own_meta(self) -> None:
        from mineproductivity.analytics.baseline import RollingBaselineModel

        metadata = REGISTRY.metadata_for("BASELINE.Rolling")
        assert metadata.unwrap() is RollingBaselineModel.meta


class TestRegistryGetUnknownCode:
    def test_raises_unregistered_lookup_error(self) -> None:
        with pytest.raises(UnregisteredLookupError):
            REGISTRY.get("NOT.AReal.Code")


class TestRegisterDecorator:
    def test_registers_a_new_model(self) -> None:
        @register
        class _NewFixture(_FixtureModel):
            meta = _meta("TEST.RegistryFixtureNew")

        assert REGISTRY.get("TEST.RegistryFixtureNew") is _NewFixture

    def test_returns_the_class_unchanged(self) -> None:
        class _Fixture(_FixtureModel):
            meta = _meta("TEST.RegistryFixtureUnchanged")

        decorated = register(_Fixture)
        assert decorated is _Fixture

    def test_empty_code_raises_analytics_validation_error(self) -> None:
        """A real ``AnalyticsMetadata`` can never carry an empty ``code``
        (its own ``validate()`` rejects it before ``register`` is ever
        reached), so ``register``'s own defensive empty-code guard is
        exercised here via a minimal ``meta`` stand-in that bypasses
        ``AnalyticsMetadata`` construction entirely -- the same technique
        ``test_kpi_registry.py`` uses for its own equivalent guard."""

        class _FakeMeta:
            code = ""

        class _Fixture(_FixtureModel):
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(AnalyticsValidationError):
            register(_Fixture)

    def test_duplicate_code_raises_version_conflict(self) -> None:
        class _Fixture(_FixtureModel):
            meta = _meta("TREND.Linear")  # already registered by trend.py

        with pytest.raises(AnalyticsVersionConflictError):
            register(_Fixture)

    def test_duplicate_code_rejected_even_with_identical_metadata(self) -> None:
        """``Registry.register`` is add-only and rejects *any*
        re-registration under an existing key, identical item or not
        (design spec AD-RG-04) -- ``register`` does not special-case a
        harmless-looking re-import, mirroring ``kpis.register``'s own
        behavior exactly."""
        shared_meta = _meta("TEST.RegistryFixtureIdentical")

        class _First(_FixtureModel):
            meta = shared_meta

        register(_First)

        class _Second(_FixtureModel):
            meta = shared_meta

        with pytest.raises(AnalyticsVersionConflictError):
            register(_Second)
