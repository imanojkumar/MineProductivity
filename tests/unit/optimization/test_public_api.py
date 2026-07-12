"""Tests for the mineproductivity.optimization package's public API
surface, including the §35 mechanical proofs (no-fact-recomputation,
no-statistics-reimplementation, no-solver-coupling, no-architectural-
drift)."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import mineproductivity.optimization as optimization

FORBIDDEN_IMPORT_PREFIXES = (
    "mineproductivity.agents",
    "mineproductivity.visualization",
)

ALLOWED_TOP_LEVEL_DEPENDENCIES = {
    "optimization",
    "core",
    "events",
    "kpis",
    "analytics",
    "decision",
    "digital_twin",
    "simulation",
    "registry",
}

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
    "simulation",
)

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
    "SimulationExecutor",
    "ExperimentRunner",
}

FORBIDDEN_SOLVER_STRINGS = ("ortools", "pyomo", "pulp", "scipy")


class TestPublicApiSurface:
    def test_all_is_sorted_unique_and_importable(self) -> None:
        assert list(optimization.__all__) == sorted(optimization.__all__)
        assert len(optimization.__all__) == len(set(optimization.__all__))
        for name in optimization.__all__:
            assert hasattr(optimization, name)

    def test_exactly_the_design_spec_7_symbol_list(self) -> None:
        assert set(optimization.__all__) == {
            "OptimizationModel",
            "OptimizationContext",
            "OptimizationMetadata",
            "OptimizationCategory",
            "Objective",
            "ObjectiveDirection",
            "Constraint",
            "ConstraintOperator",
            "DecisionVariable",
            "VariableDomain",
            "OptimizationProblem",
            "ProblemStatus",
            "OptimizationRun",
            "RunStatus",
            "OptimizationExecutor",
            "OptimizationState",
            "LinearProgrammingModel",
            "MixedIntegerProgrammingModel",
            "ConstraintProgrammingModel",
            "MultiObjectiveModel",
            "EvolutionaryMetaheuristicModel",
            "NetworkOptimizationModel",
            "PlanComparator",
            "SensitivityAnalyzer",
            "by_category",
            "by_scope",
            "OptimizationRunRepository",
            "OptimizationResult",
            "ParetoResult",
            "register",
            "REGISTRY",
            "OptimizationValidationError",
            "OptimizationRunNotFoundError",
            "OptimizationExecutionError",
            "OptimizationVersionConflictError",
            "ProblemConflictError",
        }

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(optimization.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported.add(name)
        assert not (imported - set(optimization.__all__))


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        package_dir = Path(optimization.__file__).parent
        for py_file in package_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith(FORBIDDEN_IMPORT_PREFIXES)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES)

    def test_only_depends_on_currently_exercised_packages(self) -> None:
        package_dir = Path(optimization.__file__).parent
        for py_file in package_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module.startswith("mineproductivity.")
                ):
                    assert node.module.split(".")[1] in ALLOWED_TOP_LEVEL_DEPENDENCIES

    def test_no_fact_recomputation_engines_are_imported(self) -> None:
        """Design spec §35 proof 1."""
        package_dir = Path(optimization.__file__).parent
        for py_file in package_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        assert alias.name not in FORBIDDEN_COMPUTATION_SYMBOLS, (
                            f"{py_file.name} imports {alias.name}"
                        )

    def test_no_solver_coupling(self) -> None:
        """Design spec §17, §35: no module imports or even names
        OR-Tools, Pyomo, PuLP, or SciPy."""
        package_dir = Path(optimization.__file__).parent
        for py_file in package_dir.glob("*.py"):
            source = py_file.read_text(encoding="utf-8").lower()
            for solver in FORBIDDEN_SOLVER_STRINGS:
                assert solver not in source, f"{py_file.name} references {solver!r}"

    def test_no_statistics_reimplementation_in_comparison_or_sensitivity(self) -> None:
        """Design spec §35 proof 2."""
        package_dir = Path(optimization.__file__).parent
        for module_name in ("comparison.py", "sensitivity.py"):
            source = (package_dir / module_name).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=module_name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name not in {"statistics", "math", "numpy"}
            assert "sum(" not in source
            assert "/ len(" not in source

    def test_no_caching_module_exists(self) -> None:
        """Design spec §26's documented, deliberate non-need; §34's
        recorded anti-pattern against adding one 'for consistency'."""
        package_dir = Path(optimization.__file__).parent
        assert not (package_dir / "caching.py").exists()


class TestNoReverseDependency:
    def test_no_lower_package_imports_optimization(self) -> None:
        src_root = Path(optimization.__file__).parent.parent
        for package_name in LOWER_PACKAGES:
            package_dir = src_root / package_name
            if not package_dir.is_dir():
                continue
            for py_file in package_dir.rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        assert not node.module.startswith("mineproductivity.optimization")
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert not alias.name.startswith("mineproductivity.optimization")


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "exceptions",
            "metadata",
            "state",
            "result",
            "problem",
            "run",
            "abstractions",
            "linear_programming",
            "mixed_integer_programming",
            "constraint_programming",
            "multi_objective",
            "evolutionary",
            "network_optimization",
            "_registry",
            "discovery",
            "persistence",
            "executor",
            "comparison",
            "sensitivity",
        ]
        for name in submodules:
            assert importlib.import_module(f"mineproductivity.optimization.{name}")

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(optimization)
        assert "OptimizationModel" in optimization.__all__
