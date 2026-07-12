"""``OptimizationExecutor``: orchestrates one ``OptimizationRun``
(design spec §10).

Reuse audit: dispatch reads the registered model's
``OptimizationCategory`` off ``OptimizationProblem.model_code`` via
``REGISTRY``, never branching on the model's concrete Python type
(§10); the ``remove``-then-``add`` repository pair is the same single,
narrow mutable operation every prior package concentrates its
mutation into, with a serialization violation surfacing as
``OptimizationExecutionError`` (§32). Registered models instantiate
via a no-arg constructor (the platform convention since
``kpis.KPIEngine``); a model's tunables arrive via
``OptimizationProblem.parameters``. A legitimately infeasible problem
flows through as ``OptimizationResult(feasible=False, ...)`` -- never
a raise (§28). Iterative categories (evolutionary/metaheuristic) loop
``_iterate`` to value-convergence or the iteration bound carried in
``problem.parameters["max_iterations"]`` (default 100, disclosed --
the spec prescribes "convergence or a termination bound" without
fixing the number).
"""

from __future__ import annotations

from mineproductivity.core import DuplicateError, NotFoundError
from mineproductivity.registry import UnregisteredLookupError

from mineproductivity.optimization._registry import REGISTRY
from mineproductivity.optimization.abstractions import OptimizationContext
from mineproductivity.optimization.constraint_programming import ConstraintProgrammingModel
from mineproductivity.optimization.evolutionary import EvolutionaryMetaheuristicModel
from mineproductivity.optimization.exceptions import (
    OptimizationExecutionError,
    OptimizationRunNotFoundError,
    OptimizationValidationError,
)
from mineproductivity.optimization.linear_programming import LinearProgrammingModel
from mineproductivity.optimization.metadata import OptimizationCategory
from mineproductivity.optimization.mixed_integer_programming import (
    MixedIntegerProgrammingModel,
)
from mineproductivity.optimization.multi_objective import MultiObjectiveModel
from mineproductivity.optimization.network_optimization import NetworkOptimizationModel
from mineproductivity.optimization.persistence import OptimizationRunRepository
from mineproductivity.optimization.problem import OptimizationProblem, VariableDomain
from mineproductivity.optimization.result import OptimizationResult
from mineproductivity.optimization.run import OptimizationRun, RunStatus

__all__ = ["OptimizationExecutor"]

_DEFAULT_MAX_ITERATIONS = 100


class OptimizationExecutor:
    """Orchestrates one ``OptimizationRun``: fetches the current
    instance, validates the problem/category pairing (§11's
    variable-domain rule, §14's objective-count rule), dispatches to
    the registered model's category-specific method -- looping
    iterative categories to convergence or the termination bound --
    and persists the resulting state (design spec §10's sequence
    diagram)."""

    def __init__(self, *, repository: OptimizationRunRepository) -> None:
        self._repository = repository

    def __repr__(self) -> str:
        return f"{type(self).__name__}(repository={self._repository!r})"

    def execute(
        self,
        run_id: str,
        problem: OptimizationProblem,
        *,
        context: OptimizationContext,
    ) -> OptimizationResult:
        """Solve ``problem`` for the run stored under ``run_id``.

        A run already ``Completed``/``Failed`` is terminal (design
        spec §10): execution is skipped and a warning-carrying result
        returned. A legitimately infeasible problem returns
        ``feasible=False`` plus a warning, never a raise (§28).

        Raises
        ------
        OptimizationRunNotFoundError
            If no run is stored under ``run_id``, or no
            ``OptimizationModel`` is registered for
            ``problem.model_code``.
        OptimizationValidationError
            If the problem/category pairing violates §11's
            variable-domain rule or §14's objective-count rule.
        OptimizationExecutionError
            If the model's category method raised for a structurally
            valid input (the run is marked ``Failed`` first, §10), or
            the repository's per-id write serialization contract was
            violated mid-swap (§32).
        """
        maybe_run = self._repository.find(run_id)
        if maybe_run.is_nothing:
            raise OptimizationRunNotFoundError(f"No optimization run is stored under id {run_id!r}")
        run = maybe_run.unwrap()

        if run.status in (RunStatus.COMPLETED, RunStatus.FAILED):
            return OptimizationResult(
                run_id=run_id,
                warnings=(
                    f"run is {run.status.value}; execution skipped "
                    f"({run.status.value} is terminal)",
                ),
            )

        try:
            model_cls = REGISTRY.get(problem.model_code)
        except UnregisteredLookupError as exc:
            raise OptimizationRunNotFoundError(
                f"No OptimizationModel is registered for code {problem.model_code!r}"
            ) from exc
        category = model_cls.meta.category
        self._validate_pairing(problem, category)

        run = run.with_state(run.state, status=RunStatus.RUNNING)
        self._replace(run_id, run)

        model = model_cls()
        try:
            if category is OptimizationCategory.EVOLUTIONARY_METAHEURISTIC:
                assert isinstance(model, EvolutionaryMetaheuristicModel)
                result = self._run_iterative(model, run_id, run, problem, context)
            elif category is OptimizationCategory.LINEAR_PROGRAMMING:
                assert isinstance(model, LinearProgrammingModel)
                result = model._solve_lp(problem, context=context)
            elif category is OptimizationCategory.MIXED_INTEGER_PROGRAMMING:
                assert isinstance(model, MixedIntegerProgrammingModel)
                result = model._solve_mip(problem, context=context)
            elif category is OptimizationCategory.CONSTRAINT_PROGRAMMING:
                assert isinstance(model, ConstraintProgrammingModel)
                result = model._solve_cp(problem, context=context)
            elif category is OptimizationCategory.MULTI_OBJECTIVE:
                assert isinstance(model, MultiObjectiveModel)
                result = model._solve_pareto(problem, context=context)
            else:
                assert isinstance(model, NetworkOptimizationModel)
                result = model._solve_network(problem, context=context)
        except Exception as exc:
            self._replace(run_id, run.with_state(run.state, status=RunStatus.FAILED))
            raise OptimizationExecutionError(
                f"OptimizationModel {problem.model_code!r} raised for a structurally "
                f"valid input on run {run_id!r}: {exc}"
            ) from exc

        final = self._repository.get(run_id)
        self._replace(run_id, final.with_state(final.state, status=RunStatus.COMPLETED))
        return result.replace(run_id=run_id)

    def _run_iterative(
        self,
        model: EvolutionaryMetaheuristicModel,
        run_id: str,
        run: OptimizationRun,
        problem: OptimizationProblem,
        context: OptimizationContext,
    ) -> OptimizationResult:
        """The §10 iterative branch: loop ``_iterate`` until the state
        is value-unchanged (convergence) or the iteration bound is
        reached, persisting each produced state via the repository
        swap. The final result reads ``objective_value``/``solution``
        from the final state's own attributes when the model recorded
        them there."""
        max_iterations = int(problem.parameters.get("max_iterations", _DEFAULT_MAX_ITERATIONS))
        current = run.state
        warnings: tuple[str, ...] = ()
        if max_iterations <= 0:
            warnings = ("max_iterations produced zero iterations; state unchanged",)
        for _ in range(max_iterations):
            next_state = model._iterate(problem, current, context=context)
            converged = next_state == current
            current = next_state
            run = run.with_state(current)
            self._replace(run_id, run)
            if converged:
                break

        attributes = current.attributes
        raw_objective = attributes.get("objective_value")
        raw_solution = attributes.get("solution")
        solution: dict[str, float] = {}
        if isinstance(raw_solution, dict):
            solution = {
                str(name): float(value)
                for name, value in raw_solution.items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            }
        return OptimizationResult(
            run_id=run_id,
            warnings=warnings,
            objective_value=(
                float(raw_objective)
                if isinstance(raw_objective, (int, float)) and not isinstance(raw_objective, bool)
                else None
            ),
            solution=solution,
        )

    @staticmethod
    def _validate_pairing(problem: OptimizationProblem, category: OptimizationCategory) -> None:
        """§27's cross-field rules: LP admits continuous variables only
        (§11); the multi-objective category requires two or more
        objectives, and every other category exactly one (§14)."""
        if category is OptimizationCategory.LINEAR_PROGRAMMING and any(
            variable.domain is not VariableDomain.CONTINUOUS for variable in problem.variables
        ):
            raise OptimizationValidationError(
                f"Problem {problem.code!r} pairs non-continuous decision variables "
                f"with an LP-category model (design spec §11)"
            )
        if category is OptimizationCategory.MULTI_OBJECTIVE and len(problem.objectives) < 2:
            raise OptimizationValidationError(
                f"Problem {problem.code!r} pairs a single objective with a "
                f"multi-objective-category model (design spec §14)"
            )
        if category is not OptimizationCategory.MULTI_OBJECTIVE and len(problem.objectives) != 1:
            raise OptimizationValidationError(
                f"Problem {problem.code!r} declares {len(problem.objectives)} objectives "
                f"for a single-objective-category model (design spec §14)"
            )

    def _replace(self, run_id: str, replacement: OptimizationRun) -> None:
        try:
            self._repository.remove(run_id)
            self._repository.add(replacement)
        except (NotFoundError, DuplicateError) as exc:
            raise OptimizationExecutionError(
                f"Concurrent execute() calls for run {run_id!r} raced past the "
                f"repository's per-id write serialization contract (design spec §32)"
            ) from exc
