"""``mineproductivity.optimization`` -- the platform's prescriptive
search layer, built directly on top of ``simulation``.

Answers: *given a governed problem statement -- objectives,
constraints, decision variables -- what is the best feasible plan?*
The package is an orchestration layer over six pluggable,
interface-only solving paradigms (linear programming, mixed-integer
programming, constraint programming, multi-objective, evolutionary/
metaheuristic, network optimization, design spec §11-§16); it never
imports a solver library (third-party solver libraries -- §17's adapter
pattern), never recomputes a KPI/statistic/decision/twin-state/
simulation fact (§3.2), and delegates every statistical judgment on
its outputs to ``analytics`` (§19-§20).

The complete design spec §6 module list (twenty modules) is
implemented: ``OptimizationModel``/``OptimizationContext`` (§8);
``OptimizationMetadata``/``OptimizationCategory`` (§29); the full
problem-definition family -- ``Objective``/``ObjectiveDirection``,
``Constraint``/``ConstraintOperator``, ``DecisionVariable``/
``VariableDomain``, ``OptimizationProblem``/``ProblemStatus`` as a
versioned, governed artifact (§9); ``OptimizationRun``/``RunStatus``/
``OptimizationExecutor`` (§10); ``OptimizationState`` (§10); the six
interface-only category ABCs with zero concrete subclasses by design
(§11-§16, ADR-0010); ``PlanComparator``/``SensitivityAnalyzer``
(§19-§20); ``by_category``/``by_scope`` (§22);
``OptimizationRunRepository`` as a literal ``type`` alias over
``core.BaseRepository[OptimizationRun, str]`` (§24); the
``OptimizationResult``/``ParetoResult`` family (§18);
``REGISTRY``/``register`` (§21); and the full exception hierarchy.
No caching module exists, deliberately (§26's documented non-need).

``optimization`` depends on ``core`` through ``simulation`` -- and
MUST NEVER import ``agents`` or ``visualization``.
"""

from __future__ import annotations

from mineproductivity.optimization._registry import REGISTRY, register
from mineproductivity.optimization.abstractions import OptimizationContext, OptimizationModel
from mineproductivity.optimization.comparison import PlanComparator
from mineproductivity.optimization.constraint_programming import ConstraintProgrammingModel
from mineproductivity.optimization.discovery import by_category, by_scope
from mineproductivity.optimization.evolutionary import EvolutionaryMetaheuristicModel
from mineproductivity.optimization.exceptions import (
    OptimizationExecutionError,
    OptimizationRunNotFoundError,
    OptimizationValidationError,
    OptimizationVersionConflictError,
    ProblemConflictError,
)
from mineproductivity.optimization.executor import OptimizationExecutor
from mineproductivity.optimization.linear_programming import LinearProgrammingModel
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata
from mineproductivity.optimization.mixed_integer_programming import (
    MixedIntegerProgrammingModel,
)
from mineproductivity.optimization.multi_objective import MultiObjectiveModel
from mineproductivity.optimization.network_optimization import NetworkOptimizationModel
from mineproductivity.optimization.persistence import OptimizationRunRepository
from mineproductivity.optimization.problem import (
    Constraint,
    ConstraintOperator,
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationProblem,
    ProblemStatus,
    VariableDomain,
)
from mineproductivity.optimization.result import OptimizationResult, ParetoResult
from mineproductivity.optimization.run import OptimizationRun, RunStatus
from mineproductivity.optimization.sensitivity import SensitivityAnalyzer
from mineproductivity.optimization.state import OptimizationState

__all__ = [
    "Constraint",
    "ConstraintOperator",
    "ConstraintProgrammingModel",
    "DecisionVariable",
    "EvolutionaryMetaheuristicModel",
    "LinearProgrammingModel",
    "MixedIntegerProgrammingModel",
    "MultiObjectiveModel",
    "NetworkOptimizationModel",
    "Objective",
    "ObjectiveDirection",
    "OptimizationCategory",
    "OptimizationContext",
    "OptimizationExecutionError",
    "OptimizationExecutor",
    "OptimizationMetadata",
    "OptimizationModel",
    "OptimizationProblem",
    "OptimizationResult",
    "OptimizationRun",
    "OptimizationRunNotFoundError",
    "OptimizationRunRepository",
    "OptimizationState",
    "OptimizationValidationError",
    "OptimizationVersionConflictError",
    "ParetoResult",
    "PlanComparator",
    "ProblemConflictError",
    "ProblemStatus",
    "REGISTRY",
    "RunStatus",
    "SensitivityAnalyzer",
    "VariableDomain",
    "by_category",
    "by_scope",
    "register",
]
