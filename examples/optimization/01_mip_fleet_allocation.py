"""A mixed-integer fleet/shift allocation problem seeded from a real
``digital_twin.TwinSnapshot`` (design spec §12, §17-adjacent), solved
end-to-end through ``OptimizationExecutor``.

The concrete ``MixedIntegerProgrammingModel`` below is example-local:
the package itself ships zero concrete solver models by design
(interface-only paradigms, spec 10 §11-§16, ADR-0010). A production
deployment would register a real solver adapter (OR-Tools, Pyomo, ...)
the identical way -- ``optimization`` never imports a solver library
(§17).

Run: python examples/optimization/01_mip_fleet_allocation.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.core import InMemoryRepository
from mineproductivity.digital_twin import TwinSnapshot, TwinState, TwinStatus
from mineproductivity.events import AsOf
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
    RunStatus,
    VariableDomain,
    register,
)

NOW = datetime(2026, 7, 8, 6, 0, tzinfo=timezone.utc)


@register
class FleetAllocationModel(MixedIntegerProgrammingModel):
    """Greedy integer allocation of a fixed truck budget across two
    shifts, each with its own per-truck productivity and headcount cap
    -- example-local, stateless, with a hand-computable optimum
    (fill the higher-rate shift to its cap, then spill the remainder)."""

    meta = OptimizationMetadata(
        code="MIP.FleetShiftAllocation",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description=(
            "Greedy integer allocation of a truck budget across two shifts "
            "with per-shift productivity and headcount caps."
        ),
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        # The fleet budget is read from the twin snapshot the problem was
        # seeded with -- optimization consumes twin state, never re-derives it.
        assert problem.initial_state is not None
        budget = int(problem.initial_state.state.attributes["available_trucks"])

        rates = {v.name: float(problem.parameters[f"{v.name}_rate"]) for v in problem.variables}
        caps = {
            c.name.removesuffix("_cap"): int(c.bound)
            for c in problem.constraints
            if c.name.endswith("_cap")
        }

        remaining = budget
        solution: dict[str, float] = {}
        tonnes = 0.0
        for name in sorted(rates, key=lambda n: rates[n], reverse=True):
            take = min(caps.get(name, remaining), remaining)
            solution[name] = float(take)
            tonnes += take * rates[name]
            remaining -= take

        warnings = () if remaining == 0 else (f"{remaining} trucks left unallocated by the caps",)
        return OptimizationResult(objective_value=tonnes, solution=solution, warnings=warnings)


def main() -> None:
    print("--- 1. Start from a real twin snapshot, not a hand-authored guess ---")
    snapshot = TwinSnapshot(
        twin_id="FLEET-NORTH",
        state=TwinState(attributes={"available_trucks": 30}, captured_at=NOW),
        status=TwinStatus.SYNCHRONIZED,
        as_of=AsOf(utc=NOW),
    )
    print(f"snapshot of {snapshot.twin_id}: {dict(snapshot.state.attributes)}")

    print()
    print("--- 2. A governed problem: objective, caps, decision variables ---")
    problem = OptimizationProblem(
        code="FLEET.NightShiftAllocation",
        model_code="MIP.FleetShiftAllocation",
        objectives=(Objective(name="tonnes_moved", direction=ObjectiveDirection.MAXIMIZE),),
        constraints=(
            Constraint(
                name="day_trucks_cap",
                expression="day_trucks",
                operator=ConstraintOperator.LESS_EQUAL,
                bound=18.0,
            ),
            Constraint(
                name="night_trucks_cap",
                expression="night_trucks",
                operator=ConstraintOperator.LESS_EQUAL,
                bound=18.0,
            ),
        ),
        variables=(
            DecisionVariable(name="day_trucks", domain=VariableDomain.INTEGER),
            DecisionVariable(name="night_trucks", domain=VariableDomain.INTEGER),
        ),
        parameters={"day_trucks_rate": 520.0, "night_trucks_rate": 460.0},
        initial_state=snapshot,
    )
    print(f"problem={problem.code!r} model={problem.model_code!r} budget from snapshot")

    print()
    print("--- 3. Provision a run and dispatch through the executor ---")
    repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    repository.add(
        OptimizationRun(
            id="RUN-FLEET-1",
            problem_code=problem.code,
            state=OptimizationState(attributes={"provisioned": True}),
        )
    )
    executor = OptimizationExecutor(repository=repository)
    result = executor.execute("RUN-FLEET-1", problem, context=OptimizationContext())

    print()
    print("--- 4. The solved plan ---")
    print(f"feasible={result.feasible}  objective={result.objective_value:.0f} t/shift")
    for name, value in result.solution.items():
        print(f"  {name}: {value:.0f} trucks")
    print(f"run status COMPLETED: {repository.get('RUN-FLEET-1').status is RunStatus.COMPLETED}")
    print("(optimum: 18 day trucks @520 + 12 night @460 = 14,880 t/shift)")


if __name__ == "__main__":
    main()
