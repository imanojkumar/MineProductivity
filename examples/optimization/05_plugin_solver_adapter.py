"""A third-party-style solver adapter registered via entry points,
mirroring ``examples/registry/01_register_and_discover.py``'s pattern --
the exact wiring design spec 10 §31 prescribes:

    [project.entry-points."mineproductivity.optimization"]
    sitepack = "mineproductivity_sitepack.optimization"

The plugin subclasses one interface-only category ABC and registers a
concrete solver adapter -- the only place a real solver library (OR-Tools,
Pyomo, PuLP, SciPy) would ever be imported. ``optimization`` itself never
imports one (§17).

Run: python examples/optimization/05_plugin_solver_adapter.py
"""

from __future__ import annotations

import importlib.metadata
import sys
import tempfile
from pathlib import Path

from mineproductivity.core import InMemoryRepository
from mineproductivity.optimization import (
    REGISTRY,
    Constraint,
    ConstraintOperator,
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationContext,
    OptimizationExecutor,
    OptimizationMetadata,
    OptimizationProblem,
    OptimizationRun,
    OptimizationState,
    RunStatus,
    VariableDomain,
)

_PLUGIN_SOURCE = '''\
"""A site pack's own MIP solver adapter -- importing this module
registers it, exactly as a pip-installed plugin's entry-point scan
would. A real adapter would translate the problem into its solver
library here; this one solves the trivial single-bound case directly."""

from mineproductivity.optimization import (
    MixedIntegerProgrammingModel,
    OptimizationCategory,
    OptimizationContext,
    OptimizationMetadata,
    OptimizationProblem,
    OptimizationResult,
    register,
)


@register
class SitePackBudgetSolver(MixedIntegerProgrammingModel):
    """A site pack's budget-maximizing MIP adapter."""

    meta = OptimizationMetadata(
        code="MIP.SitePackBudgetSolver",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="A site pack's budget-maximizing MIP solver adapter.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        bound = problem.constraints[0].bound if problem.constraints else 0.0
        return OptimizationResult(
            objective_value=bound, solution={problem.variables[0].name: bound}
        )
'''


def main() -> None:
    print("--- 1. optimization ships zero built-in solvers (interface-only) ---")
    before = sorted(code for code in REGISTRY if "SitePack" in code)
    print(f"site-pack solvers before discovery: {before}")

    print()
    print("--- 2. A site pack declares its adapter via a pyproject.toml entry-point ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        plugin_path = Path(tmp_dir) / "_example_sitepack_optimization.py"
        plugin_path.write_text(_PLUGIN_SOURCE, encoding="utf-8")
        sys.path.insert(0, tmp_dir)
        try:
            real_entry_points = importlib.metadata.entry_points

            def _fake_entry_points(*, group: str):  # type: ignore[no-untyped-def]
                if group == "mineproductivity.optimization":
                    return (
                        importlib.metadata.EntryPoint(
                            name="sitepack",
                            value="_example_sitepack_optimization",
                            group=group,
                        ),
                    )
                return real_entry_points(group=group)

            importlib.metadata.entry_points = _fake_entry_points  # type: ignore[assignment]
            try:
                from mineproductivity.registry import EntryPointDiscovery, EntryPointSpec

                discovery = EntryPointDiscovery()
                spec = EntryPointSpec(
                    group="mineproductivity.optimization", target_registry="optimization"
                )
                discover_result = discovery.discover(spec)
            finally:
                importlib.metadata.entry_points = real_entry_points
        finally:
            sys.path.remove(tmp_dir)
            sys.modules.pop("_example_sitepack_optimization", None)

    print(
        f"discover() -> is_ok: {discover_result.is_ok},"
        f" loaded entry-points: {discover_result.value}"
    )
    metadata = REGISTRY.metadata_for("MIP.SitePackBudgetSolver").unwrap()
    assert isinstance(metadata, OptimizationMetadata)
    print(f"registered: {metadata.code} ({metadata.category.value})")

    print()
    print("--- 3. The discovered adapter dispatches like any built-in would ---")
    repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    repository.add(
        OptimizationRun(
            id="RUN-SITEPACK-1",
            problem_code="FLEET.SitePackBudget",
            state=OptimizationState(attributes={"provisioned": True}),
        )
    )
    executor = OptimizationExecutor(repository=repository)
    problem = OptimizationProblem(
        code="FLEET.SitePackBudget",
        model_code="MIP.SitePackBudgetSolver",
        objectives=(Objective(name="trucks", direction=ObjectiveDirection.MAXIMIZE),),
        constraints=(
            Constraint(
                name="fleet_budget",
                expression="trucks",
                operator=ConstraintOperator.LESS_EQUAL,
                bound=27.0,
            ),
        ),
        variables=(DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),),
    )
    result = executor.execute("RUN-SITEPACK-1", problem, context=OptimizationContext())
    print(f"objective={result.objective_value:.0f}  solution={dict(result.solution)}")
    print(f"run status COMPLETED: {repository.get('RUN-SITEPACK-1').status is RunStatus.COMPLETED}")


if __name__ == "__main__":
    main()
