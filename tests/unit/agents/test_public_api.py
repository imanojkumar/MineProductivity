"""Tests for the mineproductivity.agents package's public API surface,
including the §35 mechanical proofs (no-fact-recomputation,
interface-purity, no-architectural-drift, no-provider-coupling)."""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import mineproductivity.agents as agents
from mineproductivity.agents.abstractions import Agent
from mineproductivity.agents.memory import AgentMemory
from mineproductivity.agents.tool import Tool

FORBIDDEN_IMPORT_PREFIXES = ("mineproductivity.visualization",)

ALLOWED_TOP_LEVEL_DEPENDENCIES = {
    "agents",
    "core",
    "events",
    "registry",
    "connectors",
    "kpis",
    "analytics",
    "decision",
    "digital_twin",
    "simulation",
    "optimization",
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
}

# Design spec §35 proof 5 -- checked lowercase against every module's
# full source, so even a string reference trips the scan.
FORBIDDEN_PROVIDER_STRINGS = (
    "openai",
    "anthropic",
    "google.generativeai",
    "gemini",
    "llama",
    "mistral",
    "langchain",
)


class TestPublicApiSurface:
    def test_all_is_sorted_unique_and_importable(self) -> None:
        assert list(agents.__all__) == sorted(agents.__all__)
        assert len(agents.__all__) == len(set(agents.__all__))
        for name in agents.__all__:
            assert hasattr(agents, name)

    def test_exactly_the_design_spec_7_symbol_list(self) -> None:
        assert set(agents.__all__) == {
            "Agent",
            "AgentContext",
            "AgentMetadata",
            "AgentCategory",
            "Permission",
            "AgentCapabilitySet",
            "AgentPolicy",
            "PolicyStatus",
            "PolicyEngine",
            "Task",
            "TaskStatus",
            "TaskState",
            "AgentMemory",
            "ConversationTurn",
            "ConversationContext",
            "ApprovalRequest",
            "ApprovalStatus",
            "Tool",
            "ToolMetadata",
            "ToolInvocation",
            "AgentMessage",
            "DelegationRequest",
            "Goal",
            "WorkflowEngine",
            "TaskExecutor",
            "AgentResult",
            "AgentAuditTrail",
            "AgentAuditEntry",
            "by_category",
            "by_scope",
            "TaskRepository",
            "register",
            "register_tool",
            "REGISTRY",
            "TOOLS",
            "AgentValidationError",
            "TaskNotFoundError",
            "AgentExecutionError",
            "AgentVersionConflictError",
            "PolicyConflictError",
            "PermissionDeniedError",
        }

    def test_every_imported_symbol_is_exported_in_all(self) -> None:
        init_path = Path(agents.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    name = alias.asname or alias.name
                    if not name.startswith("_"):
                        imported.add(name)
        assert not (imported - set(agents.__all__))


class TestNoForbiddenDependencies:
    def test_no_submodule_imports_a_higher_layer_package(self) -> None:
        """Design spec §5: agents imports nothing above itself --
        visualization does not exist yet and never will be imported
        here."""
        package_dir = Path(agents.__file__).parent
        for py_file in package_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith(FORBIDDEN_IMPORT_PREFIXES)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES)

    def test_only_depends_on_currently_exercised_packages(self) -> None:
        package_dir = Path(agents.__file__).parent
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
        """Design spec §35 proof 1: every KPI/statistical/decision/
        twin-state/simulation/solved-plan value arrives via a lower
        package's result types, never a lower engine run here."""
        package_dir = Path(agents.__file__).parent
        for py_file in package_dir.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        assert alias.name not in FORBIDDEN_COMPUTATION_SYMBOLS, (
                            f"{py_file.name} imports {alias.name}"
                        )

    def test_no_llm_provider_coupling(self) -> None:
        """Design spec §35 proof 5: no module imports, or contains a
        string reference to, any LLM provider SDK."""
        package_dir = Path(agents.__file__).parent
        for py_file in package_dir.glob("*.py"):
            source = py_file.read_text(encoding="utf-8").lower()
            for provider in FORBIDDEN_PROVIDER_STRINGS:
                assert provider not in source, f"{py_file.name} references {provider!r}"

    def test_no_caching_module_exists(self) -> None:
        """Design spec §27's documented, deliberate non-need; §34's
        recorded anti-pattern against adding one 'for consistency'."""
        package_dir = Path(agents.__file__).parent
        assert not (package_dir / "caching.py").exists()


class TestInterfacePurity:
    def test_agent_tool_and_memory_have_zero_concrete_subclasses_in_src(self) -> None:
        """Design spec §35 proof 3, mechanically over every module."""
        package_dir = Path(agents.__file__).parent
        for py_file in package_dir.glob("*.py"):
            module_name = f"mineproductivity.agents.{py_file.stem}"
            if py_file.stem == "__init__":
                module_name = "mineproductivity.agents"
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module.__name__:
                    continue
                if issubclass(obj, (Agent, Tool, AgentMemory)):
                    assert inspect.isabstract(obj), f"{module_name}.{obj.__name__} is concrete"


class TestNoReverseDependency:
    def test_no_lower_package_imports_agents(self) -> None:
        """Design spec §5: the optimization-package precedent for this
        test, extended one layer up."""
        src_root = Path(agents.__file__).parent.parent
        for package_name in LOWER_PACKAGES:
            package_dir = src_root / package_name
            if not package_dir.is_dir():
                continue
            for py_file in package_dir.rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        assert not node.module.startswith("mineproductivity.agents")
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert not alias.name.startswith("mineproductivity.agents")


class TestNoCircularImports:
    def test_every_submodule_imports_cleanly_in_isolation(self) -> None:
        submodules = [
            "exceptions",
            "metadata",
            "state",
            "task",
            "capability",
            "policy",
            "abstractions",
            "memory",
            "conversation",
            "approval",
            "tool",
            "communication",
            "goal",
            "result",
            "audit",
            "workflow",
            "executor",
            "discovery",
            "persistence",
            "_registry",
        ]
        for name in submodules:
            assert importlib.import_module(f"mineproductivity.agents.{name}")

    def test_package_reimport_is_idempotent(self) -> None:
        importlib.reload(agents)
        assert "Agent" in agents.__all__
