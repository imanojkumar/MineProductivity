"""Tests for mineproductivity.optimization._registry.

Entry-point discovery/isolation against real installed fixture plugins
is covered generically, once, in
``tests/integration/test_registry_plugin_discovery.py`` -- the
mechanism is identical regardless of which ``Registry`` it targets
(``EntryPointSpec(group="mineproductivity.optimization", target_registry="optimization")``,
spec 03 §11), the same delegation reasoning every sibling package's
registry tests record. The §17 adapter-plugin path (a category-ABC
subclass registered via a real on-disk module discovered through
``EntryPointDiscovery``) is exercised end to end below.
"""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

import mineproductivity.optimization as optimization
from mineproductivity.optimization._registry import REGISTRY, register
from mineproductivity.optimization.abstractions import OptimizationContext, OptimizationModel
from mineproductivity.optimization.exceptions import (
    OptimizationValidationError,
    OptimizationVersionConflictError,
)
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata
from mineproductivity.optimization.mixed_integer_programming import (
    MixedIntegerProgrammingModel,
)
from mineproductivity.optimization.problem import OptimizationProblem
from mineproductivity.optimization.result import OptimizationResult
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec, UnregisteredLookupError


def _meta(code: str) -> OptimizationMetadata:
    return OptimizationMetadata(
        code=code, category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING, description="x"
    )


def _unique_code() -> str:
    return f"MIP.RegistryFixture{uuid.uuid4().hex}"


class _FixtureModel(MixedIntegerProgrammingModel):
    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        return OptimizationResult()


class TestNoBuiltInModelsShipped:
    def test_no_module_in_the_package_registers_a_model(self) -> None:
        """Design spec §11-§16: every paradigm is interface-only."""
        package_dir = Path(optimization.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "_registry.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            assert "@register" not in source, f"{py_file.name} registers a built-in model"


class TestRegisterDecorator:
    def test_get_unknown_raises(self) -> None:
        with pytest.raises(UnregisteredLookupError):
            REGISTRY.get("NOT.AReal.Code")

    def test_registers_and_returns_the_class_unchanged(self) -> None:
        code = _unique_code()

        class _Fixture(_FixtureModel):
            meta = _meta(code)

        assert register(_Fixture) is _Fixture
        assert REGISTRY.get(code) is _Fixture
        assert REGISTRY.metadata_for(code).unwrap() is _Fixture.meta

    def test_empty_code_raises_validation_error(self) -> None:
        class _FakeMeta:
            code = ""

        class _Fixture(OptimizationModel):  # no category base -> no definition-time check
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(OptimizationValidationError):
            register(_Fixture)

    def test_duplicate_code_raises_version_conflict_even_with_identical_metadata(
        self,
    ) -> None:
        shared_meta = _meta(_unique_code())

        class _First(_FixtureModel):
            meta = shared_meta

        register(_First)

        class _Second(_FixtureModel):
            meta = shared_meta

        with pytest.raises(OptimizationVersionConflictError):
            register(_Second)


_PLUGIN_SOURCE = '''\
"""A third-party solver adapter -- importing this module registers it,
exactly as a pip-installed plugin entry-point scan would (spec 10 §17)."""

from mineproductivity.optimization import (
    MixedIntegerProgrammingModel,
    OptimizationCategory,
    OptimizationContext,
    OptimizationMetadata,
    OptimizationProblem,
    OptimizationResult,
    register,
)


@register
class SitePackMipAdapter(MixedIntegerProgrammingModel):
    """A site pack MIP solver adapter fixture -- translation logic
    belongs to the plugin, never this platform."""

    meta = OptimizationMetadata(
        code="MIP.SitePackAdapterFixture",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="A site pack MIP solver adapter fixture.",
    )

    def _solve_mip(self, problem: OptimizationProblem, *, context: OptimizationContext) -> OptimizationResult:
        return OptimizationResult(objective_value=1.0)
'''


class TestAdapterPluginEntryPointPath:
    def test_adapter_registered_via_real_entry_point_discovery(self) -> None:
        """Design spec §17's scripted adapter-plugin proof: platform-side
        dispatch/registration works end to end without this package
        depending on the fixture's own translation logic."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            plugin_path = Path(tmp_dir) / "_optimization_adapter_fixture.py"
            plugin_path.write_text(_PLUGIN_SOURCE, encoding="utf-8")
            sys.path.insert(0, tmp_dir)
            try:
                real_entry_points = importlib.metadata.entry_points

                def _fake_entry_points(*, group: str):  # type: ignore[no-untyped-def]
                    if group == "mineproductivity.optimization":
                        return (
                            importlib.metadata.EntryPoint(
                                name="sitepack",
                                value="_optimization_adapter_fixture",
                                group=group,
                            ),
                        )
                    return real_entry_points(group=group)

                importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
                try:
                    result = EntryPointDiscovery().discover(
                        EntryPointSpec(
                            group="mineproductivity.optimization",
                            target_registry="optimization",
                        )
                    )
                finally:
                    importlib.metadata.entry_points = real_entry_points
            finally:
                sys.path.remove(tmp_dir)
                sys.modules.pop("_optimization_adapter_fixture", None)

        assert result.is_ok
        assert "MIP.SitePackAdapterFixture" in REGISTRY
