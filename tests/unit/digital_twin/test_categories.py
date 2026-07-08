"""Tests for mineproductivity.digital_twin.categories."""

from __future__ import annotations

from abc import ABC
from typing import Any

import pytest

from mineproductivity.digital_twin.abstractions import Twin, TwinContext
from mineproductivity.digital_twin.categories import (
    ConveyorTwin,
    EquipmentTwin,
    FleetTwin,
    GeologicalTwin,
    HaulageTwin,
    MineTwin,
    PlantTwin,
    ProcessingPlantTwin,
    ProductionTwin,
    StockpileTwin,
    VentilationTwin,
)
from mineproductivity.digital_twin.exceptions import TwinValidationError
from mineproductivity.digital_twin.metadata import TwinCategory, TwinMetadata
from mineproductivity.digital_twin.state import TwinState

_BASES = (
    (MineTwin, "MINE", TwinCategory.MINE),
    (EquipmentTwin, "EQUIPMENT", TwinCategory.EQUIPMENT),
    (PlantTwin, "PLANT", TwinCategory.PLANT),
    (ConveyorTwin, "CONVEYOR", TwinCategory.CONVEYOR),
    (HaulageTwin, "HAULAGE", TwinCategory.HAULAGE),
    (FleetTwin, "FLEET", TwinCategory.FLEET),
    (ProcessingPlantTwin, "PROCESSING_PLANT", TwinCategory.PROCESSING_PLANT),
    (GeologicalTwin, "GEOLOGICAL", TwinCategory.GEOLOGICAL),
    (VentilationTwin, "VENTILATION", TwinCategory.VENTILATION),
    (StockpileTwin, "STOCKPILE", TwinCategory.STOCKPILE),
    (ProductionTwin, "PRODUCTION", TwinCategory.PRODUCTION),
)


def _apply_stub(self: Twin, events: Any, *, context: TwinContext) -> TwinState:
    return self.state


def _leaf(base: type[Twin], code: str, category: TwinCategory) -> type[Twin]:
    """Dynamically define a concrete leaf twin type under ``base`` --
    the class-creation moment is exactly when the category base's
    ``__init_subclass__`` conformance check fires."""
    return type(
        "_LeafTwin",
        (base,),
        {
            "meta": TwinMetadata(code=code, category=category, description="x"),
            "_apply": _apply_stub,
        },
    )


class TestElevenCategoryBases:
    @pytest.mark.parametrize(("base", "namespace", "category"), _BASES)
    def test_each_base_is_an_abstract_twin_subclass(
        self, base: type[Twin], namespace: str, category: TwinCategory
    ) -> None:
        assert issubclass(base, Twin)
        assert issubclass(base, ABC)

    @pytest.mark.parametrize(("base", "namespace", "category"), _BASES)
    def test_bases_contribute_no_behavior_beyond_the_convention_check(
        self, base: type[Twin], namespace: str, category: TwinCategory
    ) -> None:
        """Design spec §9: identical in spirit to ``kpis``' nine
        category bases -- no fields, no methods, only the
        ``__init_subclass__`` conformance hook and a docstring."""
        members = {
            name for name in vars(base) if not (name.startswith("__") or name.startswith("_abc"))
        }
        assert members == set()
        assert "__init_subclass__" in vars(base)

    @pytest.mark.parametrize(("base", "namespace", "category"), _BASES)
    def test_conforming_leaf_definition_succeeds(
        self, base: type[Twin], namespace: str, category: TwinCategory
    ) -> None:
        leaf = _leaf(base, f"{namespace}.TestLeaf", category)
        assert leaf.meta.code == f"{namespace}.TestLeaf"

    @pytest.mark.parametrize(("base", "namespace", "category"), _BASES)
    def test_bare_namespace_code_is_also_accepted(
        self, base: type[Twin], namespace: str, category: TwinCategory
    ) -> None:
        assert _leaf(base, namespace, category).meta.code == namespace


class TestNamespaceConformance:
    def test_wrong_namespace_fails_at_class_definition_time(self) -> None:
        with pytest.raises(TwinValidationError, match="must fall in the 'CONVEYOR' namespace"):
            _leaf(ConveyorTwin, "STOCKPILE.Wrong", TwinCategory.CONVEYOR)

    def test_prefix_must_be_a_whole_namespace_segment(self) -> None:
        """``PLANT.x`` belongs to ``PlantTwin``, and a code like
        ``PLANTATION.x`` must not sneak into the ``PLANT`` namespace."""
        with pytest.raises(TwinValidationError, match="must fall in the 'PLANT' namespace"):
            _leaf(PlantTwin, "PLANTATION.Wrong", TwinCategory.PLANT)

    def test_wrong_category_member_fails_at_class_definition_time(self) -> None:
        with pytest.raises(TwinValidationError, match="meta.category must be"):
            _leaf(ConveyorTwin, "CONVEYOR.Wrong", TwinCategory.STOCKPILE)

    def test_abstract_intermediate_without_its_own_meta_is_skipped(self) -> None:
        class _StillAbstract(ConveyorTwin, ABC):  # declares no meta of its own
            """An abstract intermediate refinement."""

        assert issubclass(_StillAbstract, ConveyorTwin)

    def test_the_check_reaches_grandchildren_that_declare_meta(self) -> None:
        class _StillAbstract(ConveyorTwin, ABC):
            """An abstract intermediate refinement."""

        with pytest.raises(TwinValidationError):
            _leaf(_StillAbstract, "WRONG.Namespace", TwinCategory.CONVEYOR)
