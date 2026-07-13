"""A third-party-style ``Agent`` and ``Tool`` registered via entry
points into the package's two orthogonal registries (spec 11 §22, §31):

    [project.entry-points."mineproductivity.agents"]
    sitepack = "mineproductivity_sitepack.agents"
    [project.entry-points."mineproductivity.agents.tools"]
    sitepack = "mineproductivity_sitepack.tools"

``REGISTRY`` holds agent *types*; ``TOOLS`` holds tool *types* — never
merged. An ``Agent`` decides; a ``Tool`` acts at the agent's direction.
No LLM-provider SDK or external-system client lives in this repository;
both belong in the plugin (mechanically enforced).

Run: python examples/agents/05_plugin_agent_and_tool.py
"""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
from pathlib import Path

from mineproductivity.agents import (
    REGISTRY,
    TOOLS,
    AgentAuditTrail,
    AgentContext,
    AgentMetadata,
    PolicyEngine,
    Task,
    TaskExecutor,
    TaskState,
    TaskStatus,
    ToolMetadata,
)
from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import InMemoryRepository
from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec

_PLUGIN_SOURCE = '''\
"""A site pack's own agent and tool -- importing this module registers
both, exactly as a pip-installed plugin's entry-point scan would."""

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from mineproductivity.agents import (
    TOOLS,
    Agent,
    AgentCategory,
    AgentContext,
    AgentMetadata,
    AgentResult,
    Task,
    Tool,
    ToolInvocation,
    ToolMetadata,
    register,
    register_tool,
)


@register_tool
class DispatchQueryTool(Tool):
    """A site pack's dispatch-system query tool. A real one would call
    the external dispatch API here; this one returns a canned reading."""

    meta = ToolMetadata(code="TOOL.SitePackDispatchQuery", description="Queries dispatch.")

    def invoke(self, *, arguments: Mapping[str, Any], context: AgentContext) -> Mapping[str, Any]:
        return {"pit": arguments.get("pit", "north"), "idle_trucks": 4}


@register
class SitePackDispatchAgent(Agent):
    """A site pack's agent that consults its own tool, then decides."""

    meta = AgentMetadata(
        code="DISPATCH.SitePackReallocation",
        category=AgentCategory.DISPATCH,
        description="A site pack's dispatch reallocation agent.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        tool = TOOLS.get("TOOL.SitePackDispatchQuery")()
        reading = tool.invoke(arguments={"pit": "north"}, context=context)
        invocation = ToolInvocation(
            tool_code="TOOL.SitePackDispatchQuery",
            arguments={"pit": "north"},
            result=reading,
            invoked_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
        )
        return AgentResult(
            output={"idle_trucks": reading["idle_trucks"]}, tool_invocations=(invocation,)
        )
'''


def main() -> None:
    print("--- 1. agents ships zero concrete agents or tools (interface-only) ---")
    print(f"site-pack agents before: {sorted(c for c in REGISTRY if 'SitePack' in c)}")
    print(f"site-pack tools before:  {sorted(c for c in TOOLS if 'SitePack' in c)}")

    print()
    print("--- 2. A site pack declares both via pyproject.toml entry-points ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / "_example_sitepack_agents.py"
        plugin_path.write_text(_PLUGIN_SOURCE, encoding="utf-8")
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points

            def _fake_entry_points(*, group: str):  # type: ignore[no-untyped-def]
                if group in ("mineproductivity.agents", "mineproductivity.agents.tools"):
                    return (
                        importlib.metadata.EntryPoint(
                            name="sitepack", value="_example_sitepack_agents", group=group
                        ),
                    )
                return real_entry_points(group=group)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                discovery = EntryPointDiscovery()
                agents_result = discovery.discover(
                    EntryPointSpec(group="mineproductivity.agents", target_registry="agents")
                )
                tools_result = discovery.discover(
                    EntryPointSpec(
                        group="mineproductivity.agents.tools", target_registry="agents.tools"
                    )
                )
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop("_example_sitepack_agents", None)

    print(f"agents discover() is_ok: {agents_result.is_ok} loaded: {agents_result.value}")
    print(f"tools  discover() is_ok: {tools_result.is_ok} loaded: {tools_result.value}")
    agent_meta = REGISTRY.metadata_for("DISPATCH.SitePackReallocation").unwrap()
    tool_meta = TOOLS.metadata_for("TOOL.SitePackDispatchQuery").unwrap()
    assert isinstance(agent_meta, AgentMetadata)
    assert isinstance(tool_meta, ToolMetadata)
    print(f"registered agent: {agent_meta.code}; registered tool: {tool_meta.code}")

    print()
    print("--- 3. The discovered agent dispatches like any built-in, consulting its tool ---")
    task = Task(
        id="TASK-SITEPACK-1",
        goal_code="GOAL.SitePackReallocate",
        agent_code="DISPATCH.SitePackReallocation",
        state=TaskState(attributes={"pit": "north"}),
    )
    repository: InMemoryRepository[Task, str] = InMemoryRepository()
    repository.add(task)
    executor = TaskExecutor(
        repository=repository,
        policy_engine=PolicyEngine(),
        audit_trail=AgentAuditTrail(),
        retry_policy=RetryPolicy(base_delay_s=0.0),
    )
    result = executor.execute(task.id, task, context=AgentContext())
    print(f"agent output: {dict(result.output)}")
    print(f"tool invocations carried on the result: {len(result.tool_invocations)}")
    print(f"task status COMPLETED: {repository.get(task.id).status is TaskStatus.COMPLETED}")


if __name__ == "__main__":
    main()
