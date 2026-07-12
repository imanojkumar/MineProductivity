"""``ScenarioComparator``: scenario comparison (design spec §19).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
Every statistical treatment is a call into ``analytics`` --
``analytics.describe()`` over an ``analytics.TimeSeries`` assembled
from the supplied ``SimulationState``\\ s -- never a mean/percentile
computation of this package's own (design spec §19, §35's
no-statistics-reimplementation proof; ADR-0009's recorded trade-off:
this class is a thin orchestration layer whose entire value is in
assembling the right series for ``analytics`` to consume). The
comparison judgment itself (what counts as a "better" outcome) is left
to the caller -- that is a ``decision``-layer question (spec 07 §3).

One small, disclosed resolution beyond §19's bare pseudocode:
``compare`` accepts an optional ``attribute`` keyword naming which
``SimulationState.attributes`` key to extract -- §19's own prose
("extracts the numeric attribute(s) of interest") requires the class
to know which attribute that is, and nothing in the pseudocode
signature supplies it. When omitted, the single numeric attribute
common to the supplied states is auto-selected; an ambiguous or absent
candidate set raises ``SimulationValidationError`` naming the options.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mineproductivity.analytics import StatisticalSummary, TimeSeries, TimeSeriesPoint, describe

from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.state import SimulationState

__all__ = ["ScenarioComparator"]


class ScenarioComparator:
    """Compares simulation outcomes across two or more scenarios by
    delegating statistical treatment to ``analytics`` -- never
    computing descriptive statistics itself (design spec §19)."""

    def compare(
        self,
        results_by_scenario: Mapping[str, Sequence[SimulationState]],
        *,
        attribute: str | None = None,
    ) -> Mapping[str, StatisticalSummary]:
        """For each scenario key, extracts the numeric attribute of
        interest from its ``SimulationState`` sequence and calls
        ``analytics.describe()`` -- never re-implements
        mean/percentile computation here (design spec §19)."""
        summaries: dict[str, StatisticalSummary] = {}
        for scenario_key, states in results_by_scenario.items():
            if not states:
                raise SimulationValidationError(
                    f"ScenarioComparator.compare received zero states for scenario "
                    f"{scenario_key!r}; there is nothing to summarize"
                )
            chosen = attribute if attribute is not None else self._sole_numeric(states)
            points = tuple(
                TimeSeriesPoint(
                    timestamp=state.simulated_time, value=float(state.attributes[chosen])
                )
                for state in states
                if isinstance(state.attributes.get(chosen), (int, float))
                and not isinstance(state.attributes.get(chosen), bool)
            )
            if not points:
                raise SimulationValidationError(
                    f"attribute {chosen!r} is not a numeric attribute of scenario "
                    f"{scenario_key!r}'s states"
                )
            summaries[scenario_key] = describe(TimeSeries(points=points))
        return summaries

    @staticmethod
    def _sole_numeric(states: Sequence[SimulationState]) -> str:
        candidates = sorted(
            {
                key
                for state in states
                for key, value in state.attributes.items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            }
        )
        if len(candidates) != 1:
            raise SimulationValidationError(
                f"ScenarioComparator.compare cannot auto-select the attribute of "
                f"interest: numeric candidates are {candidates!r}; name one explicitly "
                f"via the attribute keyword"
            )
        return candidates[0]

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"
