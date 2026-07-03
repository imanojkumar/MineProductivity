"""Tests for mineproductivity.ontology.material.material_type."""

from __future__ import annotations

from mineproductivity.ontology.material.material_type import MaterialType


class TestMaterialType:
    def test_has_three_classifications(self) -> None:
        assert len(list(MaterialType)) == 3

    def test_values(self) -> None:
        assert MaterialType.ORE.value == "ore"
        assert MaterialType.WASTE.value == "waste"
        assert MaterialType.PRODUCT.value == "product"
