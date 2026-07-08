"""Tests for the mineproductivity.decision package's public API surface."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.decision as decision

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.digital_twin",
    "mineproductivity.simulation",
    "mineproductivity.optimization",
    "mineproductivity.visualization",
    "mineproductivity.agents",
)

ALLOWED_TOP_LEVEL_DEPENDENCIES = {"decision", "core", "events", "kpis", "analytics", "registry"}
"""Only what this Foundation-phase slice of ``decision`` actually
imports today.

The design specification (§5) additionally *permits* ``ontology``,
``plugins``, and ``connectors`` for later phases of this package
(e.g. ``ontology`` entity-type scoping, once a concrete
``DecisionStrategy`` needs it), but none of those are exercised yet --
this set is deliberately the narrower, currently-true one so that a
future accidental dependency is caught immediately rather than being
retroactively excused by a permission this phase does not use.
"""

FOUNDATION_LAYER_PACKAGES = (
    "core",
    "ontology",
    "events",
    "registry",
    "plugins",
    "connectors",
    "kpis",
    "analytics",
)


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in decision.__all__:
            assert hasattr(decision, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(decision.__all__) == len(set(decision.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(decision.__all__) == sorted(decision.__all__)

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(decision.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported_names.add(name)
        missing = imported_names - set(decision.__all__)
        assert not missing, f"Imported but not exported in __all__: {missing}"

    def test_direct_import_of_foundation_classes(self) -> None:
        from mineproductivity.decision import DecisionContext, DecisionMetadata, DecisionModel

        assert DecisionModel is not None
        assert DecisionMetadata is not None
        assert DecisionContext is not None


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        decision_dir = Path(decision.__file__).parent
        violations: list[str] = []
        for py_file in decision_dir.rglob("*.py"):
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
        decision_dir = Path(decision.__file__).parent
        for py_file in decision_dir.rglob("*.py"):
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


class TestNoReverseDependency:
    """Design spec §5, §3.5: no Foundation Layer package or ``analytics``
    may import ``decision`` -- the ``analytics``-package precedent for
    this test (spec 06 checklist) extended one layer up."""

    def test_no_lower_package_imports_decision(self) -> None:
        src_root = Path(decision.__file__).parent.parent
        violations: list[str] = []
        for package_name in FOUNDATION_LAYER_PACKAGES:
            package_dir = src_root / package_name
            if not package_dir.is_dir():
                continue
            for py_file in package_dir.rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.ImportFrom)
                        and node.module
                        and node.module.startswith("mineproductivity.decision")
                    ):
                        violations.append(f"{py_file}: from {node.module} import ...")
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith("mineproductivity.decision"):
                                violations.append(f"{py_file}: import {alias.name}")
        assert not violations, f"Lower package(s) import decision: {violations}"


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "exceptions",
            "metadata",
            "thresholds",
            "result",
            "abstractions",
            "pipeline",
            "_registry",
            "rules",
            "policy",
            "recommendation",
            "strategy",
            "scoring",
            "ranking",
            "explanation",
            "prioritization",
            "root_cause",
            "what_if",
            "planning",
            "alerting",
            "realtime",
            "batch",
            "audit",
        ]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.decision.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(decision)
        assert "DecisionModel" in decision.__all__
