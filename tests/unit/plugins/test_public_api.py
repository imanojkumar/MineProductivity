"""Tests for the mineproductivity.plugins package's public API surface."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.plugins as plugins

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.ontology",
    "mineproductivity.events",
    "mineproductivity.connectors",
    "mineproductivity.kpis",
    "mineproductivity.analytics",
    "mineproductivity.optimization",
    "mineproductivity.simulation",
    "mineproductivity.decision",
    "mineproductivity.digital_twin",
    "mineproductivity.agents",
    "mineproductivity.visualization",
)


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in plugins.__all__:
            assert hasattr(plugins, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(plugins.__all__) == len(set(plugins.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(plugins.__all__) == sorted(plugins.__all__)

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(plugins.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported_names.add(name)
        missing = imported_names - set(plugins.__all__)
        assert not missing, f"Imported but not exported in __all__: {missing}"

    def test_direct_import_of_core_classes(self) -> None:
        from mineproductivity.plugins import PluginLifecycle, PluginManifest

        assert PluginManifest is not None
        assert PluginLifecycle is not None


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        plugins_dir = Path(plugins.__file__).parent
        violations: list[str] = []
        for py_file in plugins_dir.rglob("*.py"):
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

    def test_only_depends_on_core_and_registry(self) -> None:
        plugins_dir = Path(plugins.__file__).parent
        for py_file in plugins_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module.startswith("mineproductivity.")
                ):
                    top = node.module.split(".")[1]
                    assert top in {"core", "registry", "plugins"}, (
                        f"{py_file}: unexpected dependency on {node.module}"
                    )


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = ["manifest", "lifecycle", "loader", "dependency", "exceptions"]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.plugins.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(plugins)
