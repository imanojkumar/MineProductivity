"""Tests for the mineproductivity.simulation package's public API
surface."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.simulation as simulation

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.optimization",
    "mineproductivity.agents",
    "mineproductivity.visualization",
)

ALLOWED_TOP_LEVEL_DEPENDENCIES = {
    "simulation",
    "core",
    "events",
    "kpis",
    "analytics",
    "decision",
    "digital_twin",
    "registry",
}
"""Only what this package actually imports today. The design
specification (§5) additionally *permits* ``ontology``, ``plugins``,
and ``connectors``, but none are exercised -- the same
narrower-than-permitted discipline every sibling package's copy of
this test established."""

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
    "digital_twin",
)

#: Design spec §35 proof 1 (no fact-recomputation): the computation
#: engines' orchestrators must never be imported by this package --
#: ``simulation`` consumes their *result types* (and, uniquely,
#: ``analytics``' statistical primitives, §5) only.
FORBIDDEN_COMPUTATION_SYMBOLS = {
    "KPIEngine",
    "AnalyticsPipeline",
    "BatchAnalyticsRunner",
    "StreamingAnalyticsSession",
    "DecisionPipeline",
    "RuleEngine",
    "BatchDecisionRunner",
    "RealTimeDecisionSession",
    "TwinSynchronizer",
}


class TestPublicApiSurface:
    def test_all_entries_are_actually_importable_attributes(self) -> None:
        for name in simulation.__all__:
            assert hasattr(simulation, name), f"{name!r} listed in __all__ but not defined"

    def test_no_duplicate_entries_in_all(self) -> None:
        assert len(simulation.__all__) == len(set(simulation.__all__))

    def test_all_is_sorted(self) -> None:
        assert list(simulation.__all__) == sorted(simulation.__all__)

    def test_exactly_the_design_spec_7_symbol_list(self) -> None:
        assert set(simulation.__all__) == {
            "SimulationModel",
            "SimulationContext",
            "SimulationMetadata",
            "SimulationCategory",
            "Scenario",
            "ScenarioStatus",
            "SimulationRun",
            "RunStatus",
            "SimulationExecutor",
            "SimulationState",
            "SimulationClock",
            "TimeProgressionMode",
            "seed_from_replay",
            "MonteCarloModel",
            "DiscreteEventModel",
            "SystemDynamicsModel",
            "CalibrationModel",
            "Experiment",
            "ExperimentRunner",
            "ScenarioComparator",
            "SensitivityAnalyzer",
            "by_category",
            "by_scope",
            "SimulationRunRepository",
            "SimulationStateCache",
            "SimulationResult",
            "ExperimentResult",
            "register",
            "REGISTRY",
            "SimulationValidationError",
            "SimulationRunNotFoundError",
            "SimulationExecutionError",
            "SimulationVersionConflictError",
            "ScenarioConflictError",
        }

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(simulation.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported_names.add(name)
        missing = imported_names - set(simulation.__all__)
        assert not missing, f"Imported but not exported in __all__: {missing}"


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        package_dir = Path(simulation.__file__).parent
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
        package_dir = Path(simulation.__file__).parent
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
        """Design spec §35 proof 1."""
        package_dir = Path(simulation.__file__).parent
        violations: list[str] = []
        for py_file in package_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        if alias.name in FORBIDDEN_COMPUTATION_SYMBOLS:
                            violations.append(f"{py_file}: {alias.name}")
        assert not violations, f"Computation engines imported into simulation: {violations}"

    def test_no_statistics_reimplementation_in_comparison_or_sensitivity(self) -> None:
        """Design spec §35 proof 2: ``comparison.py``/``sensitivity.py``
        contain zero mean/percentile/correlation arithmetic of their
        own -- every such computation is a call into ``analytics``.
        Mechanically: no ``statistics``/``math`` import, no ``sum(``,
        and no division-by-length idiom appears in either module."""
        package_dir = Path(simulation.__file__).parent
        for module_name in ("comparison.py", "sensitivity.py"):
            source = (package_dir / module_name).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=module_name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name not in {"statistics", "math", "numpy"}, (
                            f"{module_name} imports a statistics library"
                        )
            assert "sum(" not in source, f"{module_name} sums values itself"
            assert "/ len(" not in source, f"{module_name} computes a mean itself"


class TestNoReverseDependency:
    def test_no_lower_package_imports_simulation(self) -> None:
        src_root = Path(simulation.__file__).parent.parent
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
                        and node.module.startswith("mineproductivity.simulation")
                    ):
                        violations.append(f"{py_file}: from {node.module} import ...")
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith("mineproductivity.simulation"):
                                violations.append(f"{py_file}: import {alias.name}")
        assert not violations, f"Lower package(s) import simulation: {violations}"


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "exceptions",
            "metadata",
            "state",
            "result",
            "scenario",
            "run",
            "clock",
            "replay",
            "abstractions",
            "montecarlo",
            "discrete_event",
            "system_dynamics",
            "calibration",
            "_registry",
            "discovery",
            "persistence",
            "caching",
            "executor",
            "experiment",
            "comparison",
            "sensitivity",
        ]
        for name in submodules:
            module = importlib.import_module(f"mineproductivity.simulation.{name}")
            assert module is not None

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(simulation)
        assert "SimulationModel" in simulation.__all__
