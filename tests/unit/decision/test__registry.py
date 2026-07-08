"""Tests for mineproductivity.decision._registry.

Mirrors ``tests/unit/analytics/test__registry.py``'s scope exactly --
``decision.REGISTRY``/``register`` specialize ``registry.Registry`` the
same way ``analytics._registry`` does one layer down, with no
``DependencyGraph``-equivalent machinery (``DecisionMetadata`` has no
``dependencies`` field). Two built-in ``DecisionModel`` subclasses
self-register at import time (``STRATEGY.Threshold`` in Phase 07.2,
``RANKING.WeightedScore`` in Phase 07.3), exercised in the
"registered by default" tests below.

Entry-point discovery/isolation against real installed plugin packages
(the healthy/broken fixture-plugin pattern) is already covered
generically, once, in
``tests/integration/test_registry_plugin_discovery.py`` -- the
mechanism (``EntryPointDiscovery``/``EntryPointSpec``) is identical
regardless of which ``Registry`` it targets
(``EntryPointSpec(group="mineproductivity.decision", target_registry="decision")``
goes through the exact same per-entry-point isolation code path, spec
03 §11), so a second, Decision-specific copy of that same test would
add no incremental coverage -- the same reasoning that keeps ``kpis``
and ``analytics`` from having their own copies either. What *is*
Decision-specific -- ``register``'s translation of a duplicate/empty
code into this package's own exception types -- is exercised below.
``examples/decision/04_plugin_strategy.py`` additionally demonstrates
the full third-party entry-point wiring end to end.
"""

from __future__ import annotations

import pytest

from mineproductivity.registry import UnregisteredLookupError

from mineproductivity.decision._registry import REGISTRY, register
from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.exceptions import (
    DecisionValidationError,
    DecisionVersionConflictError,
)
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
from mineproductivity.decision.result import DecisionResult


def _meta(code: str, **overrides: object) -> DecisionMetadata:
    fields: dict[str, object] = {
        "code": code,
        "category": DecisionCategory.STRATEGY,
        "description": "x",
    }
    fields.update(overrides)
    return DecisionMetadata(**fields)  # type: ignore[arg-type]


class _FixtureModel(DecisionModel):
    def _decide(self, context: DecisionContext) -> DecisionResult:
        return DecisionResult(model_code=self.meta.code)


class TestBuiltInModelsRegisteredByDefault:
    @pytest.mark.parametrize("code", ["STRATEGY.Threshold", "RANKING.WeightedScore"])
    def test_registered(self, code: str) -> None:
        import mineproductivity.decision  # noqa: F401  # triggers self-registration

        assert code in REGISTRY

    def test_registry_get_returns_the_registered_class(self) -> None:
        from mineproductivity.decision.strategy import ThresholdDecisionStrategy

        assert REGISTRY.get("STRATEGY.Threshold") is ThresholdDecisionStrategy

    def test_metadata_for_matches_the_class_own_meta(self) -> None:
        from mineproductivity.decision.ranking import WeightedScoreRanking

        metadata = REGISTRY.metadata_for("RANKING.WeightedScore")
        assert metadata.unwrap() is WeightedScoreRanking.meta


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

    def test_registry_metadata_matches_the_class_own_meta(self) -> None:
        @register
        class _Fixture(_FixtureModel):
            meta = _meta("TEST.RegistryFixtureMetadata")

        assert REGISTRY.metadata_for("TEST.RegistryFixtureMetadata").unwrap() is _Fixture.meta

    def test_returns_the_class_unchanged(self) -> None:
        class _Fixture(_FixtureModel):
            meta = _meta("TEST.RegistryFixtureUnchanged")

        decorated = register(_Fixture)
        assert decorated is _Fixture

    def test_empty_code_raises_decision_validation_error(self) -> None:
        """A real ``DecisionMetadata`` can never carry an empty ``code``
        (its own ``validate()`` rejects it before ``register`` is ever
        reached), so ``register``'s own defensive empty-code guard is
        exercised here via a minimal ``meta`` stand-in that bypasses
        ``DecisionMetadata`` construction entirely -- the same technique
        ``analytics``/``kpis`` own registry tests use for their
        equivalent guard."""

        class _FakeMeta:
            code = ""

        class _Fixture(_FixtureModel):
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(DecisionValidationError):
            register(_Fixture)

    def test_duplicate_code_raises_version_conflict(self) -> None:
        class _First(_FixtureModel):
            meta = _meta("TEST.RegistryFixtureDuplicate")

        register(_First)

        class _Second(_FixtureModel):
            meta = _meta("TEST.RegistryFixtureDuplicate")

        with pytest.raises(DecisionVersionConflictError):
            register(_Second)

    def test_duplicate_code_rejected_even_with_identical_metadata(self) -> None:
        """``Registry.register`` is add-only and rejects *any*
        re-registration under an existing key, identical item or not
        (design spec AD-RG-04) -- ``register`` does not special-case a
        harmless-looking re-import, mirroring ``analytics.register``'s
        own behavior exactly."""
        shared_meta = _meta("TEST.RegistryFixtureIdentical")

        class _First(_FixtureModel):
            meta = shared_meta

        register(_First)

        class _Second(_FixtureModel):
            meta = shared_meta

        with pytest.raises(DecisionVersionConflictError):
            register(_Second)
