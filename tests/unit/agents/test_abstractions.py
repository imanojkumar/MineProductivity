"""Tests for mineproductivity.agents.abstractions (design spec §8):
the interface-only Agent ABC and the caller-assembled AgentContext."""

from __future__ import annotations

import inspect

import pytest

import mineproductivity.agents.abstractions as abstractions_module
from mineproductivity.agents.abstractions import Agent, AgentContext
from mineproductivity.agents.metadata import AgentCategory, AgentMetadata
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.state import TaskState
from mineproductivity.agents.task import Task
from mineproductivity.kpis import KPIResult


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            Agent()  # type: ignore[abstract]

    def test_act_is_the_one_shared_abstract_method(self) -> None:
        """Design spec §8: the shared-_act posture, mirroring
        decision.DecisionModel, not simulation's/optimization's
        no-shared-method posture."""
        assert Agent.__abstractmethods__ == frozenset({"_act"})

    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(abstractions_module, inspect.isclass):
            if issubclass(obj, Agent):
                assert inspect.isabstract(obj)


class TestStatelessness:
    def test_a_conforming_agent_mutates_no_instance_attribute(self) -> None:
        """Design spec §32: statefulness lives entirely in Task."""

        class _Stateless(Agent):
            meta = AgentMetadata(
                code="FLEET.StatelessFixture",
                category=AgentCategory.FLEET,
                description="x",
            )

            def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
                return AgentResult(output={"noted": task.id})

        agent = _Stateless()
        before = dict(getattr(agent, "__dict__", {}))
        task = Task(
            id="TASK-STATELESS",
            goal_code="G",
            agent_code="FLEET.StatelessFixture",
            state=TaskState(attributes={"provisioned": True}),
        )
        agent._act(task, context=AgentContext())
        assert dict(getattr(agent, "__dict__", {})) == before


class TestAgentContext:
    def test_every_evidence_field_defaults_empty(self) -> None:
        context = AgentContext()
        assert context.kpi_results == ()
        assert context.analytics_results == ()
        assert context.decision_results == ()
        assert context.twin_snapshot is None
        assert context.simulation_results == ()
        assert context.optimization_results == ()

    def test_sequences_are_coerced_to_tuples_once_at_construction(self) -> None:
        """Design spec §27, §36: evidence assembly happens once, at
        construction -- a later mutation of the source list never
        reaches the context."""
        source = [KPIResult(code="UTIL.OEE", value=0.71, unit="ratio")]
        context = AgentContext(kpi_results=source)
        source.append(KPIResult(code="UTIL.OEE", value=0.99, unit="ratio"))
        assert len(context.kpi_results) == 1

    def test_repr_names_all_six_evidence_fields(self) -> None:
        rendered = repr(AgentContext())
        for field in (
            "kpi_results",
            "analytics_results",
            "decision_results",
            "twin_snapshot",
            "simulation_results",
            "optimization_results",
        ):
            assert field in rendered
