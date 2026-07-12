"""Tests for mineproductivity.agents.workflow -- design spec §13's
decompose/run contract, §19's multi-agent worked example, and the §13
composition proofs over ``simulation.ExperimentRunner`` and
``optimization.OptimizationExecutor``/``PlanComparator``."""

from __future__ import annotations

import uuid
from datetime import timedelta
from pathlib import Path

import mineproductivity.agents.workflow as workflow_module
from mineproductivity.agents._registry import register
from mineproductivity.agents.abstractions import Agent, AgentContext
from mineproductivity.agents.audit import AgentAuditTrail
from mineproductivity.agents.executor import TaskExecutor
from mineproductivity.agents.goal import Goal
from mineproductivity.agents.metadata import AgentCategory, AgentMetadata
from mineproductivity.agents.policy import PolicyEngine
from mineproductivity.agents.result import AgentResult
from mineproductivity.agents.task import Task, TaskStatus
from mineproductivity.agents.workflow import WorkflowEngine
from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import InMemoryRepository


def _agent(category: AgentCategory, marker: str) -> str:
    code = f"{category.name}.Workflow{marker}{uuid.uuid4().hex[:8]}"

    @register
    class _WorkflowAgent(Agent):
        meta = AgentMetadata(
            code=code, category=category, description=f"Workflow fixture ({marker})."
        )

        def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
            return AgentResult(
                output={
                    "agent": type(self).meta.code,
                    "chain": task.state.attributes["delegation_chain"],
                }
            )

    return code


def _engine() -> tuple[InMemoryRepository[Task, str], AgentAuditTrail, WorkflowEngine]:
    repository: InMemoryRepository[Task, str] = InMemoryRepository()
    trail = AgentAuditTrail()
    executor = TaskExecutor(
        repository=repository,
        policy_engine=PolicyEngine(),
        audit_trail=trail,
        retry_policy=RetryPolicy(base_delay_s=0.0),
    )
    return repository, trail, WorkflowEngine(executor=executor, repository=repository)


class TestDecompose:
    def test_one_provisioned_task_per_named_agent_code(self) -> None:
        fleet = _agent(AgentCategory.FLEET, "Decompose")
        maintenance = _agent(AgentCategory.MAINTENANCE, "Decompose")
        repository, _, engine = _engine()
        goal = Goal(
            description="GOAL.DecomposeTest",
            success_criteria={"agent_codes": (fleet, maintenance), "target_tph": 1200.0},
        )
        tasks = engine.decompose(goal, context=AgentContext())
        assert [task.agent_code for task in tasks] == [fleet, maintenance]
        for task in tasks:
            stored = repository.get(task.id)
            assert stored.status is TaskStatus.SCHEDULED
            assert stored.goal_code == "GOAL.DecomposeTest"
            assert stored.state.attributes["target_tph"] == 1200.0

    def test_delegation_chain_is_carried_in_state_attributes(self) -> None:
        """Design spec §18: the chain is an open-mapping entry, never
        a new typed field on Task."""
        supervisor = _agent(AgentCategory.SHIFT_SUPERVISOR, "Chain")
        fleet = _agent(AgentCategory.FLEET, "Chain")
        _, _, engine = _engine()
        tasks = engine.decompose(
            Goal(
                description="GOAL.ChainTest",
                success_criteria={"agent_codes": (supervisor, fleet)},
            ),
            context=AgentContext(),
        )
        assert tasks[0].state.attributes["delegation_chain"] == (supervisor,)
        assert tasks[1].state.attributes["delegation_chain"] == (supervisor, fleet)

    def test_absent_agent_codes_decomposes_to_zero_tasks(self) -> None:
        _, _, engine = _engine()
        assert engine.decompose(Goal(description="GOAL.Empty"), context=AgentContext()) == ()
        assert engine.run(Goal(description="GOAL.Empty"), context=AgentContext()) == ()


class TestRun:
    def test_results_preserve_decomposition_order_and_are_audited(self) -> None:
        supervisor = _agent(AgentCategory.SHIFT_SUPERVISOR, "Run")
        fleet = _agent(AgentCategory.FLEET, "Run")
        maintenance = _agent(AgentCategory.MAINTENANCE, "Run")
        repository, trail, engine = _engine()
        results = engine.run(
            Goal(
                description="GOAL.RunTest",
                success_criteria={"agent_codes": (supervisor, fleet, maintenance)},
            ),
            context=AgentContext(),
        )
        assert [result.output["agent"] for result in results] == [
            supervisor,
            fleet,
            maintenance,
        ]
        assert len(trail.query()) == 3
        assert all(task.status is TaskStatus.COMPLETED for task in repository.list())


class TestMultiAgentCollaboration:
    def test_design_spec_19_worked_example_shape(self) -> None:
        """A ShiftSupervisor-category task coordinating a Fleet- and a
        Maintenance-category task, each producing its own audited
        AgentResult (design spec §19, §35)."""
        supervisor = _agent(AgentCategory.SHIFT_SUPERVISOR, "S19")
        fleet = _agent(AgentCategory.FLEET, "S19")
        maintenance = _agent(AgentCategory.MAINTENANCE, "S19")
        _, trail, engine = _engine()
        goal = Goal(
            description="Recover night-shift haulage throughput after a fleet breakdown",
            success_criteria={
                "agent_codes": (supervisor, fleet, maintenance),
                "target_tph": 1200.0,
            },
        )
        results = engine.run(goal, context=AgentContext())
        assert len(results) == 3
        for result in results[1:]:
            assert result.output["chain"][0] == supervisor
        audited_agents = {entry.agent_code for entry in trail.query()}
        assert audited_agents == {supervisor, fleet, maintenance}

    def test_no_category_behavior_is_hard_coded_into_the_orchestrators(self) -> None:
        """Design spec §19: category-specific reasoning lives
        exclusively in the registered Agent subclass."""
        import mineproductivity.agents.executor as executor_module

        for module in (workflow_module, executor_module):
            source = Path(module.__file__).read_text(encoding="utf-8")
            for member in AgentCategory:
                assert member.name not in source
                assert f'"{member.value}"' not in source


class TestHypothesisExplorationComposition:
    def test_a_scripted_task_composes_simulation_experiment_runner(self) -> None:
        """Design spec §13, §35: hypothesis exploration is
        ``simulation.ExperimentRunner.run_trials``, composed directly
        -- never reimplemented here."""
        from mineproductivity.events.store import _InMemoryEventStore
        from mineproductivity.simulation import (
            Experiment,
            ExperimentRunner,
            MonteCarloModel,
            Scenario,
            SimulationCategory,
            SimulationClock,
            SimulationContext,
            SimulationExecutor,
            SimulationMetadata,
            SimulationResult,
            SimulationRun,
            SimulationState,
            TimeProgressionMode,
        )
        from mineproductivity.simulation import register as sim_register
        from datetime import datetime, timezone

        @sim_register
        class _HypothesisModel(MonteCarloModel):
            meta = SimulationMetadata(
                code="MONTECARLO.AgentHypothesisFixture",
                category=SimulationCategory.MONTE_CARLO,
                description="Scores one hypothesis trial.",
            )

            def _trial(
                self, scenario: Scenario, *, context: SimulationContext, random_seed: int
            ) -> SimulationResult:
                return SimulationResult(
                    final_state=SimulationState(
                        attributes={"seed": random_seed},
                        simulated_time=datetime(2026, 7, 12, tzinfo=timezone.utc),
                    )
                )

        code = f"PLANNING.HypothesisExplorer{uuid.uuid4().hex[:8]}"

        @register
        class _HypothesisAgent(Agent):
            meta = AgentMetadata(
                code=code,
                category=AgentCategory.PLANNING,
                description="Explores hypotheses via ExperimentRunner.",
            )

            def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
                sim_repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
                runner = ExperimentRunner(
                    executor=SimulationExecutor(
                        repository=sim_repository,
                        clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED),
                    ),
                    repository=sim_repository,
                )
                experiment = runner.run_trials(
                    Scenario(
                        code="AGENT.HypothesisScenario",
                        model_code="MONTECARLO.AgentHypothesisFixture",
                        time_horizon=timedelta(hours=12),
                    ),
                    trials=4,
                    context=SimulationContext(event_store=_InMemoryEventStore()),
                )
                assert isinstance(experiment, Experiment)
                return AgentResult(output={"trials": len(experiment.run_ids)})

        _, _, engine = _engine()
        results = engine.run(
            Goal(
                description="GOAL.HypothesisExploration",
                success_criteria={"agent_codes": (code,)},
            ),
            context=AgentContext(),
        )
        assert results[0].output["trials"] == 4


class TestCandidatePlanSearchComposition:
    def test_a_scripted_task_composes_optimization_executor_and_comparator(self) -> None:
        """Design spec §13, §35: candidate-plan search is
        ``optimization.OptimizationExecutor``/``PlanComparator``,
        composed directly -- never reimplemented here."""
        from mineproductivity.optimization import (
            Constraint,
            ConstraintOperator,
            DecisionVariable,
            MixedIntegerProgrammingModel,
            Objective,
            ObjectiveDirection,
            OptimizationCategory,
            OptimizationContext,
            OptimizationExecutor,
            OptimizationMetadata,
            OptimizationProblem,
            OptimizationResult,
            OptimizationRun,
            OptimizationState,
            PlanComparator,
            VariableDomain,
        )
        from mineproductivity.optimization import register as opt_register

        @opt_register
        class _PlanSearchModel(MixedIntegerProgrammingModel):
            meta = OptimizationMetadata(
                code="MIP.AgentPlanSearchFixture",
                category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
                description="Echoes the first constraint bound as the optimum.",
            )

            def _solve_mip(
                self, problem: OptimizationProblem, *, context: OptimizationContext
            ) -> OptimizationResult:
                bound = problem.constraints[0].bound
                return OptimizationResult(objective_value=bound)

        code = f"PLANNING.PlanSearcher{uuid.uuid4().hex[:8]}"

        @register
        class _PlanSearchAgent(Agent):
            meta = AgentMetadata(
                code=code,
                category=AgentCategory.PLANNING,
                description="Searches candidate plans via OptimizationExecutor.",
            )

            def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
                opt_repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
                opt_executor = OptimizationExecutor(repository=opt_repository)
                outcomes = []
                for index, bound in enumerate((24.0, 27.0)):
                    run_id = f"{task.id}::candidate-{index}"
                    opt_repository.add(
                        OptimizationRun(
                            id=run_id,
                            problem_code="AGENT.PlanSearchProblem",
                            state=OptimizationState(attributes={"provisioned": True}),
                        )
                    )
                    outcomes.append(
                        opt_executor.execute(
                            run_id,
                            OptimizationProblem(
                                code="AGENT.PlanSearchProblem",
                                model_code="MIP.AgentPlanSearchFixture",
                                objectives=(
                                    Objective(name="tonnes", direction=ObjectiveDirection.MAXIMIZE),
                                ),
                                constraints=(
                                    Constraint(
                                        name="truck_budget",
                                        expression="trucks",
                                        operator=ConstraintOperator.LESS_EQUAL,
                                        bound=bound,
                                    ),
                                ),
                                variables=(
                                    DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),
                                ),
                            ),
                            context=OptimizationContext(),
                        )
                    )
                summaries = PlanComparator().compare({"candidates": outcomes})
                return AgentResult(
                    output={
                        "best": max(o.objective_value for o in outcomes if o.objective_value),
                        "mean": summaries["candidates"].mean,
                    }
                )

        _, _, engine = _engine()
        results = engine.run(
            Goal(
                description="GOAL.CandidatePlanSearch",
                success_criteria={"agent_codes": (code,)},
            ),
            context=AgentContext(),
        )
        assert results[0].output["best"] == 27.0
        assert results[0].output["mean"] == 25.5

    def test_repr(self) -> None:
        assert "WorkflowEngine" in repr(_engine()[2])
