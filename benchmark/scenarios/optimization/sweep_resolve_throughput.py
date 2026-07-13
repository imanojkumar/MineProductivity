"""Benchmark scenario: post-optimality sweep re-solve throughput,
sequential vs. parallel, at representative sweep-value counts
(Optimization implementation checklist, Benchmarks).

Independent ``OptimizationRun``s (distinct ids) carry no shared mutable
state and execute with no contention (design spec §32, §33), so a
sweep's re-solves parallelize across a thread pool. This scenario
quantifies that: the same N re-solves, run sequentially through
``SensitivityAnalyzer.sweep()`` and concurrently through a
``ThreadPoolExecutor``. The example-local model is a trivial, fast MIP
so the measurement isolates dispatch/persistence overhead, not solver
arithmetic.

Standalone by design. Results are recorded in
``benchmark/reports/optimization/``.

Run: python benchmark/scenarios/optimization/sweep_resolve_throughput.py
"""

from __future__ import annotations

import platform
import time
from concurrent.futures import ThreadPoolExecutor

from mineproductivity.core import InMemoryRepository
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
    SensitivityAnalyzer,
    VariableDomain,
    register,
)

SWEEP_COUNTS = (50, 200, 1_000)
WORKERS = 8


@register
class _BenchmarkResolveModel(MixedIntegerProgrammingModel):
    meta = OptimizationMetadata(
        code="MIP.BenchmarkResolve",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="Trivial fast MIP isolating executor dispatch/persistence cost.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        bound = problem.constraints[0].bound
        return OptimizationResult(objective_value=bound * 175.0, solution={"trucks": bound})


def _base_problem() -> OptimizationProblem:
    return OptimizationProblem(
        code="PLANT.BenchmarkSweep",
        model_code="MIP.BenchmarkResolve",
        objectives=(Objective(name="throughput", direction=ObjectiveDirection.MAXIMIZE),),
        constraints=(
            Constraint(
                name="fleet_budget",
                expression="trucks",
                operator=ConstraintOperator.LESS_EQUAL,
                bound=20.0,
            ),
        ),
        variables=(DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),),
    )


def _sequential(count: int, context: OptimizationContext) -> float:
    repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    executor = OptimizationExecutor(repository=repository)
    analyzer = SensitivityAnalyzer(executor=executor, repository=repository)
    values = [float(18 + index % 20) for index in range(count)]
    start = time.perf_counter()
    analyzer.sweep(_base_problem(), target="fleet_budget", values=values, context=context)
    return time.perf_counter() - start


def _parallel(count: int, context: OptimizationContext) -> float:
    repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    executor = OptimizationExecutor(repository=repository)
    base = _base_problem()
    for index in range(count):
        repository.add(
            OptimizationRun(
                id=f"RUN-{index:06d}",
                problem_code=base.code,
                state=OptimizationState(attributes={"provisioned": True}),
            )
        )

    def _resolve(index: int) -> OptimizationResult:
        return executor.execute(f"RUN-{index:06d}", base, context=context)

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(_resolve, range(count)))
    return time.perf_counter() - start


def main() -> None:
    print("Optimization sweep re-solve throughput (sequential vs. parallel)")
    print(f"python={platform.python_version()} machine={platform.machine()} workers={WORKERS}")
    print()
    print(f"{'re-solves':>10} {'seq_ms':>10} {'seq_per_s':>12} {'par_ms':>10} {'par_per_s':>12}")

    context = OptimizationContext()
    for count in SWEEP_COUNTS:
        seq_seconds = _sequential(count, context)
        par_seconds = _parallel(count, context)
        print(
            f"{count:>10} {seq_seconds * 1e3:>10.2f} {count / seq_seconds:>12.0f}"
            f" {par_seconds * 1e3:>10.2f} {count / par_seconds:>12.0f}"
        )


if __name__ == "__main__":
    main()
