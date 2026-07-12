"""Tests for mineproductivity.visualization.dashboard (design spec
§10)."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.core import BaseEntity
from mineproductivity.visualization.dashboard import Dashboard
from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.widget import Widget


def _dashboard(dashboard_id: str = "DASH-1", **overrides: object) -> Dashboard:
    kwargs: dict[str, object] = {
        "id": dashboard_id,
        "name": "Night Shift Handover",
        "owner": "supervisor-a",
    }
    kwargs.update(overrides)
    return Dashboard(**kwargs)  # type: ignore[arg-type]


class TestIdentity:
    def test_same_id_different_widgets_compare_equal(self) -> None:
        """Design spec §33: BaseEntity-inherited identity equality."""
        bare = _dashboard()
        widgeted = dataclasses.replace(
            bare, widgets=(Widget(code="w", visualization_code="KPI_CARD.Standard"),)
        )
        assert bare == widgeted
        assert hash(bare) == hash(widgeted)

    def test_different_ids_never_equal(self) -> None:
        assert _dashboard("DASH-1") != _dashboard("DASH-2")

    def test_eq_and_hash_are_inherited_unchanged_from_base_entity(self) -> None:
        assert "__eq__" not in Dashboard.__dict__
        assert "__hash__" not in Dashboard.__dict__
        assert Dashboard.__eq__ is BaseEntity.__eq__
        assert Dashboard.__hash__ is BaseEntity.__hash__

    def test_same_name_under_different_owners_is_never_a_conflict(self) -> None:
        """Design spec §23: id, not name, is the identity."""
        one = _dashboard("DASH-1", owner="supervisor-a")
        other = _dashboard("DASH-2", owner="supervisor-b")
        assert one.name == other.name
        assert one != other


class TestValidation:
    def test_empty_name_raises(self) -> None:
        with pytest.raises(VisualizationValidationError, match="name"):
            _dashboard(name="  ")

    def test_empty_owner_raises(self) -> None:
        with pytest.raises(VisualizationValidationError, match="owner"):
            _dashboard(owner="")


class TestImmutability:
    def test_frozen_and_changed_only_via_replace(self) -> None:
        original = _dashboard()
        with pytest.raises(dataclasses.FrozenInstanceError):
            original.theme_code = "DARK"  # type: ignore[misc]
        updated = dataclasses.replace(original, theme_code="DARK_HIGH_CONTRAST")
        assert original.theme_code == ""
        assert updated.theme_code == "DARK_HIGH_CONTRAST"

    def test_no_status_field_and_no_with_state_method(self) -> None:
        """Design spec §10, §32: a configuration entity has no
        execution lifecycle to track -- a deliberate departure from
        Twin/SimulationRun/OptimizationRun/Task."""
        field_names = {field.name for field in dataclasses.fields(Dashboard)}
        assert "status" not in field_names
        assert not hasattr(Dashboard, "with_state")

    def test_defaults(self) -> None:
        dashboard = _dashboard()
        assert dashboard.widgets == ()
        assert dashboard.layout is None
        assert dashboard.theme_code == ""
