"""Tests for the mineproductivity.visualization package's public API
surface, including the §33 mechanical proofs (no-fact-recomputation,
interface-purity, no-architectural-drift, no-backend-coupling)."""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import mineproductivity.visualization as visualization
from mineproductivity.visualization.abstractions import Visualization
from mineproductivity.visualization.renderer import Renderer

ALLOWED_TOP_LEVEL_DEPENDENCIES = {
    "visualization",
    "core",
    "registry",
    "kpis",
    "analytics",
    "decision",
    "digital_twin",
    "simulation",
    "optimization",
    "agents",
    "events",
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
    "optimization",
    "agents",
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
    "OptimizationExecutor",
    "PlanComparator",
    "SensitivityAnalyzer",
    "TaskExecutor",
    "WorkflowEngine",
    "PolicyEngine",
}

# Design spec §33 proof 5 -- checked lowercase against every module's
# full source, so even a string reference trips the scan.
FORBIDDEN_BACKEND_STRINGS = (
    "plotly",
    "matplotlib",
    "jinja2",
    "weasyprint",
    "bokeh",
    "seaborn",
    "altair",
    "reportlab",
)


class TestPublicApiSurface:
    def test_all_is_sorted_unique_and_importable(self) -> None:
        assert list(visualization.__all__) == sorted(visualization.__all__)
        assert len(visualization.__all__) == len(set(visualization.__all__))
        for name in visualization.__all__:
            assert hasattr(visualization, name)

    def test_exactly_the_design_spec_7_symbol_list(self) -> None:
        assert set(visualization.__all__) == {
            "Visualization",
            "VisualizationContext",
            "PresentationModel",
            "Theme",
            "Layout",
            "Widget",
            "Dashboard",
            "DashboardBuilder",
            "Report",
            "ReportBuilder",
            "RenderingPipeline",
            "Renderer",
            "RendererMetadata",
            "RenderedOutput",
            "ExportRequest",
            "ExportResult",
            "by_theme",
            "by_owner",
            "DashboardRepository",
            "register",
            "register_renderer",
            "REGISTRY",
            "RENDERERS",
            "VisualizationMetadata",
            "VisualizationCategory",
            "VisualizationValidationError",
            "DashboardNotFoundError",
            "RenderingError",
            "VisualizationVersionConflictError",
        }

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(visualization.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported.add(name)
        assert not (imported - set(visualization.__all__))


class TestNoForbiddenDependencies:
    def test_only_depends_on_currently_exercised_packages(self) -> None:
        """Design spec §5: visualization imports nothing above itself
        -- no future package exists."""
        package_dir = Path(visualization.__file__).parent
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
        """Design spec §33 proof 1: every KPI/statistical/decision/
        twin-state/simulation/solved-plan/agent-decision value arrives
        via a lower package's result types, never a lower engine run
        here."""
        package_dir = Path(visualization.__file__).parent
        for py_file in package_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        assert alias.name not in FORBIDDEN_COMPUTATION_SYMBOLS, (
                            f"{py_file.name} imports {alias.name}"
                        )

    def test_no_charting_or_templating_backend_coupling(self) -> None:
        """Design spec §33 proof 5: no module imports, or contains a
        string reference to, a charting/templating/document-generation
        library."""
        package_dir = Path(visualization.__file__).parent
        for py_file in package_dir.glob("*.py"):
            source = py_file.read_text(encoding="utf-8").lower()
            for backend in FORBIDDEN_BACKEND_STRINGS:
                assert backend not in source, f"{py_file.name} references {backend!r}"

    def test_no_caching_module_exists(self) -> None:
        """Design spec §24's documented, deliberate non-need; §32's
        recorded anti-pattern against adding one 'for consistency'."""
        package_dir = Path(visualization.__file__).parent
        assert not (package_dir / "caching.py").exists()


class TestInterfacePurity:
    def test_visualization_and_renderer_have_zero_concrete_subclasses_in_src(self) -> None:
        """Design spec §33 proof 3, mechanically over every module."""
        package_dir = Path(visualization.__file__).parent
        for py_file in package_dir.glob("*.py"):
            module_name = f"mineproductivity.visualization.{py_file.stem}"
            if py_file.stem == "__init__":
                module_name = "mineproductivity.visualization"
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module.__name__:
                    continue
                if issubclass(obj, (Visualization, Renderer)):
                    assert inspect.isabstract(obj), f"{module_name}.{obj.__name__} is concrete"


class TestNoReverseDependency:
    def test_no_lower_package_imports_visualization(self) -> None:
        """Design spec §5: the agents-package precedent for this test,
        extended one final layer up."""
        src_root = Path(visualization.__file__).parent.parent
        for package_name in LOWER_PACKAGES:
            package_dir = src_root / package_name
            if not package_dir.is_dir():
                continue
            for py_file in package_dir.rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        assert not node.module.startswith("mineproductivity.visualization")
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert not alias.name.startswith("mineproductivity.visualization")


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "exceptions",
            "abstractions",
            "presentation",
            "theme",
            "layout",
            "widget",
            "dashboard",
            "dashboard_builder",
            "report",
            "report_builder",
            "renderer",
            "pipeline",
            "export",
            "discovery",
            "persistence",
            "_registry",
        ]
        for name in submodules:
            assert importlib.import_module(f"mineproductivity.visualization.{name}")

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(visualization)
        assert "Visualization" in visualization.__all__
