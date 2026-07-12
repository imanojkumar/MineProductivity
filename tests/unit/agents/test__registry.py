"""Tests for mineproductivity.agents._registry (design spec §22, §31):
two orthogonal registries, never merged, plus the entry-point plugin
path for both groups."""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

import mineproductivity.agents as agents
from mineproductivity.agents._registry import REGISTRY, TOOLS, register, register_tool
from mineproductivity.agents.abstractions import Agent, AgentContext
from mineproductivity.agents.exceptions import (
    AgentValidationError,
    AgentVersionConflictError,
)
from mineproductivity.agents.metadata import AgentCategory, AgentMetadata
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.task import Task
from mineproductivity.agents.tool import Tool, ToolMetadata
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec, UnregisteredLookupError


def _agent_meta(code: str) -> AgentMetadata:
    return AgentMetadata(code=code, category=AgentCategory.FLEET, description="x")


def _unique_agent_code() -> str:
    return f"FLEET.RegistryFixture{uuid.uuid4().hex}"


class _FixtureAgent(Agent):
    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        return AgentResult()


class _FixtureTool(Tool):
    def invoke(self, *, arguments: Mapping[str, Any], context: AgentContext) -> Mapping[str, Any]:
        return {}


class TestNoBuiltInAgentsOrToolsShipped:
    def test_no_module_in_the_package_registers_anything(self) -> None:
        """Design spec §8, §14, §17: interface-only throughout."""
        package_dir = Path(agents.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "_registry.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            assert "@register" not in source, f"{py_file.name} registers a built-in"


class TestTwoOrthogonalRegistries:
    def test_registry_and_tools_are_distinct_instances(self) -> None:
        """Design spec §22: never merged into one."""
        assert REGISTRY is not TOOLS

    def test_an_agent_registration_never_appears_in_tools(self) -> None:
        code = _unique_agent_code()

        class _AnAgent(_FixtureAgent):
            meta = _agent_meta(code)

        register(_AnAgent)
        assert REGISTRY.get(code) is _AnAgent
        with pytest.raises(UnregisteredLookupError):
            TOOLS.get(code)

    def test_a_tool_registration_never_appears_in_registry(self) -> None:
        code = f"TOOL.RegistryFixture{uuid.uuid4().hex}"

        class _ATool(_FixtureTool):
            meta = ToolMetadata(code=code, description="x")

        register_tool(_ATool)
        assert TOOLS.get(code) is _ATool
        with pytest.raises(UnregisteredLookupError):
            REGISTRY.get(code)


class TestRegisterDecorators:
    def test_register_returns_the_class_unchanged(self) -> None:
        code = _unique_agent_code()

        class _AnAgent(_FixtureAgent):
            meta = _agent_meta(code)

        assert register(_AnAgent) is _AnAgent
        assert REGISTRY.metadata_for(code).unwrap() is _AnAgent.meta

    def test_empty_agent_code_raises(self) -> None:
        class _FakeMeta:
            code = ""

        class _AnAgent(_FixtureAgent):
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(AgentValidationError):
            register(_AnAgent)

    def test_empty_tool_code_raises(self) -> None:
        class _FakeMeta:
            code = ""

        class _ATool(_FixtureTool):
            meta = _FakeMeta()  # type: ignore[assignment]

        with pytest.raises(AgentValidationError):
            register_tool(_ATool)

    def test_duplicate_agent_code_raises_version_conflict(self) -> None:
        shared = _agent_meta(_unique_agent_code())

        class _First(_FixtureAgent):
            meta = shared

        register(_First)

        class _Second(_FixtureAgent):
            meta = shared

        with pytest.raises(AgentVersionConflictError):
            register(_Second)

    def test_duplicate_tool_code_raises_version_conflict(self) -> None:
        shared = ToolMetadata(code=f"TOOL.Conflict{uuid.uuid4().hex}", description="x")

        class _First(_FixtureTool):
            meta = shared

        register_tool(_First)

        class _Second(_FixtureTool):
            meta = shared

        with pytest.raises(AgentVersionConflictError):
            register_tool(_Second)


_AGENT_PLUGIN_SOURCE = '''\
"""A third-party reasoning-backend plugin -- importing this module
registers it, exactly as a pip-installed entry-point scan would
(spec 11 §31)."""

from mineproductivity.agents import (
    Agent,
    AgentCategory,
    AgentContext,
    AgentMetadata,
    AgentResult,
    Task,
    register,
)


@register
class SitePackFleetAgent(Agent):
    """A site pack fleet reasoning-backend fixture."""

    meta = AgentMetadata(
        code="FLEET.SitePackAgentFixture",
        category=AgentCategory.FLEET,
        description="A site pack fleet reasoning-backend fixture.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        return AgentResult(output={"plugin": True})
'''

_TOOL_PLUGIN_SOURCE = '''\
"""A third-party tool-integration plugin (spec 11 §31)."""

from collections.abc import Mapping
from typing import Any

from mineproductivity.agents import AgentContext, Tool, ToolMetadata, register_tool


@register_tool
class SitePackDispatchTool(Tool):
    """A site pack dispatch-query tool fixture."""

    meta = ToolMetadata(
        code="TOOL.SitePackToolFixture",
        description="A site pack dispatch-query tool fixture.",
    )

    def invoke(self, *, arguments: Mapping[str, Any], context: AgentContext) -> Mapping[str, Any]:
        return {"ok": True}
'''


def _discover_with_fixture(module_name: str, source: str, group: str, target: str) -> Any:
    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / f"{module_name}.py"
        plugin_path.write_text(source, encoding="utf-8")
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points
            wanted_group = group

            def _fake_entry_points(*, group: str = "", **kwargs: Any) -> Any:
                if group == wanted_group:
                    return (
                        importlib.metadata.EntryPoint(
                            name="sitepack", value=module_name, group=group
                        ),
                    )
                return real_entry_points(group=group, **kwargs)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                return EntryPointDiscovery().discover(
                    EntryPointSpec(group=group, target_registry=target)
                )
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop(module_name, None)


class TestPluginEntryPointPaths:
    def test_agent_plugin_registered_via_real_entry_point_discovery(self) -> None:
        result = _discover_with_fixture(
            "_agents_plugin_fixture",
            _AGENT_PLUGIN_SOURCE,
            "mineproductivity.agents",
            "agents",
        )
        assert result.is_ok
        assert "FLEET.SitePackAgentFixture" in REGISTRY

    def test_tool_plugin_discoverable_independently_of_the_agent_fixture(self) -> None:
        result = _discover_with_fixture(
            "_agents_tool_fixture",
            _TOOL_PLUGIN_SOURCE,
            "mineproductivity.agents.tools",
            "agents.tools",
        )
        assert result.is_ok
        assert "TOOL.SitePackToolFixture" in TOOLS
        assert "TOOL.SitePackToolFixture" not in REGISTRY
