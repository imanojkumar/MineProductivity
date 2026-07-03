"""Tests for mineproductivity.ontology.cost.cost_center."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.cost.cost_center import CostCategory, CostCenter
from mineproductivity.ontology.exceptions import OntologyValidationError


class TestCostCategory:
    def test_has_five_categories(self) -> None:
        assert len(list(CostCategory)) == 5

    def test_values(self) -> None:
        assert CostCategory.FUEL.value == "fuel"
        assert CostCategory.LABOUR.value == "labour"
        assert CostCategory.MAINTENANCE.value == "maintenance"
        assert CostCategory.CONSUMABLES.value == "consumables"
        assert CostCategory.OVERHEAD.value == "overhead"


class TestCostCenter:
    def test_valid_construction(self) -> None:
        cc = CostCenter(id="CC-FUEL-01", business_unit_id="bu-1", category=CostCategory.FUEL)
        assert cc.category is CostCategory.FUEL

    def test_supported_kpis(self) -> None:
        assert CostCenter.meta.supported_kpis == ("COST.CostPerTonne",)

    def test_empty_business_unit_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            CostCenter(id="x", business_unit_id="", category=CostCategory.FUEL)

    @pytest.mark.parametrize("category", list(CostCategory))
    def test_every_category_accepted(self, category: CostCategory) -> None:
        assert CostCenter(id="cc", business_unit_id="bu-1", category=category).category is category
