"""Tests for the mineproductivity.kpis package's public API surface."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.kpis as kpis

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.connectors",
    "mineproductivity.analytics",
    "mineproductivity.optimization",
    "mineproductivity.simulation",
    "mineproductivity.decision",
    "mineproductivity.digital_twin",
    "mineproductivity.agents",
)

ALLOWED_TOP_LEVEL_DEPENDENCIES = {"core", "ontology", "events", "registry", "kpis"}


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in kpis.__all__:
            assert hasattr(kpis, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(kpis.__all__) == len(set(kpis.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(kpis.__all__) == sorted(kpis.__all__)

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(kpis.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                if node.module == "mineproductivity.kpis.standard_library":
                    continue  # side-effecting only, deliberately not re-exported
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported_names.add(name)
        missing = imported_names - set(kpis.__all__)
        assert not missing, f"Imported but not exported in __all__: {missing}"

    def test_direct_import_of_core_classes(self) -> None:
        from mineproductivity.kpis import REGISTRY, BaseKPI, KPIEngine, KPIMetadata

        assert REGISTRY is not None
        assert BaseKPI is not None
        assert KPIEngine is not None
        assert KPIMetadata is not None

    def test_flagship_kpi_classes_not_in_top_level_all(self) -> None:
        assert "TonnesPerHour" not in kpis.__all__
        assert "OverallEquipmentEffectiveness" not in kpis.__all__

    def test_standard_library_registration_ran(self) -> None:
        """``REGISTRY`` is a process-level global also written to by other
        test modules' own registration fixtures within the same pytest
        session (mirroring ``connectors.CONNECTORS``'s established
        pattern), so this checks the 12 known flagships are present as a
        subset rather than asserting an exact, session-order-dependent
        count."""
        expected = {
            "PROD.TPH",
            "UTIL.PA",
            "UTIL.UA",
            "UTIL.Performance",
            "UTIL.OEE",
            "MAINT.MTTR",
            "HAUL.TruckCycleTime",
            "DISP.TotalDelayHours",
            "ENERGY.FuelConsumed",
            "QUAL.OreProportion",
            "COST.FuelPerTonne",
            "SAFE.SpeedViolationCount",
        }
        assert expected <= set(kpis.REGISTRY)


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        kpis_dir = Path(kpis.__file__).parent
        violations: list[str] = []
        for py_file in kpis_dir.rglob("*.py"):
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

    def test_never_imports_connectors_specifically(self) -> None:
        """The single most load-bearing dependency rule in the governing
        specification (design spec §7): ``kpis`` MUST NOT import
        ``connectors`` under any circumstance."""
        kpis_dir = Path(kpis.__file__).parent
        for py_file in kpis_dir.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "mineproductivity.connectors" not in text, f"{py_file} references connectors"

    def test_only_depends_on_core_ontology_events_registry(self) -> None:
        kpis_dir = Path(kpis.__file__).parent
        for py_file in kpis_dir.rglob("*.py"):
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


class TestEngineHoldsNoMetricLogic:
    def test_engine_module_contains_no_kpi_code_specific_branches(self) -> None:
        """Mechanical proof of design spec §37.1: grep ``engine.py`` for any
        literal KPI code (a ``NAMESPACE.`` prefix string), which would mean
        the orchestrator has grown metric-specific knowledge."""
        from mineproductivity.kpis.naming import CONTROLLED_NAMESPACES

        engine_path = Path(kpis.__file__).parent / "engine.py"
        text = engine_path.read_text(encoding="utf-8")
        violations = [ns for ns in CONTROLLED_NAMESPACES if f'"{ns}.' in text or f"'{ns}." in text]
        assert not violations, f"engine.py references specific KPI codes: {violations}"


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "exceptions",
            "lifecycle",
            "naming",
            "metadata",
            "result",
            "base_kpi",
            "composite",
            "inheritance",
            "dependency_graph",
            "aggregation",
            "windowing",
            "caching",
            "validation",
            "certification",
            "_registry",
            "engine",
            "categories",
            "categories._common",
            "categories.production_kpi",
            "categories.utilization_kpi",
            "categories.maintenance_kpi",
            "categories.haulage_kpi",
            "categories.delay_kpi",
            "categories.energy_kpi",
            "categories.quality_kpi",
            "categories.cost_kpi",
            "categories.safety_kpi",
            "backends",
            "backends.base_backend",
            "backends.pandas_backend",
            "backends.numpy_backend",
            "backends.polars_backend",
            "backends.duckdb_backend",
            "standard_library",
            "standard_library.production",
            "standard_library.utilization",
            "standard_library.maintenance",
            "standard_library.haulage",
            "standard_library.delay",
            "standard_library.energy",
            "standard_library.quality",
            "standard_library.cost",
            "standard_library.safety",
        ]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.kpis.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(kpis)
        assert "PROD.TPH" in kpis.REGISTRY
