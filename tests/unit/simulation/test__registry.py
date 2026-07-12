"""Tests for mineproductivity.simulation._registry.

Mirrors ``tests/unit/digital_twin/test__registry.py``'s scope exactly.
This package deliberately ships **zero** registered built-in simulation
models (interface-only methodologies, design spec §13-§16), proven
below by a mechanical scan rather than a registration-order-dependent
emptiness assertion.

Entry-point discovery/isolation against real installed plugin packages
(the healthy/broken fixture-plugin pattern) is already covered
generically, once, in
``tests/integration/test_registry_plugin_discovery.py`` -- the
mechanism (``EntryPointDiscovery``/``EntryPointSpec``) is identical
regardless of which ``Registry`` it targets
(``EntryPointSpec(group="mineproductivity.simulation", target_registry="simulation")``
goes through the exact same per-entry-point isolation code path, spec
03 §11), so a second, Simulation-specific copy would add no
incremental coverage -- the same reasoning that keeps ``kpis``,
``analytics``, ``decision``, and ``digital_twin`` from having their
own copies either. What *is* Simulation-specific -- ``register``'s
translation of a duplicate/empty code into this package's own
exception types -- is exercised below.
``examples/simulation/04_plugin_simulation_model.py`` additionally
demonstrates the full third-party entry-point wiring end to end.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

import mineproductivity.simulation as simulation
from mineproductivity.registry import UnregisteredLookupError
from mineproductivity.simulation._registry import REGISTRY, register
from mineproductivity.simulation.abstractions import SimulationContext, SimulationModel
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.montecarlo import MonteCarloModel
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.scenario import Scenario
from mineproductivity.simulation.exceptions import (
    SimulationValidationError,
    SimulationVersionConflictError,
)


def _meta(code: str) -> SimulationMetadata:
    return SimulationMetadata(code=code, category=SimulationCategory.MONTE_CARLO, description="x")


def _unique_code() -> str:
    return f"MONTECARLO.RegistryFixture{uuid.uuid4().hex}"


class _FixtureModel(MonteCarloModel):
    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        return SimulationResult()


class TestNoBuiltInModelsShipped:
    def test_no_module_in_the_package_registers_a_model(self) -> None:
        """Design spec §13-§16: every methodology is interface-only --
        mechanically, no ``@register`` use exists anywhere in
        ``src/mineproductivity/simulation/``."""
        package_dir = Path(simulation.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "_registry.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            assert "@register" not in source, f"{py_file.name} registers a built-in model"


class TestRegistryGetUnknownCode:
    def test_raises_unregistered_lookup_error(self) -> None:
        with pytest.raises(UnregisteredLookupError):
            REGISTRY.get("NOT.AReal.Code")


class TestRegisterDecorator:
    def test_registers_a_new_model_type(self) -> None:
        code = _unique_code()

        @register
        class _NewFixture(_FixtureModel):
            meta = _meta(code)

        assert REGISTRY.get(code) is _NewFixture

    def test_registry_metadata_matches_the_class_own_meta(self) -> None:
        code = _unique_code()

        @register
        class _Fixture(_FixtureModel):
            meta = _meta(code)

        assert REGISTRY.metadata_for(code).unwrap() is _Fixture.meta

    def test_returns_the_class_unchanged(self) -> None:
        class _Fixture(_FixtureModel):
            meta = _meta(_unique_code())

        assert register(_Fixture) is _Fixture

    def test_empty_code_raises_simulation_validation_error(self) -> None:
        """The fixture subclasses ``SimulationModel`` directly (no
        category base) so the category bases' own definition-time
        namespace check cannot fire first -- ``register``'s defensive
        empty-code guard is what gets exercised."""

        class _FakeMeta:
            code = ""

        class _Fixture(SimulationModel):
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(SimulationValidationError):
            register(_Fixture)

    def test_duplicate_code_raises_version_conflict(self) -> None:
        code = _unique_code()

        @register
        class _First(_FixtureModel):
            meta = _meta(code)

        class _Second(_FixtureModel):
            meta = _meta(code)

        with pytest.raises(SimulationVersionConflictError):
            register(_Second)

    def test_duplicate_code_rejected_even_with_identical_metadata(self) -> None:
        shared_meta = _meta(_unique_code())

        class _First(_FixtureModel):
            meta = shared_meta

        register(_First)

        class _Second(_FixtureModel):
            meta = shared_meta

        with pytest.raises(SimulationVersionConflictError):
            register(_Second)
