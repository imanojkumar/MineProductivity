"""Tests for mineproductivity.optimization.discovery."""

from __future__ import annotations

import uuid

from mineproductivity.core import InMemoryRepository
from mineproductivity.optimization.discovery import by_category, by_scope
from mineproductivity.optimization.metadata import OptimizationCategory
from mineproductivity.optimization.problem import (
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationProblem,
    VariableDomain,
    publish_problem,
)
from mineproductivity.optimization.run import RunStatus, OptimizationRun
from mineproductivity.optimization.state import OptimizationState
from mineproductivity.optimization._registry import register
from mineproductivity.optimization.abstractions import OptimizationContext
from mineproductivity.optimization.metadata import OptimizationMetadata
from mineproductivity.optimization.mixed_integer_programming import (
    MixedIntegerProgrammingModel,
)
from mineproductivity.optimization.result import OptimizationResult


@register
class _DiscoveryMipModel(MixedIntegerProgrammingModel):
    meta = OptimizationMetadata(
        code="MIP.DiscoveryFixture",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="A MIP model for discovery tests.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        return OptimizationResult()


def _published_problem_code() -> str:
    code = f"TEST.DiscoveryProblem.{uuid.uuid4().hex}"
    publish_problem(
        OptimizationProblem(
            code=code,
            model_code="MIP.DiscoveryFixture",
            objectives=(Objective(name="tonnes", direction=ObjectiveDirection.MAXIMIZE),),
            variables=(DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),),
        )
    )
    return code


def _run(run_id: str, problem_code: str, **attributes: object) -> OptimizationRun:
    return OptimizationRun(
        id=run_id,
        problem_code=problem_code,
        state=OptimizationState(attributes=attributes or {"provisioned": True}),
    )


class TestByCategory:
    def test_matches_through_published_problem_and_registry(self) -> None:
        code = _published_problem_code()
        repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", code))
        matched = repository.list(by_category(OptimizationCategory.MIXED_INTEGER_PROGRAMMING))
        assert [run.id for run in matched] == ["RUN-1"]
        assert list(repository.list(by_category(OptimizationCategory.NETWORK_OPTIMIZATION))) == []

    def test_unpublished_problem_never_matches_and_never_raises(self) -> None:
        repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.NeverPublished"))
        assert (
            list(repository.list(by_category(OptimizationCategory.MIXED_INTEGER_PROGRAMMING))) == []
        )


class TestByScope:
    def test_matches_on_problem_code_status_and_state_attributes(self) -> None:
        repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.ScopeA", pit="north"))
        repository.add(
            _run("RUN-2", "TEST.ScopeB").with_state(
                OptimizationState(attributes={"provisioned": True}),
                status=RunStatus.COMPLETED,
            )
        )
        assert [run.id for run in repository.list(by_scope({"problem_code": "TEST.ScopeA"}))] == [
            "RUN-1"
        ]
        assert [run.id for run in repository.list(by_scope({"status": "completed"}))] == ["RUN-2"]
        assert [run.id for run in repository.list(by_scope({"pit": "north"}))] == ["RUN-1"]
        assert list(repository.list(by_scope({"pit": "north", "status": "completed"}))) == []

    def test_requested_scope_is_copied_not_aliased(self) -> None:
        wanted = {"pit": "north"}
        specification = by_scope(wanted)
        wanted["pit"] = "south"
        repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
        repository.add(_run("RUN-1", "TEST.ScopeA", pit="north"))
        assert [run.id for run in repository.list(specification)] == ["RUN-1"]
