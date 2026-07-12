"""Problem definition (design spec §9): ``OptimizationProblem`` as a
versioned, governed artifact plus its constituent value objects.

Reuse audit: ``core.BaseValueObject`` and the mapping-freezing
convention reused verbatim; ``digital_twin.TwinSnapshot`` reused
directly as ``initial_state`` and ``events.AsOf`` as the point-in-time
reference, exactly as ``simulation.Scenario`` already does (spec 09
§9). ``Constraint.expression`` is a solver-independent string this
package never parses or evaluates -- interpretation belongs to a
concrete adapter's own translation into its solver library (§17). No
dependency-graph mechanism exists for constraints/variables: every
constraint is imposed simultaneously on one feasible region (§9's
documented non-need). The publish/supersede governance mirrors
``simulation.publish_scenario`` exactly; ``publish_problem`` is
deliberately not re-exported from the package's top-level ``__all__``
(design spec §7 names ``OptimizationProblem``/``ProblemStatus`` only).
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject
from mineproductivity.digital_twin import TwinSnapshot
from mineproductivity.events import AsOf

from mineproductivity.optimization.exceptions import (
    OptimizationValidationError,
    ProblemConflictError,
)

__all__ = [
    "Constraint",
    "ConstraintOperator",
    "DecisionVariable",
    "Objective",
    "ObjectiveDirection",
    "OptimizationProblem",
    "ProblemStatus",
    "VariableDomain",
]

_problems: dict[str, OptimizationProblem] = {}
_problem_history: dict[str, list[OptimizationProblem]] = {}
_lock = threading.Lock()


class ObjectiveDirection(Enum):
    """Whether an ``Objective`` is minimized or maximized."""

    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


@dataclasses.dataclass(frozen=True, slots=True)
class Objective(BaseValueObject):
    """One term of an ``OptimizationProblem``'s objective function
    (design spec §9). A single-objective problem declares exactly one;
    a multi-objective problem (§14) declares two or more, each with an
    optional ``weight`` a scalarizing implementation may use -- and a
    Pareto-search implementation is free to ignore.

    Examples
    --------
    >>> Objective(name="tonnes_moved", direction=ObjectiveDirection.MAXIMIZE).weight
    1.0
    """

    name: str
    direction: ObjectiveDirection
    weight: float = dataclasses.field(default=1.0, kw_only=True)


class ConstraintOperator(Enum):
    """The relational operator a ``Constraint`` enforces between its
    expression and its bound."""

    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    EQUAL = "="


@dataclasses.dataclass(frozen=True, slots=True)
class Constraint(BaseValueObject):
    """One constraint the feasible region must satisfy (design spec
    §9). ``expression`` is a solver-independent string this package
    never parses or evaluates -- a concrete ``OptimizationModel``
    adapter's own translation is where it is interpreted (§17).

    Examples
    --------
    >>> Constraint(
    ...     name="truck_budget", expression="trucks_route_a + trucks_route_b",
    ...     operator=ConstraintOperator.LESS_EQUAL, bound=27.0,
    ... ).bound
    27.0
    """

    name: str
    expression: str
    operator: ConstraintOperator
    bound: float


class VariableDomain(Enum):
    """The domain a ``DecisionVariable``'s optimal value is drawn
    from."""

    CONTINUOUS = "continuous"
    INTEGER = "integer"
    BINARY = "binary"


@dataclasses.dataclass(frozen=True, slots=True)
class DecisionVariable(BaseValueObject):
    """One variable an ``OptimizationModel`` solves for (design spec
    §9). ``lower_bound``/``upper_bound`` default to ``None``
    (unbounded), matching core's None-over-sentinel convention.

    Examples
    --------
    >>> DecisionVariable(name="trucks_route_a", domain=VariableDomain.INTEGER).lower_bound
    """

    name: str
    domain: VariableDomain
    lower_bound: float | None = dataclasses.field(default=None, kw_only=True)
    upper_bound: float | None = dataclasses.field(default=None, kw_only=True)


class ProblemStatus(Enum):
    """The ``OptimizationProblem`` lifecycle -- mirrors
    ``simulation.ScenarioStatus`` (spec 09 §9) exactly."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


@dataclasses.dataclass(frozen=True, slots=True)
class OptimizationProblem(BaseValueObject):
    """A named, versioned optimization problem statement -- the
    governed artifact this package owns, analogous to
    ``simulation.Scenario`` (spec 09 §9) one layer down. An ``Active``
    problem is never edited in place: a changed problem is a new
    version, the prior one ``Superseded`` (§9, §25).

    Examples
    --------
    >>> problem = OptimizationProblem(
    ...     code="FLEET.NightShiftAllocation",
    ...     model_code="MIP.FleetAllocation",
    ...     objectives=(Objective(name="tonnes", direction=ObjectiveDirection.MAXIMIZE),),
    ...     variables=(DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),),
    ... )
    >>> problem.status
    <ProblemStatus.PROPOSED: 'proposed'>
    """

    code: str
    version: str = dataclasses.field(default="1.0.0", kw_only=True)
    status: ProblemStatus = dataclasses.field(
        default_factory=lambda: ProblemStatus.PROPOSED, kw_only=True
    )
    model_code: str = dataclasses.field(kw_only=True)
    objectives: tuple[Objective, ...] = dataclasses.field(kw_only=True)
    constraints: tuple[Constraint, ...] = dataclasses.field(default=(), kw_only=True)
    variables: tuple[DecisionVariable, ...] = dataclasses.field(kw_only=True)
    parameters: Mapping[str, Any] = dataclasses.field(default_factory=dict, kw_only=True)
    initial_state: TwinSnapshot | None = dataclasses.field(default=None, kw_only=True)
    as_of: AsOf | None = dataclasses.field(default=None, kw_only=True)

    def _normalize(self) -> None:
        super(OptimizationProblem, self)._normalize()
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))

    def validate(self) -> None:
        if not self.code.strip():
            raise OptimizationValidationError("OptimizationProblem.code must not be empty")
        if not self.model_code.strip():
            raise OptimizationValidationError("OptimizationProblem.model_code must not be empty")
        if not self.objectives:
            raise OptimizationValidationError("OptimizationProblem.objectives must not be empty")
        if not self.variables:
            raise OptimizationValidationError("OptimizationProblem.variables must not be empty")


def publish_problem(problem: OptimizationProblem) -> OptimizationProblem:
    """Publish ``problem`` into the process-wide problem store, keyed
    by ``problem.code`` (design spec §9, §25).

    Raises
    ------
    ProblemConflictError
        If an ``Active`` problem is already published under
        ``problem.code`` and ``problem`` changes its objectives/
        constraints/variables without a version bump -- raised at
        publication time, never deferred.
    """
    with _lock:
        existing = _problems.get(problem.code)
        if existing is not None and existing.status is ProblemStatus.ACTIVE:
            changed = (
                existing.objectives != problem.objectives
                or existing.constraints != problem.constraints
                or existing.variables != problem.variables
            )
            if changed and problem.version == existing.version:
                raise ProblemConflictError(
                    f"OptimizationProblem {problem.code!r} is Active at version "
                    f"{existing.version!r}; changing its objectives/constraints/variables "
                    f"requires a new version, not re-publication"
                )
            if changed and problem.status is ProblemStatus.ACTIVE:
                superseded = existing.replace(status=ProblemStatus.SUPERSEDED)
                _problem_history.setdefault(problem.code, []).append(superseded)
        _problems[problem.code] = problem
        return problem


def published_problem(code: str) -> OptimizationProblem | None:
    """Non-raising lookup of the currently-published problem for
    ``code``, or ``None``."""
    with _lock:
        return _problems.get(code)


def problem_history(code: str) -> tuple[OptimizationProblem, ...]:
    """Every prior version of ``code`` transitioned to ``Superseded``,
    oldest first."""
    with _lock:
        return tuple(_problem_history.get(code, ()))
