"""Tests for mineproductivity.visualization.dashboard_builder (design
spec §12): core.BaseBuilder's own contract, exercised concretely for
the first time in this series."""

from __future__ import annotations

import pytest

from mineproductivity.core import BaseBuilder
from mineproductivity.visualization.dashboard import Dashboard
from mineproductivity.visualization.dashboard_builder import DashboardBuilder
from mineproductivity.visualization.exceptions import VisualizationValidationError
from mineproductivity.visualization.layout import Layout
from mineproductivity.visualization.widget import Widget


def _widget(code: str) -> Widget:
    return Widget(code=code, visualization_code="KPI_CARD.Standard")


class TestFluentConstruction:
    def test_the_design_spec_15_worked_example_shape(self) -> None:
        dashboard = (
            DashboardBuilder(owner="shift-supervisor-a")
            .with_name("Night Shift Handover")
            .with_widget(_widget("tph_card"))
            .with_widget(_widget("plan_compare"))
            .with_layout(Layout(code="handover_grid", slots={"tph_card": "row=1;col=1"}))
            .with_theme("DARK_HIGH_CONTRAST")
            .build()
        )
        assert isinstance(dashboard, Dashboard)
        assert dashboard.name == "Night Shift Handover"
        assert dashboard.owner == "shift-supervisor-a"
        assert [widget.code for widget in dashboard.widgets] == ["tph_card", "plan_compare"]
        assert dashboard.layout is not None
        assert dashboard.theme_code == "DARK_HIGH_CONTRAST"

    def test_each_build_assigns_a_fresh_identity(self) -> None:
        builder = DashboardBuilder(owner="a").with_name("Shared Name")
        assert builder.build().id != builder.build().id


class TestBuilderContract:
    def test_is_a_concrete_core_base_builder_subclass(self) -> None:
        """Design spec §12: the first concrete core.BaseBuilder
        subclass anywhere in this series."""
        assert issubclass(DashboardBuilder, BaseBuilder)

    def test_build_raises_on_missing_name(self) -> None:
        with pytest.raises(VisualizationValidationError, match="name"):
            DashboardBuilder(owner="a").build()

    def test_build_raises_on_empty_owner(self) -> None:
        with pytest.raises(VisualizationValidationError, match="owner"):
            DashboardBuilder(owner="  ").with_name("X").build()

    def test_build_result_is_the_inherited_unoverridden_variant(self) -> None:
        """Design spec §12: no second non-raising variant."""
        assert "build_result" not in DashboardBuilder.__dict__
        outcome = DashboardBuilder(owner="a").build_result()
        assert outcome.is_err
        assert isinstance(outcome.error, VisualizationValidationError)
        assert DashboardBuilder(owner="a").with_name("X").build_result().is_ok

    def test_reset_makes_the_builder_reusable(self) -> None:
        """core.BaseBuilder.reset()'s own contract, exercised."""
        builder = (
            DashboardBuilder(owner="a")
            .with_name("First")
            .with_widget(_widget("w1"))
            .with_theme("DARK")
        )
        first = builder.build()
        second = builder.reset().with_name("Second").build()
        assert first.name == "First"
        assert second.name == "Second"
        assert second.widgets == ()
        assert second.theme_code == ""
        assert second.owner == "a"  # construction-time identity survives reset
