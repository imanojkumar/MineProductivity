"""Tests for mineproductivity.simulation.run."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from mineproductivity.core import BaseEntity
from mineproductivity.simulation.run import RunStatus, SimulationRun
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _state(**attributes: object) -> SimulationState:
    return SimulationState(attributes=attributes or {"provisioned": True}, simulated_time=_EPOCH)


def _run(run_id: str = "RUN-1", **kwargs: object) -> SimulationRun:
    kwargs.setdefault("scenario_code", "FLEET.NightShiftSurge")
    kwargs.setdefault("state", _state())
    return SimulationRun(id=run_id, **kwargs)  # type: ignore[arg-type]


class TestRunStatus:
    def test_exactly_the_five_members_of_design_spec_10(self) -> None:
        assert {member.value for member in RunStatus} == {
            "scheduled",
            "running",
            "paused",
            "completed",
            "failed",
        }


class TestSimulationRunIsABaseEntity:
    def test_subclasses_base_entity_and_is_concrete(self) -> None:
        assert issubclass(SimulationRun, BaseEntity)
        run = _run()  # concrete: no abstract method (§10's recorded difference from Twin)
        assert run.status is RunStatus.SCHEDULED

    def test_same_id_different_state_compare_equal(self) -> None:
        first = _run("RUN-1")
        second = _run("RUN-1", state=_state(queue_len=9), status=RunStatus.COMPLETED)
        assert first == second
        assert hash(first) == hash(second)

    def test_different_ids_never_compare_equal(self) -> None:
        assert _run("RUN-1") != _run("RUN-2")

    def test_eq_and_hash_are_inherited_from_base_entity_unchanged(self) -> None:
        assert "__eq__" not in SimulationRun.__dict__
        assert "__hash__" not in SimulationRun.__dict__
        assert SimulationRun.__eq__ is BaseEntity.__eq__
        assert SimulationRun.__hash__ is BaseEntity.__hash__


class TestImmutabilityAndWithState:
    def test_state_cannot_be_reassigned(self) -> None:
        run = _run()
        with pytest.raises(dataclasses.FrozenInstanceError):
            run.state = _state(queue_len=1)  # type: ignore[misc]

    def test_status_cannot_be_reassigned(self) -> None:
        run = _run()
        with pytest.raises(dataclasses.FrozenInstanceError):
            run.status = RunStatus.RUNNING  # type: ignore[misc]

    def test_with_state_returns_a_new_instance_and_leaves_the_original_untouched(self) -> None:
        run = _run()
        replacement = run.with_state(_state(queue_len=1), status=RunStatus.RUNNING)
        assert replacement is not run
        assert replacement == run  # same identity (§10)
        assert replacement.status is RunStatus.RUNNING
        assert run.status is RunStatus.SCHEDULED
        assert run.state.attributes == {"provisioned": True}

    def test_with_state_status_defaults_to_current(self) -> None:
        run = _run(status=RunStatus.RUNNING)
        assert run.with_state(_state(queue_len=1)).status is RunStatus.RUNNING

    def test_with_state_preserves_id_and_scenario_code(self) -> None:
        replacement = _run().with_state(_state(queue_len=1))
        assert replacement.id == "RUN-1"
        assert replacement.scenario_code == "FLEET.NightShiftSurge"
