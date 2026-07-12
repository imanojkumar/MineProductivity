"""Tests for mineproductivity.simulation.comparison."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.analytics import StatisticalSummary
from mineproductivity.simulation import comparison as comparison_module
from mineproductivity.simulation.comparison import ScenarioComparator
from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _states(*values: float, attribute: str = "outcome") -> list[SimulationState]:
    return [
        SimulationState(
            attributes={attribute: value},
            simulated_time=_EPOCH + timedelta(minutes=index),
        )
        for index, value in enumerate(values)
    ]


class TestCompare:
    def test_returns_an_analytics_statistical_summary_per_scenario(self) -> None:
        comparator = ScenarioComparator()
        summaries = comparator.compare(
            {
                "baseline": _states(10.0, 20.0, 30.0),
                "surge": _states(40.0, 50.0, 60.0),
            }
        )
        assert set(summaries) == {"baseline", "surge"}
        assert isinstance(summaries["baseline"], StatisticalSummary)
        assert summaries["baseline"].mean == 20.0
        assert summaries["surge"].mean == 50.0

    def test_delegates_to_analytics_describe(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Design spec §35's delegation proof: assert the actual
        ``analytics`` primitive invoked, never re-derive the expected
        statistic independently here."""
        calls: list[int] = []
        real_describe = comparison_module.describe

        def _spy(series: object) -> StatisticalSummary:
            calls.append(1)
            return real_describe(series)  # type: ignore[arg-type]

        monkeypatch.setattr(comparison_module, "describe", _spy)
        ScenarioComparator().compare({"only": _states(1.0, 2.0)})
        assert calls == [1]

    def test_explicit_attribute_selects_among_several_numeric_keys(self) -> None:
        states = [
            SimulationState(
                attributes={"outcome": 10.0, "queue_len": 4},
                simulated_time=_EPOCH,
            ),
            SimulationState(
                attributes={"outcome": 20.0, "queue_len": 6},
                simulated_time=_EPOCH + timedelta(minutes=1),
            ),
        ]
        summaries = ScenarioComparator().compare({"only": states}, attribute="queue_len")
        assert summaries["only"].mean == 5.0

    def test_ambiguous_auto_selection_raises_naming_the_candidates(self) -> None:
        states = [
            SimulationState(attributes={"outcome": 10.0, "queue_len": 4}, simulated_time=_EPOCH)
        ]
        with pytest.raises(SimulationValidationError, match="queue_len"):
            ScenarioComparator().compare({"only": states})

    def test_zero_states_for_a_scenario_raises(self) -> None:
        with pytest.raises(SimulationValidationError, match="zero states"):
            ScenarioComparator().compare({"empty": []})

    def test_non_numeric_attribute_raises(self) -> None:
        states = [SimulationState(attributes={"label": "high"}, simulated_time=_EPOCH)]
        with pytest.raises(SimulationValidationError):
            ScenarioComparator().compare({"only": states}, attribute="label")

    def test_repr(self) -> None:
        assert repr(ScenarioComparator()) == "ScenarioComparator()"
