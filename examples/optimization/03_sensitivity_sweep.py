"""``SensitivityAnalyzer.sweep()`` over a single constraint bound
(design spec §20): one re-solve per swept value, ordered to match,
with distributional treatment of the outcomes delegated to
``analytics`` (``distribution``/``confidence_interval``). The base,
governed problem is never edited in place -- each variant is a
transient copy.

The concrete ``MixedIntegerProgrammingModel`` below is example-local.

Run: python examples/optimization/03_sensitivity_sweep.py
"""

from __future__ import annotations

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
    SensitivityAnalyzer,
    VariableDomain,
    register,
)


@register
class ThroughputFromBudgetModel(MixedIntegerProgrammingModel):
    """Throughput scales linearly with the allotted truck budget up to
    a crusher cap that flattens the curve -- example-local, so the
    sweep produces a genuinely non-linear response worth summarizing."""

    meta = OptimizationMetadata(
        code="MIP.ThroughputFromBudget",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="Throughput from truck budget, capped at crusher capacity.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        budget = int(problem.constraints[0].bound)
        rate = float(problem.parameters["t_per_truck"])
        crusher_cap = float(problem.parameters["crusher_cap_tph"])
        tph = min(budget * rate, crusher_cap)
        return OptimizationResult(objective_value=tph, solution={"trucks": float(budget)})


def main() -> None:
    print("--- 1. A base problem and the constraint bound to sweep ---")
    base = OptimizationProblem(
        code="PLANT.CrusherFeedStudy",
        model_code="MIP.ThroughputFromBudget",
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
        parameters={"t_per_truck": 175.0, "crusher_cap_tph": 5000.0},
    )
    values = [18.0, 22.0, 26.0, 30.0, 34.0]
    print(f"base={base.code!r}, sweeping 'fleet_budget' over {values}")

    print()
    print("--- 2. One re-solve per value, ordered to match ---")
    repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    executor = OptimizationExecutor(repository=repository)
    analyzer = SensitivityAnalyzer(executor=executor, repository=repository)
    results = analyzer.sweep(
        base, target="fleet_budget", values=values, context=OptimizationContext()
    )
    outcomes: list[float] = []
    for value, result in zip(values, results, strict=True):
        assert result.objective_value is not None
        outcomes.append(result.objective_value)
        print(f"budget={value:>5.0f} -> throughput={result.objective_value:7.1f} t/h")
    print("(the crusher cap flattens the curve past ~28 trucks)")

    print()
    print("--- 3. Distributional treatment is analytics' job, not optimization's ---")
    shape, interval = analyzer.summarize(outcomes, confidence=0.95)
    print(f"skewness={shape.skewness:+.3f} kurtosis={shape.kurtosis:.3f}")
    print(
        f"{interval.confidence:.0%} CI around the sweep mean:"
        f" [{interval.lower:.1f}, {interval.upper:.1f}] t/h ({interval.method})"
    )

    print()
    print("--- 4. The base problem is untouched -- variants were transient copies ---")
    print(f"base 'fleet_budget' bound still: {base.constraints[0].bound}")


if __name__ == "__main__":
    main()
