"""Tests for mineproductivity.simulation.result."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.core.serialization import DataclassSerializer, to_dict
from mineproductivity.simulation.result import ExperimentResult, SimulationResult
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _state() -> SimulationState:
    return SimulationState(attributes={"outcome": 42.0}, simulated_time=_EPOCH)


class TestSimulationResult:
    def test_defaults(self) -> None:
        result = SimulationResult()
        assert result.run_id == ""
        assert result.warnings == ()
        assert result.final_state is None
        assert result.computed_at.tzinfo is timezone.utc

    def test_carries_the_final_state(self) -> None:
        assert SimulationResult(run_id="RUN-1", final_state=_state()).final_state == _state()


class TestExperimentResult:
    def test_aggregates_trial_results_without_characterizing_them(self) -> None:
        """Design spec §18: an aggregation, not a statistical
        characterization -- no mean/percentile field exists here."""
        trials = (SimulationResult(run_id="RUN-1"), SimulationResult(run_id="RUN-2"))
        result = ExperimentResult(trial_results=trials)
        assert result.trial_results == trials
        field_names = set(ExperimentResult.__dataclass_fields__)
        assert field_names == {
            "run_id",
            "computed_at",
            "warnings",
            "final_state",
            "trial_results",
        }

    def test_is_a_simulation_result(self) -> None:
        assert issubclass(ExperimentResult, SimulationResult)


class TestSerialization:
    _INSTANCES = (
        SimulationResult(run_id="RUN-1"),
        SimulationResult(run_id="RUN-1", final_state=_state()),
        ExperimentResult(trial_results=(SimulationResult(run_id="RUN-1"),)),
    )

    @pytest.mark.parametrize("instance", _INSTANCES)
    def test_to_dict_works_generically_for_every_result_type(self, instance: object) -> None:
        data = to_dict(instance)
        assert isinstance(data, dict)
        assert data

    @pytest.mark.parametrize("instance", _INSTANCES)
    def test_no_result_type_defines_its_own_to_dict_method(self, instance: object) -> None:
        assert "to_dict" not in type(instance).__dict__

    def test_simulation_result_round_trips(self) -> None:
        serializer = DataclassSerializer(SimulationResult)
        original = SimulationResult(run_id="RUN-1", warnings=("zero trials",))
        assert serializer.deserialize(serializer.serialize(original)) == original
