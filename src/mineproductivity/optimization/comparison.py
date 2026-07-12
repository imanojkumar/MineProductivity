"""``PlanComparator``: plan comparison (design spec §19).

Reuse audit: every statistical treatment is a call into ``analytics``
(``describe`` over an ``analytics.TimeSeries`` assembled from
``OptimizationResult.objective_value``/``solution`` values) -- never a
mean/percentile computation of this package's own (§19, §35's
no-statistics-reimplementation proof), mirroring
``simulation.ScenarioComparator``'s identical posture. The comparison
judgment itself is the caller's -- a ``decision``-layer question.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mineproductivity.analytics import StatisticalSummary, TimeSeries, TimeSeriesPoint, describe

from mineproductivity.optimization.exceptions import OptimizationValidationError
from mineproductivity.optimization.result import OptimizationResult

__all__ = ["PlanComparator"]


class PlanComparator:
    """Compares ``OptimizationResult`` collections across two or more
    problems or solver configurations by delegating statistical
    treatment to ``analytics`` (design spec §19)."""

    def compare(
        self,
        results_by_problem: Mapping[str, Sequence[OptimizationResult]],
        *,
        variable: str | None = None,
    ) -> Mapping[str, StatisticalSummary]:
        """For each problem key, extracts ``objective_value`` (or, when
        ``variable`` names one, that solution variable's value) from
        its result sequence and calls ``analytics.describe()`` --
        never re-implements mean/percentile computation here (§19)."""
        summaries: dict[str, StatisticalSummary] = {}
        for problem_key, results in results_by_problem.items():
            if not results:
                raise OptimizationValidationError(
                    f"PlanComparator.compare received zero results for problem "
                    f"{problem_key!r}; there is nothing to summarize"
                )
            points: list[TimeSeriesPoint] = []
            for result in results:
                value = (
                    result.solution.get(variable)
                    if variable is not None
                    else result.objective_value
                )
                if value is not None:
                    points.append(TimeSeriesPoint(timestamp=result.computed_at, value=float(value)))
            if not points:
                target = variable if variable is not None else "objective_value"
                raise OptimizationValidationError(
                    f"no numeric {target!r} values exist among problem {problem_key!r}'s results"
                )
            summaries[problem_key] = describe(TimeSeries(points=tuple(points)))
        return summaries

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"
