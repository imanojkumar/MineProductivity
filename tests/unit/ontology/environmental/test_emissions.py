"""Tests for mineproductivity.ontology.environmental.emissions."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.environmental.emissions import EmissionFactor, MonitoringPoint
from mineproductivity.ontology.exceptions import OntologyValidationError


class TestEmissionFactor:
    def test_valid_construction(self) -> None:
        factor = EmissionFactor(id="diesel-factor", resource_type="diesel", kg_co2e_per_unit=2.68)
        assert factor.kg_co2e_per_unit == 2.68

    def test_supported_kpis(self) -> None:
        assert EmissionFactor.meta.supported_kpis == ("CARBON.CO2PerTonne",)

    def test_empty_resource_type_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            EmissionFactor(id="x", resource_type="", kg_co2e_per_unit=1.0)

    def test_negative_factor_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            EmissionFactor(id="x", resource_type="diesel", kg_co2e_per_unit=-1.0)


class TestMonitoringPoint:
    def test_valid_construction(self) -> None:
        point = MonitoringPoint(id="MP-1", mine_id="bingham-west", measurement_type="dust")
        assert point.measurement_type == "dust"

    def test_empty_measurement_type_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            MonitoringPoint(id="x", mine_id="bingham-west", measurement_type="")
