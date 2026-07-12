"""Tests for mineproductivity.optimization.sensitivity."""

from __future__ import annotations

import pytest

from mineproductivity.analytics import ConfidenceInterval, DistributionSummary
from mineproductivity.core import InMemoryRepository
from mineproductivity.optimization import sensitivity as sensitivity_module
from mineproductivity.optimization.abstractions import OptimizationContext
from mineproductivity.optimization.exceptions import OptimizationValidationError
from mineproductivity.optimization.executor import OptimizationExecutor
from mineproductivity.optimization.problem import (
    Constraint,
    ConstraintOperator,
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationProblem,
    ProblemStatus,
    VariableDomain,
    published_problem,
)
from mineproductivity.optimization.run import OptimizationRun
from mineproductivity.optimization.sensitivity import SensitivityAnalyzer
from mineproductivity.optimization._registry import register
from mineproductivity.optimization.mixed_integer_programming import (
    MixedIntegerProgrammingModel,
)
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata
from mineproductivity.optimization.result import OptimizationResult


@register
class _SensitivityBoundEcho(MixedIntegerProgrammingModel):
    meta = OptimizationMetadata(
        code="MIP.SensitivityBoundEcho",
        category=OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        description="Echoes the first constraint bound as the optimum.",
    )

    def _solve_mip(
        self, problem: OptimizationProblem, *, context: OptimizationContext
    ) -> OptimizationResult:
        bound = problem.constraints[0].bound if problem.constraints else 0.0
        return OptimizationResult(objective_value=bound)


def _problem() -> OptimizationProblem:
    return OptimizationProblem(
        code="TEST.SensitivityProblem",
        model_code="MIP.SensitivityBoundEcho",
        objectives=(Objective(name="tonnes", direction=ObjectiveDirection.MAXIMIZE),),
        constraints=(
            Constraint(
                name="truck_budget",
                expression="trucks",
                operator=ConstraintOperator.LESS_EQUAL,
                bound=27.0,
            ),
        ),
        variables=(DecisionVariable(name="trucks", domain=VariableDomain.INTEGER),),
    )


def _analyzer() -> SensitivityAnalyzer:
    repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    executor = OptimizationExecutor(repository=repository)
    return SensitivityAnalyzer(executor=executor, repository=repository)


class TestSweep:
    def test_one_re_solve_per_value_ordered_to_match(self) -> None:
        """Design spec §20: constraint-bound perturbation, ordered."""
        analyzer = _analyzer()
        bounds = [20.0, 25.0, 30.0]
        results = analyzer.sweep(
            _problem(), target="truck_budget", values=bounds, context=OptimizationContext()
        )
        assert [result.objective_value for result in results] == bounds

    def test_objective_weight_perturbation_is_the_second_target_kind(self) -> None:
        analyzer = _analyzer()
        results = analyzer.sweep(
            _problem(), target="tonnes", values=[0.5], context=OptimizationContext()
        )
        assert len(results) == 1  # weight override accepted; solve proceeds

    def test_unknown_target_raises(self) -> None:
        analyzer = _analyzer()
        with pytest.raises(OptimizationValidationError, match="neither a constraint"):
            analyzer.sweep(
                _problem(), target="no_such", values=[1.0], context=OptimizationContext()
            )

    def test_base_problem_is_never_edited_or_published(self) -> None:
        analyzer = _analyzer()
        base = _problem()
        analyzer.sweep(base, target="truck_budget", values=[20.0], context=OptimizationContext())
        assert base.constraints[0].bound == 27.0
        assert base.status is ProblemStatus.PROPOSED
        assert published_problem(base.code) is None

    def test_zero_values_returns_an_empty_sequence(self) -> None:
        analyzer = _analyzer()
        assert (
            analyzer.sweep(
                _problem(), target="truck_budget", values=[], context=OptimizationContext()
            )
            == ()
        )


class TestSummarize:
    def test_delegates_to_analytics_distribution_and_confidence_interval(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        invoked: list[str] = []
        real_distribution = sensitivity_module.distribution
        real_interval = sensitivity_module.confidence_interval

        def _spy_distribution(values: object) -> DistributionSummary:
            invoked.append("distribution")
            return real_distribution(values)  # type: ignore[arg-type]

        def _spy_interval(values: object, *, confidence: float = 0.95) -> ConfidenceInterval:
            invoked.append("confidence_interval")
            return real_interval(values, confidence=confidence)  # type: ignore[arg-type]

        monkeypatch.setattr(sensitivity_module, "distribution", _spy_distribution)
        monkeypatch.setattr(sensitivity_module, "confidence_interval", _spy_interval)

        analyzer = _analyzer()
        shape, interval = analyzer.summarize([10.0, 12.0, 11.0], confidence=0.9)
        assert invoked == ["distribution", "confidence_interval"]
        assert isinstance(shape, DistributionSummary)
        assert interval.confidence == 0.9

    def test_repr(self) -> None:
        assert "SensitivityAnalyzer" in repr(_analyzer())
