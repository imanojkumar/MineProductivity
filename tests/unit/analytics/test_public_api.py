"""Tests for the mineproductivity.analytics package's public API surface."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.analytics as analytics

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.decision",
    "mineproductivity.digital_twin",
    "mineproductivity.optimization",
    "mineproductivity.simulation",
    "mineproductivity.agents",
    "mineproductivity.visualization",
)

ALLOWED_TOP_LEVEL_DEPENDENCIES = {"analytics", "core", "events", "kpis", "registry"}
"""Only what this Foundation-phase slice of ``analytics`` actually imports today.

The design specification (§5) additionally *permits* ``ontology``, ``plugins``,
and ``connectors`` for later phases of this package, but none of those are
exercised yet -- this set is deliberately the narrower, currently-true one so
that a future accidental dependency is caught immediately rather than being
retroactively excused by a permission this phase does not use.
"""


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in analytics.__all__:
            assert hasattr(analytics, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(analytics.__all__) == len(set(analytics.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(analytics.__all__) == sorted(analytics.__all__)

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(analytics.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported_names.add(name)
        missing = imported_names - set(analytics.__all__)
        assert not missing, f"Imported but not exported in __all__: {missing}"

    def test_direct_import_of_foundation_classes(self) -> None:
        from mineproductivity.analytics import AnalyticsMetadata, AnalyticsModel, TimeSeries

        assert AnalyticsModel is not None
        assert AnalyticsMetadata is not None
        assert TimeSeries is not None


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        analytics_dir = Path(analytics.__file__).parent
        violations: list[str] = []
        for py_file in analytics_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                module_name = None
                if isinstance(node, ast.ImportFrom) and node.module:
                    module_name = node.module
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                            violations.append(f"{py_file}: import {alias.name}")
                if module_name and module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    violations.append(f"{py_file}: from {module_name} import ...")
        assert not violations, f"Forbidden cross-layer imports found: {violations}"

    def test_only_depends_on_currently_exercised_packages(self) -> None:
        analytics_dir = Path(analytics.__file__).parent
        for py_file in analytics_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module.startswith("mineproductivity.")
                ):
                    top = node.module.split(".")[1]
                    assert top in ALLOWED_TOP_LEVEL_DEPENDENCIES, (
                        f"{py_file}: unexpected dependency on {node.module}"
                    )


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "exceptions",
            "metadata",
            "windowing",
            "result",
            "timeseries",
            "abstractions",
            "pipeline",
            "aggregation",
            "statistics",
            "rolling",
            "trend",
            "baseline",
            "benchmarking",
            "quality",
            "forecasting",
            "anomaly",
            "outliers",
            "incremental",
            "batch",
            "streaming",
            "_registry",
        ]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.analytics.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(analytics)
        assert "AnalyticsModel" in analytics.__all__
