"""Tests for mineproductivity.agents.tool (design spec §17):
interface-only ABC contract plus the ToolMetadata/ToolInvocation value
objects."""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

import pytest

import mineproductivity.agents.tool as tool_module
from mineproductivity.agents.abstractions import AgentContext
from mineproductivity.agents.exceptions import AgentValidationError
from mineproductivity.agents.tool import Tool, ToolInvocation, ToolMetadata

_WHEN = datetime(2026, 7, 1, 6, 0, tzinfo=timezone.utc)


class TestToolMetadata:
    def test_name_defaults_to_code_and_version_defaults(self) -> None:
        meta = ToolMetadata(code="TOOL.DispatchQuery", description="Queries dispatch.")
        assert meta.name == "TOOL.DispatchQuery"
        assert meta.version == "1.0.0"

    def test_empty_code_raises(self) -> None:
        with pytest.raises(AgentValidationError, match="code"):
            ToolMetadata(code=" ", description="x")


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            Tool()  # type: ignore[abstract]

    def test_invoke_is_the_one_abstract_method(self) -> None:
        assert Tool.__abstractmethods__ == frozenset({"invoke"})

    def test_module_defines_no_concrete_subclass(self) -> None:
        """Design spec §35's interface-purity proof, module-local."""
        for _, obj in inspect.getmembers(tool_module, inspect.isclass):
            if issubclass(obj, Tool):
                assert inspect.isabstract(obj)


class TestToolValidatesItsOwnArguments:
    def test_a_conforming_tool_rejects_bad_arguments_independently(self) -> None:
        """Design spec §33: permission-checking authorizes that an
        action category may be attempted, not that every argument
        value is safe."""

        class _GuardedTool(Tool):
            meta = ToolMetadata(code="TOOL.GuardedFixture", description="x")

            def invoke(
                self, *, arguments: Mapping[str, Any], context: AgentContext
            ) -> Mapping[str, Any]:
                if "pit" not in arguments:
                    raise ValueError("pit is required")
                return {"ok": True}

        with pytest.raises(ValueError, match="pit"):
            _GuardedTool().invoke(arguments={}, context=AgentContext())
        assert _GuardedTool().invoke(arguments={"pit": "north"}, context=AgentContext()) == {
            "ok": True
        }


class TestToolInvocation:
    def test_mappings_are_frozen_and_copied(self) -> None:
        arguments = {"pit": "north"}
        invocation = ToolInvocation(
            tool_code="TOOL.DispatchQuery",
            arguments=arguments,
            result={"trucks": 12},
            invoked_at=_WHEN,
        )
        arguments["pit"] = "south"
        assert invocation.arguments["pit"] == "north"
        with pytest.raises(TypeError):
            invocation.result["trucks"] = 0  # type: ignore[index]
