"""Tests for mineproductivity.simulation.clock."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.simulation.clock import SimulationClock, TimeProgressionMode
from mineproductivity.simulation.exceptions import SimulationValidationError

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestTimeProgressionMode:
    def test_exactly_the_three_members_of_design_spec_11(self) -> None:
        assert {member.value for member in TimeProgressionMode} == {
            "fixed_timestep",
            "next_event",
            "trial_based",
        }


class TestSimulationClock:
    def test_fixed_timestep_advances_by_the_constructor_dt(self) -> None:
        clock = SimulationClock(mode=TimeProgressionMode.FIXED_TIMESTEP, dt=timedelta(minutes=5))
        assert clock.advance(_EPOCH) == _EPOCH + timedelta(minutes=5)

    def test_fixed_timestep_ignores_a_per_call_delta(self) -> None:
        clock = SimulationClock(mode=TimeProgressionMode.FIXED_TIMESTEP, dt=timedelta(minutes=5))
        assert clock.advance(_EPOCH, delta=timedelta(hours=9)) == _EPOCH + timedelta(minutes=5)

    def test_fixed_timestep_without_dt_raises_at_construction(self) -> None:
        with pytest.raises(SimulationValidationError, match="requires a dt"):
            SimulationClock(mode=TimeProgressionMode.FIXED_TIMESTEP)

    def test_next_event_advances_by_the_model_supplied_delta(self) -> None:
        clock = SimulationClock(mode=TimeProgressionMode.NEXT_EVENT)
        assert clock.advance(_EPOCH, delta=timedelta(minutes=17)) == _EPOCH + timedelta(minutes=17)

    def test_next_event_without_delta_raises_per_call(self) -> None:
        clock = SimulationClock(mode=TimeProgressionMode.NEXT_EVENT)
        with pytest.raises(SimulationValidationError, match="requires a delta"):
            clock.advance(_EPOCH)

    def test_trial_based_never_advances_continuous_time(self) -> None:
        clock = SimulationClock(mode=TimeProgressionMode.TRIAL_BASED)
        assert clock.advance(_EPOCH) == _EPOCH
        assert clock.advance(_EPOCH, delta=timedelta(hours=1)) == _EPOCH

    def test_repr_names_the_mode(self) -> None:
        assert "TRIAL_BASED" in repr(SimulationClock(mode=TimeProgressionMode.TRIAL_BASED))
