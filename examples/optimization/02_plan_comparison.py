"""``PlanComparator`` over two candidate haulage plans, each solved
across a range of ore-grade scenarios (design spec §19). Every
statistical treatment is delegated to ``analytics`` -- this package
computes no mean or percentile of its own; the "which plan is better"
judgment stays with the caller (a decision-layer question).

The concrete ``LinearProgrammingModel`` below is example-local.

Run: python examples/optimization/02_plan_comparison.py
"""

from __future__ import annotations

from mineproductivity.core import InMemoryRepository
from mineproductivity.optimization import (
    DecisionVariable,
    LinearProgrammingModel,
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
    register,
)

GRADES = (0.90, 0.95, 1.00, 1.05, 1.10)


@register
class HaulThroughputModel(LinearProgrammingModel):
    """Projects shift throughput from a plan's fleet size and the
    scenario's ore grade -- example-local, deterministic, stateless."""

    meta = OptimizationMetadata(
        code="LP.HaulThroughput",
        category=OptimizationCategory.LINEAR_PROGRAMMING,
        description="Projects shift throughput from fleet size and ore grade.",
    )

    def _solve_lp(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        fleet = float(problem.parameters["fleet_size"])
        grade = float(problem.parameters["ore_grade"])
        tph = fleet * 180.0 * grade
        return OptimizationResult(objective_value=tph, solution={"tonnes_per_hour": tph})


def _solve_plan(
    executor: OptimizationExecutor,
    repository: InMemoryRepository[OptimizationRun, str],
    *,
    plan: str,
    fleet_size: int,
) -> list[OptimizationResult]:
    """Solve one plan once per ore-grade scenario, returning the
    sequence of outcomes ``PlanComparator`` will summarize."""
    results: list[OptimizationResult] = []
    for index, grade in enumerate(GRADES):
        run_id = f"RUN-{plan}-{index}"
        repository.add(
            OptimizationRun(
                id=run_id,
                problem_code=f"HAUL.{plan}",
                state=OptimizationState(attributes={"provisioned": True}),
            )
        )
        problem = OptimizationProblem(
            code=f"HAUL.{plan}",
            model_code="LP.HaulThroughput",
            objectives=(Objective(name="throughput", direction=ObjectiveDirection.MAXIMIZE),),
            variables=(DecisionVariable(name="tonnes_per_hour", domain=VariableDomain.CONTINUOUS),),
            parameters={"fleet_size": fleet_size, "ore_grade": grade},
        )
        results.append(executor.execute(run_id, problem, context=OptimizationContext()))
    return results


def main() -> None:
    print("--- 1. Two candidate plans, each solved across five ore grades ---")
    repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    executor = OptimizationExecutor(repository=repository)
    conservative = _solve_plan(executor, repository, plan="Conservative", fleet_size=24)
    aggressive = _solve_plan(executor, repository, plan="Aggressive", fleet_size=30)
    print(f"grades swept: {GRADES}")

    print()
    print("--- 2. PlanComparator delegates every statistic to analytics ---")
    summaries = PlanComparator().compare(
        {"conservative_24": conservative, "aggressive_30": aggressive}
    )
    for plan, summary in summaries.items():
        print(
            f"{plan:>15}: n={summary.n} mean={summary.mean:7.1f} t/h "
            f"p50={summary.percentiles[50]:7.1f} "
            f"range=[{summary.minimum:7.1f}, {summary.maximum:7.1f}]"
        )

    print()
    print("--- 3. The choice is the caller's; optimization only quantifies it ---")
    print("(a decision-layer model would weigh higher mean against capital cost)")


if __name__ == "__main__":
    main()
