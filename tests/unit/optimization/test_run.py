"""Tests for mineproductivity.optimization.run."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core import BaseEntity
from mineproductivity.optimization.run import OptimizationRun, RunStatus
from mineproductivity.optimization.state import OptimizationState


def _run(run_id: str = "RUN-1", **kwargs: object) -> OptimizationRun:
    kwargs.setdefault("problem_code", "FLEET.NightShiftAllocation")
    kwargs.setdefault("state", OptimizationState(attributes={"provisioned": True}))
    return OptimizationRun(id=run_id, **kwargs)  # type: ignore[arg-type]


class TestRunStatus:
    def test_exactly_the_five_members_of_design_spec_10(self) -> None:
        assert {member.value for member in RunStatus} == {
            "scheduled",
            "running",
            "paused",
            "completed",
            "failed",
        }


class TestOptimizationRun:
    def test_identity_based_equality_inherited_unchanged(self) -> None:
        first = _run("RUN-1")
        second = _run("RUN-1", status=RunStatus.COMPLETED)
        assert first == second
        assert hash(first) == hash(second)
        assert _run("RUN-1") != _run("RUN-2")
        assert "__eq__" not in OptimizationRun.__dict__
        assert OptimizationRun.__eq__ is BaseEntity.__eq__
        assert OptimizationRun.__hash__ is BaseEntity.__hash__

    def test_immutable_with_state_produces_a_new_instance(self) -> None:
        run = _run()
        with pytest.raises(dataclasses.FrozenInstanceError):
            run.status = RunStatus.RUNNING  # type: ignore[misc]
        replacement = run.with_state(
            OptimizationState(attributes={"incumbent": 1.0}), status=RunStatus.RUNNING
        )
        assert replacement is not run
        assert replacement == run  # same identity
        assert replacement.status is RunStatus.RUNNING
        assert run.status is RunStatus.SCHEDULED

    def test_with_state_status_defaults_to_current(self) -> None:
        run = _run(status=RunStatus.RUNNING)
        assert run.with_state(run.state).status is RunStatus.RUNNING
