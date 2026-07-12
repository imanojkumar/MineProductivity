"""Tests for mineproductivity.visualization.persistence (design spec
§22, §33's repository-substitutability proof: written against the
``core.BaseRepository[Dashboard, str]`` contract alone)."""

from __future__ import annotations

from typing import get_args

import pytest

from mineproductivity.core import (
    BaseRepository,
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
)
from mineproductivity.visualization.dashboard import Dashboard
from mineproductivity.visualization.persistence import DashboardRepository


def _dashboard(dashboard_id: str) -> Dashboard:
    return Dashboard(id=dashboard_id, name="Night Shift Handover", owner="supervisor-a")


def _make_repository() -> BaseRepository[Dashboard, str]:
    reference: InMemoryRepository[Dashboard, str] = InMemoryRepository()
    return reference


class TestAlias:
    def test_is_a_literal_type_alias_over_core_base_repository(self) -> None:
        aliased = DashboardRepository.__value__
        assert aliased.__origin__ is BaseRepository
        assert get_args(aliased) == (Dashboard, str)
        assert type(_make_repository()) is InMemoryRepository


class TestRepositoryContract:
    def test_full_contract_round_trip(self) -> None:
        repository = _make_repository()
        dashboard = _dashboard("DASH-1")
        repository.add(dashboard)
        assert repository.get("DASH-1") is dashboard
        assert repository.find("DASH-1").unwrap() is dashboard
        assert repository.find("NO-SUCH").is_nothing
        assert "DASH-1" in repository
        with pytest.raises(DuplicateError):
            repository.add(_dashboard("DASH-1"))
        repository.add(_dashboard("DASH-2"))
        assert sorted(d.id for d in repository.list()) == ["DASH-1", "DASH-2"]
        repository.remove("DASH-1")
        with pytest.raises(NotFoundError):
            repository.get("DASH-1")
        with pytest.raises(NotFoundError):
            repository.remove("NO-SUCH")

    def test_concurrent_writes_to_different_ids_do_not_contend(self) -> None:
        """Design spec §29: distinct ids target distinct keys; the
        bare InMemoryRepository provides no locking of its own, so
        this test keeps each thread on its own id."""
        from concurrent.futures import ThreadPoolExecutor

        repository = _make_repository()

        def _add(index: int) -> None:
            repository.add(_dashboard(f"DASH-{index}"))

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(_add, range(32)))
        assert len(repository.list()) == 32
