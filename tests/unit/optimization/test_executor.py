"""Tests for mineproductivity.optimization.executor -- design spec
§10's dispatch/persistence sequence, both single-shot and iterative
branches, the §11/§14 pairing rules, and the §17 candidate-scenario
search composed over ``simulation.ExperimentRunner``."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.core import InMemoryRepository, NotFoundError
from mineproductivity.optimization._registry import register
from mineproductivity.optimization.abstractions import OptimizationContext
from mineproductivity.optimization.evolutionary import EvolutionaryMetaheuristicModel
from mineproductivity.optimization.exceptions import (
    OptimizationExecutionError,
    OptimizationRunNotFoundError,
    OptimizationValidationError,
)
from mineproductivity.optimization.executor import OptimizationExecutor
from mineproductivity.optimization.linear_programming import LinearProgrammingModel
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata
from mineproductivity.optimization.mixed_integer_programming import (
    MixedIntegerProgrammingModel,
)
from mineproductivity.optimization.multi_objective import MultiObjectiveModel
from mineproductivity.optimization.problem import (
    Constraint,
    ConstraintOperator,
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationProblem,
    VariableDomain,
)
from mineproductivity.optimization.result import OptimizationResult, ParetoResult
from mineproductivity.optimization.run import OptimizationRun, RunStatus
from mineproductivity.optimization.state import OptimizationState


@register
class _BoundEchoMip(MixedIntegerProgrammingModel):
    meta = OptimizationMetadata(
        code="MIP.ExecutorBoundEcho",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="Echoes the first constraint bound as the optimum.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        bound = problem.constraints[0].bound if problem.constraints else 0.0
        return OptimizationResult(
            objective_value=bound, solution={problem.variables[0].name: bound}
        )


@register
class _InfeasibleMip(MixedIntegerProgrammingModel):
    meta = OptimizationMetadata(
        code="MIP.ExecutorInfeasible",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="Reports infeasibility for every problem.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        return OptimizationResult(
            feasible=False, warnings=("constraint set admits no feasible point",)
        )


@register
class _RaisingMip(MixedIntegerProgrammingModel):
    meta = OptimizationMetadata(
        code="MIP.ExecutorRaises",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="Raises for every problem.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        raise RuntimeError("solver blew up")


@register
class _LpFixture(LinearProgrammingModel):
    meta = OptimizationMetadata(
        code="LP.ExecutorFixture",
        category=OptimizationCategory.LINEAR_PROGRAMMING,
        description="A trivial LP fixture.",
    )

    def _solve_lp(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        return OptimizationResult(objective_value=1.0)


@register
class _ParetoFixture(MultiObjectiveModel):
    meta = OptimizationMetadata(
        code="MULTIOBJECTIVE.ExecutorFixture",
        category=OptimizationCategory.MULTI_OBJECTIVE,
        description="A two-point Pareto front fixture.",
    )

    def _solve_pareto(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> ParetoResult:
        return ParetoResult(
            front=(
                OptimizationResult(objective_value=1.0),
                OptimizationResult(objective_value=2.0),
            )
        )


@register
class _ConvergingEvo(EvolutionaryMetaheuristicModel):
    meta = OptimizationMetadata(
        code="EVOLUTIONARY.ExecutorConverging",
        category=OptimizationCategory.EVOLUTIONARY_METAHEURISTIC,
        description="Halves the gap each iteration until converged.",
    )

    def _iterate(
        self,
        problem: OptimizationProblem,
        state: OptimizationState,
        *,
        context: OptimizationContext,
    ) -> OptimizationState:
        gap = float(state.attributes.get("gap", 8.0))
        next_gap = gap // 2  # integer halving converges to a fixed point
        if next_gap == gap:
            return state
        return OptimizationState(
            attributes={
                "gap": next_gap,
                "objective_value": 100.0 - next_gap,
                "solution": {"x": next_gap},
            }
        )


def _objective() -> Objective:
    return Objective(name="tonnes", direction=ObjectiveDirection.MAXIMIZE)


def _problem(model_code: str = "MIP.ExecutorBoundEcho", **overrides: object) -> OptimizationProblem:
    fields: dict[str, object] = {
        "code": "TEST.ExecutorProblem",
        "model_code": model_code,
        "objectives": (_objective(),),
        "constraints": (
            Constraint(
                name="truck_budget",
                expression="trucks",
                operator=ConstraintOperator.LESS_EQUAL,
                bound=27.0,
            ),
        ),
        "variables": (DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),),
    }
    fields.update(overrides)
    return OptimizationProblem(**fields)  # type: ignore[arg-type]


def _provisioned(
    run_id: str = "RUN-1", *, status: RunStatus = RunStatus.SCHEDULED
) -> tuple[InMemoryRepository[OptimizationRun, str], OptimizationExecutor]:
    repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    repository.add(
        OptimizationRun(
            id=run_id,
            problem_code="TEST.ExecutorProblem",
            state=OptimizationState(attributes={"provisioned": True}),
            status=status,
        )
    )
    return repository, OptimizationExecutor(repository=repository)


class TestSingleShotDispatch:
    def test_mip_happy_path_completes_and_stamps_the_run_id(self) -> None:
        repository, executor = _provisioned()
        result = executor.execute("RUN-1", _problem(), context=OptimizationContext())
        assert result.run_id == "RUN-1"
        assert result.objective_value == 27.0
        assert result.solution["trucks"] == 27.0
        assert repository.get("RUN-1").status is RunStatus.COMPLETED

    def test_lp_and_pareto_categories_dispatch_to_their_own_methods(self) -> None:
        _, executor = _provisioned()
        lp_problem = _problem(
            "LP.ExecutorFixture",
            variables=(DecisionVariable(name="x", domain=VariableDomain.CONTINUOUS),),
        )
        assert executor.execute("RUN-1", lp_problem, context=OptimizationContext()).feasible

        repository2, executor2 = _provisioned("RUN-2")
        pareto_problem = _problem(
            "MULTIOBJECTIVE.ExecutorFixture",
            objectives=(
                _objective(),
                Objective(name="cost", direction=ObjectiveDirection.MINIMIZE),
            ),
        )
        result = executor2.execute("RUN-2", pareto_problem, context=OptimizationContext())
        assert isinstance(result, ParetoResult)
        assert len(result.front) == 2

    def test_infeasible_flows_through_never_raises(self) -> None:
        repository, executor = _provisioned()
        result = executor.execute(
            "RUN-1", _problem("MIP.ExecutorInfeasible"), context=OptimizationContext()
        )
        assert result.feasible is False
        assert result.warnings
        assert repository.get("RUN-1").status is RunStatus.COMPLETED

    def test_model_failure_marks_the_run_failed_and_raises(self) -> None:
        repository, executor = _provisioned()
        with pytest.raises(OptimizationExecutionError, match="ExecutorRaises"):
            executor.execute("RUN-1", _problem("MIP.ExecutorRaises"), context=OptimizationContext())
        assert repository.get("RUN-1").status is RunStatus.FAILED


class TestGuards:
    def test_unknown_run_and_unknown_model_raise_not_found(self) -> None:
        _, executor = _provisioned()
        with pytest.raises(OptimizationRunNotFoundError, match="NO-SUCH"):
            executor.execute("NO-SUCH", _problem(), context=OptimizationContext())
        with pytest.raises(OptimizationRunNotFoundError, match="No OptimizationModel"):
            executor.execute(
                "RUN-1", _problem("MIP.NeverRegistered"), context=OptimizationContext()
            )

    def test_terminal_runs_are_skipped_with_a_warning(self) -> None:
        for terminal in (RunStatus.COMPLETED, RunStatus.FAILED):
            _, executor = _provisioned(status=terminal)
            result = executor.execute("RUN-1", _problem(), context=OptimizationContext())
            assert f"{terminal.value} is terminal" in result.warnings[0]

    def test_paused_resumes_and_completes(self) -> None:
        repository, executor = _provisioned(status=RunStatus.PAUSED)
        executor.execute("RUN-1", _problem(), context=OptimizationContext())
        assert repository.get("RUN-1").status is RunStatus.COMPLETED

    def test_lp_category_rejects_non_continuous_variables(self) -> None:
        """Design spec §11's variable-domain rule."""
        _, executor = _provisioned()
        with pytest.raises(OptimizationValidationError, match="non-continuous"):
            executor.execute("RUN-1", _problem("LP.ExecutorFixture"), context=OptimizationContext())

    def test_multi_objective_category_requires_two_or_more_objectives(self) -> None:
        """Design spec §14's objective-count rule, both directions."""
        _, executor = _provisioned()
        with pytest.raises(OptimizationValidationError, match="single objective"):
            executor.execute(
                "RUN-1",
                _problem("MULTIOBJECTIVE.ExecutorFixture"),
                context=OptimizationContext(),
            )
        with pytest.raises(OptimizationValidationError, match="2 objectives"):
            executor.execute(
                "RUN-1",
                _problem(
                    objectives=(
                        _objective(),
                        Objective(name="cost", direction=ObjectiveDirection.MINIMIZE),
                    )
                ),
                context=OptimizationContext(),
            )


class TestIterativeDispatch:
    def test_iterates_to_convergence_and_extracts_the_final_result(self) -> None:
        repository, executor = _provisioned()
        result = executor.execute(
            "RUN-1",
            _problem("EVOLUTIONARY.ExecutorConverging"),
            context=OptimizationContext(),
        )
        assert result.objective_value == 100.0  # gap converged to 0
        assert result.solution == {"x": 0.0}
        assert repository.get("RUN-1").status is RunStatus.COMPLETED
        assert repository.get("RUN-1").state.attributes["gap"] == 0

    def test_iteration_bound_is_honored(self) -> None:
        repository, executor = _provisioned()
        executor.execute(
            "RUN-1",
            _problem("EVOLUTIONARY.ExecutorConverging", parameters={"max_iterations": 1}),
            context=OptimizationContext(),
        )
        assert repository.get("RUN-1").state.attributes["gap"] == 4  # one halving of 8

    def test_zero_iterations_is_a_warning_not_a_raise(self) -> None:
        _, executor = _provisioned()
        result = executor.execute(
            "RUN-1",
            _problem("EVOLUTIONARY.ExecutorConverging", parameters={"max_iterations": 0}),
            context=OptimizationContext(),
        )
        assert result.warnings == ("max_iterations produced zero iterations; state unchanged",)


class TestRepositoryConflictTranslation:
    class _VanishingRepository(InMemoryRepository[OptimizationRun, str]):
        def remove(self, entity_id: str) -> None:
            raise NotFoundError(f"{entity_id!r} vanished mid-swap")

    def test_serialization_violation_becomes_execution_error(self) -> None:
        repository = self._VanishingRepository()
        InMemoryRepository.add(
            repository,
            OptimizationRun(
                id="RUN-1",
                problem_code="TEST.ExecutorProblem",
                state=OptimizationState(attributes={"provisioned": True}),
            ),
        )
        executor = OptimizationExecutor(repository=repository)
        with pytest.raises(OptimizationExecutionError, match="write serialization"):
            executor.execute("RUN-1", _problem(), context=OptimizationContext())


class TestCandidateScenarioSearch:
    def test_search_composes_simulation_experiment_runner(self) -> None:
        """Design spec §17: a candidate-scenario search is built on
        ``simulation.ExperimentRunner.run_trials`` -- this package
        never constructs a ``simulation.SimulationRun`` directly."""
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

        @sim_register
        class _CandidateModel(MonteCarloModel):
            meta = SimulationMetadata(
                code="MONTECARLO.OptimizationCandidateSearch",
                category=SimulationCategory.MONTE_CARLO,
                description="Scores a candidate scenario per trial.",
            )

            def _trial(
                self, scenario: Scenario, *, context: SimulationContext, random_seed: int
            ) -> SimulationResult:
                trucks = int(scenario.parameters["trucks"])
                score = trucks * 100.0 * random.Random(random_seed).uniform(0.95, 1.05)
                return SimulationResult(
                    final_state=SimulationState(
                        attributes={"score": score},
                        simulated_time=datetime(2026, 7, 8, tzinfo=timezone.utc),
                    )
                )

        sim_repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
        runner = ExperimentRunner(
            executor=SimulationExecutor(
                repository=sim_repository,
                clock=SimulationClock(mode=TimeProgressionMode.TRIAL_BASED),
            ),
            repository=sim_repository,
        )
        candidates = [24, 27]
        experiments: list[Experiment] = []
        for trucks in candidates:
            scenario = Scenario(
                code=f"CANDIDATE.Trucks{trucks}",
                model_code="MONTECARLO.OptimizationCandidateSearch",
                parameters={"trucks": trucks},
                time_horizon=timedelta(hours=12),
            )
            experiments.append(
                runner.run_trials(
                    scenario,
                    trials=5,
                    context=SimulationContext(event_store=_InMemoryEventStore()),
                )
            )
        assert all(isinstance(experiment, Experiment) for experiment in experiments)
        assert all(len(experiment.run_ids) == 5 for experiment in experiments)
