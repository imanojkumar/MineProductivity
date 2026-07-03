"""Tests for the mineproductivity.connectors package's public API surface."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.connectors as connectors

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.kpis",
    "mineproductivity.analytics",
    "mineproductivity.optimization",
    "mineproductivity.simulation",
    "mineproductivity.decision",
    "mineproductivity.digital_twin",
    "mineproductivity.agents",
)

ALLOWED_TOP_LEVEL_DEPENDENCIES = {"core", "ontology", "events", "registry", "connectors"}


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in connectors.__all__:
            assert hasattr(connectors, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(connectors.__all__) == len(set(connectors.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(connectors.__all__) == sorted(connectors.__all__)

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(connectors.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported_names.add(name)
        missing = imported_names - set(connectors.__all__)
        assert not missing, f"Imported but not exported in __all__: {missing}"

    def test_direct_import_of_core_classes(self) -> None:
        from mineproductivity.connectors import CONNECTORS, FMSConnector, get_connector

        assert FMSConnector is not None
        assert get_connector is not None
        assert CONNECTORS is not None

    def test_oem_shapes_not_in_top_level_all(self) -> None:
        assert "MineStarConnector" not in connectors.__all__
        assert "WencoConnector" not in connectors.__all__


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        connectors_dir = Path(connectors.__file__).parent
        violations: list[str] = []
        for py_file in connectors_dir.rglob("*.py"):
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

    def test_only_depends_on_core_ontology_events_registry(self) -> None:
        connectors_dir = Path(connectors.__file__).parent
        for py_file in connectors_dir.rglob("*.py"):
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
            "base",
            "normalization",
            "auth",
            "retry",
            "health",
            "exceptions",
            "_registry",
            "contract_tests",
            "file",
            "file.csv_connector",
            "file.excel_connector",
            "file._common",
            "network",
            "network.rest_connector",
            "network.graphql_connector",
            "streaming",
            "streaming.kafka_connector",
            "streaming.mqtt_connector",
            "streaming._common",
            "oem",
            "oem.minestar_shape",
            "oem.dispatch_shape",
            "oem.wenco_shape",
            "oem.modular_shape",
            "oem.hexagon_shape",
        ]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.connectors.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(connectors)
