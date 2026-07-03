"""Tests for mineproductivity.connectors.normalization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from mineproductivity.core import ValidationError
from mineproductivity.events import CycleEvent, DelayEvent
from mineproductivity.ontology import DelayCategory

from mineproductivity.connectors.normalization import FieldMapper, Normalizer, ReasonCodeMap


class TestNormalizerAbstractContract:
    def test_cannot_instantiate_abstract_base(self) -> None:
        with pytest.raises(TypeError):
            Normalizer()  # type: ignore[abstract]

    def test_concrete_subclass_implements_both_methods(self) -> None:
        class _Passthrough(Normalizer):
            def normalize_cycle(self, raw: Mapping[str, Any]) -> CycleEvent:
                return CycleEvent(**raw)

            def normalize_delay(self, raw: Mapping[str, Any]) -> DelayEvent:
                return DelayEvent(**raw)

        instance = _Passthrough()
        cycle = instance.normalize_cycle(
            dict(
                equipment_id="HT-214",
                shift_id="A",
                queue_min=1.0,
                spot_min=0.5,
                load_min=2.0,
                haul_min=8.0,
                dump_min=1.0,
                return_min=6.0,
                payload_t=220.0,
            )
        )
        assert cycle.equipment_id == "HT-214"


class TestFieldMapper:
    def test_apply_renames_mapped_fields(self) -> None:
        mapper = FieldMapper(mapping={"TruckID": "equipment_id"})
        result = mapper.apply({"TruckID": "HT-214", "PayloadTonnes": 220.0})
        assert result == {"equipment_id": "HT-214", "PayloadTonnes": 220.0}

    def test_apply_leaves_unmapped_fields_unchanged(self) -> None:
        mapper = FieldMapper(mapping={})
        result = mapper.apply({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_mapping_is_frozen_defensive_copy(self) -> None:
        source = {"TruckID": "equipment_id"}
        mapper = FieldMapper(mapping=source)
        source["TruckID"] = "changed"
        assert mapper.mapping["TruckID"] == "equipment_id"

    def test_structural_equality(self) -> None:
        a = FieldMapper(mapping={"x": "y"})
        b = FieldMapper(mapping={"x": "y"})
        assert a == b


class TestReasonCodeMap:
    def test_valid_construction(self) -> None:
        rmap = ReasonCodeMap(
            vendor_name="acme", mapping={"X1": (DelayCategory.EQUIPMENT, "x1 reason")}
        )
        assert rmap.vendor_name == "acme"

    def test_empty_vendor_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ReasonCodeMap(vendor_name="", mapping={})

    def test_resolve_known_code(self) -> None:
        rmap = ReasonCodeMap(
            vendor_name="acme", mapping={"X1": (DelayCategory.EQUIPMENT, "x1 reason")}
        )
        resolved = rmap.resolve("X1")
        assert resolved.is_some
        category, reason = resolved.unwrap()
        assert category is DelayCategory.EQUIPMENT
        assert reason == "x1 reason"

    def test_resolve_unknown_code(self) -> None:
        rmap = ReasonCodeMap(vendor_name="acme", mapping={})
        assert rmap.resolve("UNKNOWN").is_nothing

    def test_mapping_is_frozen_defensive_copy(self) -> None:
        source = {"X1": (DelayCategory.EQUIPMENT, "x1 reason")}
        rmap = ReasonCodeMap(vendor_name="acme", mapping=source)
        source["X1"] = (DelayCategory.EXTERNAL, "changed")
        assert rmap.resolve("X1").unwrap()[0] is DelayCategory.EQUIPMENT
