"""Tests for mineproductivity.ontology.maintenance.failure_mode."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.maintenance.failure_mode import FailureMode, MaintenanceWorkOrder


class TestFailureMode:
    def test_valid_construction(self) -> None:
        mode = FailureMode(id="HYD-001", failure_mode_code="HYD-001", system="hydraulic")
        assert mode.system == "hydraulic"

    def test_supported_kpis(self) -> None:
        assert FailureMode.meta.supported_kpis == ("MAINT.MTBF", "MAINT.MTTR", "MAINT.Ai")

    def test_empty_failure_mode_code_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            FailureMode(id="x", failure_mode_code="", system="hydraulic")

    def test_empty_system_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            FailureMode(id="x", failure_mode_code="HYD-001", system="")


class TestMaintenanceWorkOrder:
    def test_valid_construction(self) -> None:
        wo = MaintenanceWorkOrder(
            id="WO-1", equipment_id="HT-214", failure_mode_code="HYD-001", is_planned=False
        )
        assert wo.is_planned is False

    def test_defaults(self) -> None:
        wo = MaintenanceWorkOrder(id="WO-2", equipment_id="HT-214")
        assert wo.failure_mode_code is None
        assert wo.is_planned is False

    def test_empty_equipment_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            MaintenanceWorkOrder(id="x", equipment_id="")
