"""Tests for mineproductivity.optimization.persistence (design spec
§24, §35's repository-substitutability proof: written against the
``core.BaseRepository[OptimizationRun, str]`` contract alone)."""

from __future__ import annotations

from typing import get_args

import pytest

from mineproductivity.core import (
    BaseRepository,
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
)
from mineproductivity.optimization.persistence import OptimizationRunRepository
from mineproductivity.optimization.run import OptimizationRun
from mineproductivity.optimization.state import OptimizationState


def _run(run_id: str) -> OptimizationRun:
    return OptimizationRun(
        id=run_id,
        problem_code="TEST.PersistenceProblem",
        state=OptimizationState(attributes={"provisioned": True}),
    )


def _make_repository() -> BaseRepository[OptimizationRun, str]:
    reference: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    return reference


class TestAlias:
    def test_is_a_literal_type_alias_over_core_base_repository(self) -> None:
        aliased = OptimizationRunRepository.__value__
        assert aliased.__origin__ is BaseRepository
        assert get_args(aliased) == (OptimizationRun, str)
        assert type(_make_repository()) is InMemoryRepository


class TestRepositoryContract:
    def test_full_contract_round_trip(self) -> None:
        repository = _make_repository()
        run = _run("RUN-1")
        repository.add(run)
        assert repository.get("RUN-1") is run
        assert repository.find("RUN-1").unwrap() is run
        assert repository.find("NO-SUCH").is_nothing
        assert "RUN-1" in repository
        with pytest.raises(DuplicateError):
            repository.add(_run("RUN-1"))
        repository.add(_run("RUN-2"))
        assert sorted(r.id for r in repository.list()) == ["RUN-1", "RUN-2"]
        repository.remove("RUN-1")
        with pytest.raises(NotFoundError):
            repository.get("RUN-1")
        with pytest.raises(NotFoundError):
            repository.remove("NO-SUCH")
