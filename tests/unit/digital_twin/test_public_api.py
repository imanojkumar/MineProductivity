"""Tests for the mineproductivity.digital_twin package's public API
surface."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.digital_twin as digital_twin

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.simulation",
    "mineproductivity.optimization",
    "mineproductivity.agents",
    "mineproductivity.visualization",
)

ALLOWED_TOP_LEVEL_DEPENDENCIES = {
    "digital_twin",
    "core",
    "events",
    "kpis",
    "analytics",
    "decision",
    "registry",
}
"""Only what this package actually imports today.

The design specification (§5) additionally *permits* ``ontology``,
``plugins``, and ``connectors``, but none are exercised: ``ontology``
supplies the vocabulary a twin's ``scope`` values are expressed in
(strings, not imported types), ``plugins`` orchestrates entry-point
discovery at the application level, and ``connectors`` is deliberately
never exercised (§16). This set is the narrower, currently-true one so
a future accidental dependency is caught immediately rather than being
retroactively excused by a permission this phase does not use -- the
same discipline ``decision``'s own copy of this test established.
"""

LOWER_PACKAGES = (
    "core",
    "ontology",
    "events",
    "registry",
    "plugins",
    "connectors",
    "kpis",
    "analytics",
    "decision",
)

#: Design spec §32 proof 1 (no fact-recomputation): the computation
#: engines' orchestrators must never be imported by this package --
#: ``digital_twin`` consumes their *result types* only.
FORBIDDEN_COMPUTATION_SYMBOLS = {
    "KPIEngine",
    "BatchAnalyticsRunner",
    "StreamingAnalyticsSession",
    "AnalyticsPipeline",
    "BatchDecisionRunner",
    "RealTimeDecisionSession",
    "DecisionPipeline",
    "RuleEngine",
}


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in digital_twin.__all__:
            assert hasattr(digital_twin, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(digital_twin.__all__) == len(set(digital_twin.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(digital_twin.__all__) == sorted(digital_twin.__all__)

    def test_exactly_the_design_spec_7_symbol_list(self) -> None:
        assert set(digital_twin.__all__) == {
            "Twin",
            "TwinContext",
            "TwinMetadata",
            "TwinCategory",
            "MineTwin",
            "EquipmentTwin",
            "PlantTwin",
            "ConveyorTwin",
            "HaulageTwin",
            "FleetTwin",
            "ProcessingPlantTwin",
            "GeologicalTwin",
            "VentilationTwin",
            "StockpileTwin",
            "ProductionTwin",
            "TwinStatus",
            "TwinState",
            "TwinSnapshot",
            "TwinSynchronizer",
            "SyncPolicy",
            "TelemetryReading",
            "TwinSimulationModel",
            "by_category",
            "by_scope",
            "TwinRepository",
            "TwinStateCache",
            "TwinResult",
            "SyncResult",
            "TwinSimulationResult",
            "register",
            "REGISTRY",
            "TwinValidationError",
            "TwinNotFoundError",
            "TwinSyncError",
            "TwinVersionConflictError",
            "TwinStateConflictError",
        }

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(digital_twin.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported_names.add(name)
        missing = imported_names - set(digital_twin.__all__)
        assert not missing, f"Imported but not exported in __all__: {missing}"

    def test_direct_import_of_foundation_classes(self) -> None:
        from mineproductivity.digital_twin import Twin, TwinContext, TwinMetadata

        assert Twin is not None
        assert TwinMetadata is not None
        assert TwinContext is not None


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        package_dir = Path(digital_twin.__file__).parent
        violations: list[str] = []
        for py_file in package_dir.rglob("*.py"):
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
        package_dir = Path(digital_twin.__file__).parent
        for py_file in package_dir.rglob("*.py"):
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

    def test_no_fact_recomputation_engines_are_imported(self) -> None:
        """Design spec §32 proof 1: every KPI-, Analytics-, or
        Decision-shaped value entering this package arrives as an
        already-computed result object -- the engines that compute them
        are never imported here."""
        package_dir = Path(digital_twin.__file__).parent
        violations: list[str] = []
        for py_file in package_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        if alias.name in FORBIDDEN_COMPUTATION_SYMBOLS:
                            violations.append(f"{py_file}: {alias.name}")
        assert not violations, f"Computation engines imported into digital_twin: {violations}"


class TestNoReverseDependency:
    """Design spec §5, §3.6: no lower package (``core`` through
    ``decision``) may import ``digital_twin`` -- the
    ``analytics``/``decision``-package precedent extended one layer
    up."""

    def test_no_lower_package_imports_digital_twin(self) -> None:
        src_root = Path(digital_twin.__file__).parent.parent
        violations: list[str] = []
        for package_name in LOWER_PACKAGES:
            package_dir = src_root / package_name
            if not package_dir.is_dir():
                continue
            for py_file in package_dir.rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.ImportFrom)
                        and node.module
                        and node.module.startswith("mineproductivity.digital_twin")
                    ):
                        violations.append(f"{py_file}: from {node.module} import ...")
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith("mineproductivity.digital_twin"):
                                violations.append(f"{py_file}: import {alias.name}")
        assert not violations, f"Lower package(s) import digital_twin: {violations}"


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "exceptions",
            "lifecycle",
            "metadata",
            "state",
            "snapshot",
            "result",
            "telemetry",
            "abstractions",
            "categories",
            "_registry",
            "simulation",
            "discovery",
            "persistence",
            "caching",
            "synchronization",
        ]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.digital_twin.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(digital_twin)
        assert "Twin" in digital_twin.__all__
