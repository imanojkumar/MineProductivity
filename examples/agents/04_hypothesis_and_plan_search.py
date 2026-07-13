"""A planning agent that composes two lower layers directly (design
spec §13): hypothesis exploration via ``simulation.ExperimentRunner``
and candidate-plan search via ``optimization.OptimizationExecutor`` +
``PlanComparator``. The agent orchestrates; it never reimplements a
simulation or an optimization — and ``agents`` never constructs a
``SimulationRun``/``OptimizationRun`` in its own package code (the
composition lives in the concrete agent, spec 11 §13).

The concrete models and agent are example-local.

Run: python examples/agents/04_hypothesis_and_plan_search.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.agents import (
    Agent,
    AgentAuditTrail,
    AgentCategory,
    AgentContext,
    AgentMetadata,
    AgentResult,
    Goal,
    PolicyEngine,
    Task,
    TaskExecutor,
    WorkflowEngine,
    register,
)
from mineproductivity.connectors import RetryPolicy
from mineproductivity.core import InMemoryRepository
from mineproductivity.events.store import _InMemoryEventStore
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
from mineproductivity.simulation import (
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

NOW = datetime(2026, 7, 12, tzinfo=timezone.utc)


@sim_register
class HypothesisModel(MonteCarloModel):
    """Scores one throughput hypothesis per trial (example-local)."""

    meta = SimulationMetadata(
        code="MONTECARLO.PlanningHypothesis",
        category=SimulationCategory.MONTE_CARLO,
        description="Scores one throughput hypothesis per trial.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        return SimulationResult(
            final_state=SimulationState(
                attributes={"seed": random_seed}, simulated_time=NOW + scenario.time_horizon
            )
        )


@opt_register
class PlanSearchModel(MixedIntegerProgrammingModel):
    """Echoes the truck budget as the optimum (example-local)."""

    meta = OptimizationMetadata(
        code="MIP.PlanningCandidateSearch",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="Echoes the truck budget as the optimal tonnage.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        return OptimizationResult(objective_value=problem.constraints[0].bound)


@register
class PlanningAgent(Agent):
    """Explores hypotheses, then searches candidate plans — composing
    ``simulation`` and ``optimization`` directly (example-local)."""

    meta = AgentMetadata(
        code="PLANNING.HaulageStrategist",
        category=AgentCategory.PLANNING,
        description="Explores hypotheses and searches candidate haulage plans.",
    )

    def _act(self, task: Task, *, context: AgentContext) -> AgentResult:
        trials = self._explore_hypotheses()
        best, mean = self._search_plans()
        return AgentResult(
            output={"hypothesis_trials": trials, "best_plan": best, "mean_plan": mean}
        )

    @staticmethod
    def _explore_hypotheses() -> int:
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
                code="PLANNING.HypothesisScenario",
                model_code="MONTECARLO.PlanningHypothesis",
                time_horizon=timedelta(hours=12),
            ),
            trials=6,
            context=SimulationContext(event_store=_InMemoryEventStore()),
        )
        return len(experiment.run_ids)

    @staticmethod
    def _search_plans() -> tuple[float, float]:
        opt_repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
        opt_executor = OptimizationExecutor(repository=opt_repository)
        outcomes: list[OptimizationResult] = []
        for index, budget in enumerate((24.0, 27.0, 30.0)):
            run_id = f"PLAN::candidate-{index}"
            opt_repository.add(
                OptimizationRun(
                    id=run_id,
                    problem_code="PLANNING.CandidateProblem",
                    state=OptimizationState(attributes={"provisioned": True}),
                )
            )
            outcomes.append(
                opt_executor.execute(
                    run_id,
                    OptimizationProblem(
                        code="PLANNING.CandidateProblem",
                        model_code="MIP.PlanningCandidateSearch",
                        objectives=(
                            Objective(name="tonnes", direction=ObjectiveDirection.MAXIMIZE),
                        ),
                        constraints=(
                            Constraint(
                                name="truck_budget",
                                expression="trucks",
                                operator=ConstraintOperator.LESS_EQUAL,
                                bound=budget,
                            ),
                        ),
                        variables=(DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),),
                    ),
                    context=OptimizationContext(),
                )
            )
        values = [o.objective_value for o in outcomes if o.objective_value is not None]
        mean = PlanComparator().compare({"candidates": outcomes})["candidates"].mean
        return max(values), mean


def main() -> None:
    print("--- A planning agent composes simulation + optimization directly ---")
    repository: InMemoryRepository[Task, str] = InMemoryRepository()
    engine = WorkflowEngine(
        executor=TaskExecutor(
            repository=repository,
            policy_engine=PolicyEngine(),
            audit_trail=AgentAuditTrail(),
            retry_policy=RetryPolicy(base_delay_s=0.0),
        ),
        repository=repository,
    )
    results = engine.run(
        Goal(
            description="GOAL.PlanNightShiftHaulage",
            success_criteria={"agent_codes": ("PLANNING.HaulageStrategist",)},
        ),
        context=AgentContext(),
    )
    output = results[0].output
    print(f"hypothesis trials run: {output['hypothesis_trials']}")
    print(f"best candidate plan (tonnes): {output['best_plan']}")
    print(f"mean candidate plan (analytics-computed): {output['mean_plan']}")


if __name__ == "__main__":
    main()
