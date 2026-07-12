"""Tests for mineproductivity.visualization.discovery (design spec
§27, §31)."""

from __future__ import annotations

from mineproductivity.core import InMemoryRepository
from mineproductivity.visualization.dashboard import Dashboard
from mineproductivity.visualization.discovery import by_owner, by_theme


def _dashboard(dashboard_id: str, *, owner: str = "supervisor-a", theme: str = "") -> Dashboard:
    return Dashboard(id=dashboard_id, name="Night Shift Handover", owner=owner, theme_code=theme)


class TestByTheme:
    def test_matches_and_empty_result_never_raises(self) -> None:
        repository: InMemoryRepository[Dashboard, str] = InMemoryRepository()
        repository.add(_dashboard("DASH-1", theme="DARK_HIGH_CONTRAST"))
        repository.add(_dashboard("DASH-2"))
        matched = repository.list(by_theme("DARK_HIGH_CONTRAST"))
        assert [dashboard.id for dashboard in matched] == ["DASH-1"]
        assert list(repository.list(by_theme("NEVER_USED"))) == []


class TestByOwner:
    def test_matches_and_empty_result_never_raises(self) -> None:
        repository: InMemoryRepository[Dashboard, str] = InMemoryRepository()
        repository.add(_dashboard("DASH-1", owner="supervisor-a"))
        repository.add(_dashboard("DASH-2", owner="supervisor-b"))
        matched = repository.list(by_owner("supervisor-b"))
        assert [dashboard.id for dashboard in matched] == ["DASH-2"]
        assert list(repository.list(by_owner("nobody"))) == []

    def test_is_a_convenience_query_not_an_access_control_boundary(self) -> None:
        """Design spec §31: every stored dashboard remains readable
        regardless of owner -- the filter narrows, it never hides."""
        repository: InMemoryRepository[Dashboard, str] = InMemoryRepository()
        repository.add(_dashboard("DASH-1", owner="supervisor-a"))
        repository.add(_dashboard("DASH-2", owner="supervisor-b"))
        assert len(repository.list()) == 2
        assert repository.get("DASH-2").owner == "supervisor-b"
