"""Tests for mineproductivity.optimization.problem."""

from __future__ import annotations

import uuid

import pytest

from mineproductivity.core.serialization import to_dict
from mineproductivity.optimization.exceptions import (
    OptimizationValidationError,
    ProblemConflictError,
)
from mineproductivity.optimization.problem import (
    Constraint,
    ConstraintOperator,
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationProblem,
    ProblemStatus,
    VariableDomain,
    problem_history,
    publish_problem,
    published_problem,
)


def _unique_code() -> str:
    return f"TEST.Problem.{uuid.uuid4().hex}"


def _problem(**overrides: object) -> OptimizationProblem:
    fields: dict[str, object] = {
        "code": "FLEET.NightShiftAllocation",
        "model_code": "MIP.FleetAllocation",
        "objectives": (Objective(name="tonnes", direction=ObjectiveDirection.MAXIMIZE),),
        "variables": (DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),),
    }
    fields.update(overrides)
    return OptimizationProblem(**fields)  # type: ignore[arg-type]


class TestValueObjects:
    def test_objective_defaults(self) -> None:
        objective = Objective(name="tonnes", direction=ObjectiveDirection.MAXIMIZE)
        assert objective.weight == 1.0

    def test_constraint_carries_a_solver_independent_expression(self) -> None:
        constraint = Constraint(
            name="truck_budget",
            expression="trucks_route_a + trucks_route_b",
            operator=ConstraintOperator.LESS_EQUAL,
            bound=27.0,
        )
        assert constraint.operator is ConstraintOperator.LESS_EQUAL
        assert constraint.bound == 27.0

    def test_decision_variable_bounds_default_to_none(self) -> None:
        variable = DecisionVariable(name="trucks", domain=VariableDomain.BINARY)
        assert variable.lower_bound is None
        assert variable.upper_bound is None

    def test_enums_exactly_as_specified(self) -> None:
        assert {m.value for m in ObjectiveDirection} == {"minimize", "maximize"}
        assert {m.value for m in ConstraintOperator} == {"<=", ">=", "="}
        assert {m.value for m in VariableDomain} == {"continuous", "integer", "binary"}
        assert {m.value for m in ProblemStatus} == {
            "proposed",
            "active",
            "superseded",
            "retired",
        }


class TestOptimizationProblem:
    def test_minimal_valid_construction(self) -> None:
        problem = _problem()
        assert problem.version == "1.0.0"
        assert problem.status is ProblemStatus.PROPOSED
        assert problem.constraints == ()
        assert problem.initial_state is None
        assert problem.as_of is None

    def test_parameters_are_frozen(self) -> None:
        problem = _problem(parameters={"budget": 27})
        with pytest.raises(TypeError):
            problem.parameters["more"] = 1  # type: ignore[index]

    def test_validation_rejects_empty_fields(self) -> None:
        with pytest.raises(OptimizationValidationError, match="code must not be empty"):
            _problem(code=" ")
        with pytest.raises(OptimizationValidationError, match="model_code must not be empty"):
            _problem(model_code="")
        with pytest.raises(OptimizationValidationError, match="objectives must not be empty"):
            _problem(objectives=())
        with pytest.raises(OptimizationValidationError, match="variables must not be empty"):
            _problem(variables=())

    def test_serializes_generically(self) -> None:
        assert to_dict(_problem())["code"] == "FLEET.NightShiftAllocation"


class TestPublishProblem:
    def test_first_publication_and_lookup(self) -> None:
        code = _unique_code()
        problem = _problem(code=code)
        assert publish_problem(problem) is problem
        assert published_problem(code) is problem
        assert published_problem(_unique_code()) is None

    def test_changing_an_active_problem_at_the_same_version_raises(self) -> None:
        code = _unique_code()
        publish_problem(_problem(code=code, status=ProblemStatus.ACTIVE))
        changed = _problem(
            code=code,
            status=ProblemStatus.ACTIVE,
            constraints=(
                Constraint(
                    name="cap",
                    expression="trucks",
                    operator=ConstraintOperator.LESS_EQUAL,
                    bound=20.0,
                ),
            ),
        )
        with pytest.raises(ProblemConflictError, match="requires a new version"):
            publish_problem(changed)

    def test_new_version_supersedes_the_prior_active_version(self) -> None:
        code = _unique_code()
        publish_problem(_problem(code=code, version="1.0.0", status=ProblemStatus.ACTIVE))
        v2 = _problem(
            code=code,
            version="2.0.0",
            status=ProblemStatus.ACTIVE,
            objectives=(Objective(name="cost", direction=ObjectiveDirection.MINIMIZE),),
        )
        publish_problem(v2)
        assert published_problem(code) is v2
        history = problem_history(code)
        assert len(history) == 1
        assert history[0].status is ProblemStatus.SUPERSEDED

    def test_proposed_changes_and_identical_republication_are_allowed(self) -> None:
        code = _unique_code()
        publish_problem(_problem(code=code))
        changed = _problem(
            code=code,
            status=ProblemStatus.ACTIVE,
            objectives=(Objective(name="cost", direction=ObjectiveDirection.MINIMIZE),),
        )
        assert publish_problem(changed) is changed
        publish_problem(changed)  # identical republication -- not a conflict
        assert problem_history(_unique_code()) == ()
