"""``SensitivityAnalyzer``: sensitivity analysis (design spec §20).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
A sweep is, structurally, a specialized ``Experiment`` -- one run per
swept value rather than one run per random trial -- reusing
``ExperimentRunner``'s machinery rather than a second execution path
(design spec §20). Distributional treatment of swept outcomes is a
call into ``analytics`` (``distribution``/``confidence_interval``),
never a correlation/regression/moment computation of this package's
own (§20, §35's no-statistics-reimplementation proof). Swept scenario
variants are transient, per-run copies produced via the frozen
``Scenario``'s own ``replace()`` -- the published, governed artifact
is never edited in place (§9, §34's recorded anti-pattern; the
variants are never published).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mineproductivity.analytics import (
    ConfidenceInterval,
    DistributionSummary,
    confidence_interval,
    distribution,
)

from mineproductivity.simulation.abstractions import SimulationContext
from mineproductivity.simulation.experiment import Experiment, ExperimentRunner
from mineproductivity.simulation.scenario import Scenario

__all__ = ["SensitivityAnalyzer"]


class SensitivityAnalyzer:
    """Sweeps one or more ``Scenario`` parameters across an
    ``Experiment``, handing the resulting outcomes to ``analytics`` for
    distributional treatment -- the sensitivity *computation* itself is
    ``analytics``' job, not this package's, mirroring
    ``ScenarioComparator``'s identical delegation (design spec §19,
    §20)."""

    def __init__(self, *, runner: ExperimentRunner) -> None:
        self._runner = runner

    def __repr__(self) -> str:
        return f"{type(self).__name__}(runner={self._runner!r})"

    def sweep(
        self,
        base_scenario: Scenario,
        *,
        parameter: str,
        values: Sequence[Any],
        context: SimulationContext,
    ) -> Experiment:
        """Produces one ``SimulationRun`` per value in ``values``, each
        a copy of ``base_scenario`` with ``parameter`` overridden --
        the resulting ``Experiment``'s ``run_ids`` are ordered to match
        ``values``' order, so a caller can zip them back together for
        ``analytics``' own correlation/regression primitives to consume
        (design spec §20). Zero values is a legitimately incomplete
        input (§28): an empty ``Experiment`` is returned, never a
        raise."""
        run_ids: list[str] = []
        for value in values:
            variant = base_scenario.replace(
                parameters={**dict(base_scenario.parameters), parameter: value}
            )
            experiment = self._runner.run_trials(variant, trials=1, context=context)
            run_ids.extend(experiment.run_ids)
        return Experiment(
            name=f"{base_scenario.code}::sweep({parameter})",
            scenario=base_scenario,
            run_ids=tuple(run_ids),
        )

    def summarize(
        self, outcomes: Sequence[float], *, confidence: float = 0.95
    ) -> tuple[DistributionSummary, ConfidenceInterval]:
        """Hands a sweep's numeric outcomes to ``analytics`` for
        distributional treatment -- ``analytics.distribution()`` for
        shape, ``analytics.confidence_interval()`` for the interval
        around the mean (design spec §20). This method owns no
        arithmetic of its own; both computations, including their own
        input validation, are ``analytics``' entirely."""
        return (
            distribution(outcomes),
            confidence_interval(outcomes, confidence=confidence),
        )
