"""Tests for mineproductivity.kpis.inheritance."""

from __future__ import annotations

from mineproductivity.kpis.inheritance import specialize
from mineproductivity.kpis.standard_library.production import TonnesPerHour


class TestSpecialize:
    def test_returns_a_genuine_subclass_of_the_parent(self) -> None:
        ore_cls = specialize(TonnesPerHour, code="PROD.TPH.OreFixture", material_filter="ore")
        assert issubclass(ore_cls, TonnesPerHour)

    def test_specialized_class_has_its_own_code(self) -> None:
        ore_cls = specialize(TonnesPerHour, code="PROD.TPH.OreFixture", material_filter="ore")
        assert ore_cls.meta.code == "PROD.TPH.OreFixture"
        assert TonnesPerHour.meta.code == "PROD.TPH"  # parent untouched

    def test_default_official_name_mentions_the_material_filter(self) -> None:
        ore_cls = specialize(TonnesPerHour, code="PROD.TPH.OreFixture", material_filter="ore")
        assert "ore" in ore_cls.meta.official_name

    def test_explicit_official_name_overrides_the_default(self) -> None:
        ore_cls = specialize(
            TonnesPerHour,
            code="PROD.TPH.OreFixture",
            material_filter="ore",
            official_name="Ore TPH",
        )
        assert ore_cls.meta.official_name == "Ore TPH"

    def test_class_name_derived_from_the_code(self) -> None:
        ore_cls = specialize(TonnesPerHour, code="PROD.TPH.OreFixture", material_filter="ore")
        assert ore_cls.__name__ == "PROD_TPH_OreFixture"

    def test_prefilters_rows_by_material_type_before_delegating(self) -> None:
        ore_cls = specialize(TonnesPerHour, code="PROD.TPH.OreFixture", material_filter="ore")
        rows = [
            {"payload_t": 100.0, "operating_h": 1.0, "material_type": "ore"},
            {"payload_t": 999.0, "operating_h": 1.0, "material_type": "waste"},
        ]
        result = ore_cls().compute(rows)
        assert result.value == 100.0

    def test_rows_missing_material_type_are_excluded(self) -> None:
        ore_cls = specialize(TonnesPerHour, code="PROD.TPH.OreFixture", material_filter="ore")
        result = ore_cls().compute([{"payload_t": 100.0, "operating_h": 1.0}])
        assert result.value is None  # zero rows matched -> zero hours -> None

    def test_waste_specialization_is_independent_of_ore(self) -> None:
        waste_cls = specialize(TonnesPerHour, code="PROD.TPH.WasteFixture", material_filter="waste")
        rows = [
            {"payload_t": 100.0, "operating_h": 1.0, "material_type": "ore"},
            {"payload_t": 50.0, "operating_h": 1.0, "material_type": "waste"},
        ]
        result = waste_cls().compute(rows)
        assert result.value == 50.0
