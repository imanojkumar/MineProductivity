"""Tests for the mineproductivity.events package's public API surface."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.events as events

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.connectors",
    "mineproductivity.kpis",
    "mineproductivity.analytics",
    "mineproductivity.optimization",
    "mineproductivity.simulation",
    "mineproductivity.decision",
    "mineproductivity.digital_twin",
    "mineproductivity.agents",
)


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in events.__all__:
            assert hasattr(events, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(events.__all__) == len(set(events.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(events.__all__) == sorted(events.__all__)

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        """Regression guard: __init__.py previously imported EventID but
        omitted it from __all__, which importable-attribute checks alone
        do not catch (EventID was still importable; it just wasn't
        advertised as public). Parses the AST of __init__.py itself and
        confirms every non-private imported name is listed in __all__."""
        init_path = Path(events.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported_names.add(name)
        missing = imported_names - set(events.__all__)
        assert not missing, f"Imported but not exported in __all__: {missing}"

    def test_direct_import_of_core_classes(self) -> None:
        from mineproductivity.events import BaseEvent, CycleEvent, EventEnvelope, EventStore

        assert BaseEvent is not None
        assert CycleEvent is not None
        assert EventEnvelope is not None
        assert EventStore is not None


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        events_dir = Path(events.__file__).parent
        violations: list[str] = []
        for py_file in events_dir.rglob("*.py"):
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

    def test_only_ontology_dependency_is_delaycategory(self) -> None:
        events_dir = Path(events.__file__).parent
        ontology_imports: set[str] = set()
        for py_file in events_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "mineproductivity.ontology":
                    ontology_imports.update(alias.name for alias in node.names)
        assert ontology_imports <= {"DelayCategory"}


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "base_event",
            "bus",
            "envelope",
            "exceptions",
            "identifier",
            "replay",
            "schema",
            "snapshot",
            "store",
            "validation",
            "versioning",
            "canonical",
            "canonical.consumption_event",
            "canonical.cycle_event",
            "canonical.delay_event",
            "canonical.maintenance_event",
            "canonical.production_event",
            "canonical.safety_event",
            "serialization",
            "serialization.json_codec",
            "serialization.arrow_codec",
            "serialization.parquet_codec",
        ]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.events.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(events)
