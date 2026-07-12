"""Tests for mineproductivity.simulation.persistence.

Design spec §35's repository-substitutability proof: every test here is
written against the ``core.BaseRepository[SimulationRun, str]``
contract alone (via the one ``_make_repository`` seam below), never
against ``InMemoryRepository``-specific internals.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import get_args

import pytest

from mineproductivity.core import (
    BaseRepository,
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
)
from mineproductivity.simulation.persistence import SimulationRunRepository
from mineproductivity.simulation.run import SimulationRun
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _run(run_id: str) -> SimulationRun:
    return SimulationRun(
        id=run_id,
        scenario_code="TEST.PersistenceScenario",
        state=SimulationState(attributes={"provisioned": True}, simulated_time=_EPOCH),
    )


def _make_repository() -> BaseRepository[SimulationRun, str]:
    """The single substitution seam (design spec §24, §35)."""
    reference: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    return reference


class TestSimulationRunRepositoryAlias:
    def test_is_a_literal_type_alias_over_core_base_repository(self) -> None:
        aliased = SimulationRunRepository.__value__
        assert aliased.__origin__ is BaseRepository
        assert get_args(aliased) == (SimulationRun, str)

    def test_reference_implementation_is_core_in_memory_repository_unchanged(self) -> None:
        assert type(_make_repository()) is InMemoryRepository


class TestRepositoryContract:
    def test_add_then_get_round_trips(self) -> None:
        repository = _make_repository()
        run = _run("RUN-1")
        repository.add(run)
        assert repository.get("RUN-1") is run

    def test_add_rejects_a_duplicate_id(self) -> None:
        repository = _make_repository()
        repository.add(_run("RUN-1"))
        with pytest.raises(DuplicateError):
            repository.add(_run("RUN-1"))

    def test_get_of_unknown_id_raises(self) -> None:
        with pytest.raises(NotFoundError):
            _make_repository().get("NO-SUCH-RUN")

    def test_find_returns_maybe(self) -> None:
        repository = _make_repository()
        run = _run("RUN-1")
        repository.add(run)
        assert repository.find("RUN-1").unwrap() is run
        assert repository.find("NO-SUCH-RUN").is_nothing

    def test_remove_then_get_raises(self) -> None:
        repository = _make_repository()
        repository.add(_run("RUN-1"))
        repository.remove("RUN-1")
        with pytest.raises(NotFoundError):
            repository.get("RUN-1")

    def test_list_and_contains(self) -> None:
        repository = _make_repository()
        repository.add(_run("RUN-1"))
        repository.add(_run("RUN-2"))
        assert sorted(run.id for run in repository.list()) == ["RUN-1", "RUN-2"]
        assert "RUN-1" in repository
        assert "NO-SUCH-RUN" not in repository
