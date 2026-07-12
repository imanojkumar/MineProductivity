"""``SensitivityAnalyzer``: post-optimality (sensitivity) analysis
(design spec §20).

Reuse audit: a sweep is a specialized batch of re-solves -- one run
per perturbed value -- reusing ``OptimizationExecutor``'s machinery
once per value rather than a second execution path (§20, mirroring
``simulation.SensitivityAnalyzer``'s identical reuse posture).
Distributional treatment of swept outcomes is a call into
``analytics`` (``distribution``/``confidence_interval``), never a
correlation/regression/moment computation of this package's own
(§35's no-statistics-reimplementation proof). Perturbed problem
variants are transient copies via the frozen ``OptimizationProblem``'s
own ``replace()`` -- the published, governed artifact is never edited
in place (§9, §34).
"""

from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Sequence

from mineproductivity.analytics import (
    ConfidenceInterval,
    DistributionSummary,
    confidence_interval,
    distribution,
)

from mineproductivity.optimization.abstractions import OptimizationContext
from mineproductivity.optimization.exceptions import OptimizationValidationError
from mineproductivity.optimization.executor import OptimizationExecutor
from mineproductivity.optimization.persistence import OptimizationRunRepository
from mineproductivity.optimization.problem import OptimizationProblem
from mineproductivity.optimization.result import OptimizationResult
from mineproductivity.optimization.run import OptimizationRun
from mineproductivity.optimization.state import OptimizationState

__all__ = ["SensitivityAnalyzer"]


class SensitivityAnalyzer:
    """Performs post-optimality analysis on a solved problem: how the
    optimal objective and feasibility respond to perturbing a named
    constraint's bound or objective's weight (design spec §20). Not to
    be confused with ``simulation.SensitivityAnalyzer`` -- two
    domain-appropriate uses of the same operations-research term in
    two packages' own namespaces."""

    def __init__(
        self, *, executor: OptimizationExecutor, repository: OptimizationRunRepository
    ) -> None:
        self._executor = executor
        self._repository = repository

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(executor={self._executor!r}, repository={self._repository!r})"
        )

    def sweep(
        self,
        base_problem: OptimizationProblem,
        *,
        target: str,
        values: Sequence[float],
        context: OptimizationContext,
    ) -> Sequence[OptimizationResult]:
        """Produces one re-solve per value in ``values``, each a copy
        of ``base_problem`` with the named constraint bound or
        objective weight (``target``) overridden -- ordered to match
        ``values``' order (design spec §20). Zero values is a
        legitimately incomplete input: an empty sequence is returned,
        never a raise (§28)."""
        results: list[OptimizationResult] = []
        suffix = uuid.uuid4().hex[:8]
        for index, value in enumerate(values):
            variant = self._perturbed(base_problem, target, value)
            run_id = f"{base_problem.code}::sweep-{index:04d}-{suffix}"
            self._repository.add(
                OptimizationRun(
                    id=run_id,
                    problem_code=base_problem.code,
                    state=OptimizationState(attributes={"provisioned": True}),
                )
            )
            results.append(self._executor.execute(run_id, variant, context=context))
        return tuple(results)

    @staticmethod
    def _perturbed(
        base_problem: OptimizationProblem, target: str, value: float
    ) -> OptimizationProblem:
        """A transient copy of ``base_problem`` with ``target``'s
        constraint bound (checked first) or objective weight
        overridden -- never a mutation or republication of the
        governed artifact."""
        for index, constraint in enumerate(base_problem.constraints):
            if constraint.name == target:
                perturbed = dataclasses.replace(constraint, bound=value)
                constraints = (
                    base_problem.constraints[:index]
                    + (perturbed,)
                    + base_problem.constraints[index + 1 :]
                )
                return base_problem.replace(constraints=constraints)
        for index, objective in enumerate(base_problem.objectives):
            if objective.name == target:
                perturbed_objective = dataclasses.replace(objective, weight=value)
                objectives = (
                    base_problem.objectives[:index]
                    + (perturbed_objective,)
                    + base_problem.objectives[index + 1 :]
                )
                return base_problem.replace(objectives=objectives)
        raise OptimizationValidationError(
            f"target {target!r} names neither a constraint nor an objective of "
            f"problem {base_problem.code!r}"
        )

    def summarize(
        self, outcomes: Sequence[float], *, confidence: float = 0.95
    ) -> tuple[DistributionSummary, ConfidenceInterval]:
        """Hands a sweep's numeric outcomes to ``analytics`` for
        distributional treatment -- this method owns no arithmetic of
        its own (design spec §20, §35)."""
        return (
            distribution(outcomes),
            confidence_interval(outcomes, confidence=confidence),
        )
