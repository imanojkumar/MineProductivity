"""Tests for mineproductivity.kpis.metadata."""

from __future__ import annotations

import pytest

from mineproductivity.core import ValidationError

from mineproductivity.kpis.exceptions import KPIValidationError
from mineproductivity.kpis.lifecycle import KPIStatus
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "code": "PROD.TPH",
        "name": "Tonnes Per Hour",
        "official_name": "Tonnes Per Hour",
        "business_purpose": "x",
        "operational_question": "x",
        "business_meaning": "x",
        "formula": "sum(payload_t) / sum(operating_h)",
        "unit": "t/h",
        "dimensions": ("Shift",),
        "required_events": ("CYCLE",),
        "aggregation": Aggregation.RATIO,
        "direction": Direction.HIGHER_IS_BETTER,
        "min_maturity": DigitalMaturity.L1_MANUAL,
        "leading_or_lagging": "lagging",
        "operational_or_strategic": "operational",
    }
    fields.update(overrides)
    return fields


class TestEnums:
    def test_direction_members(self) -> None:
        assert {member.value for member in Direction} == {
            "higher_is_better",
            "lower_is_better",
            "target_is_best",
        }

    def test_aggregation_members(self) -> None:
        assert {member.value for member in Aggregation} == {
            "additive",
            "ratio",
            "average",
            "weighted_average",
            "rolling",
            "cumulative",
            "derived",
        }

    def test_digital_maturity_members_are_ordered_ints(self) -> None:
        assert DigitalMaturity.L1_MANUAL.value == 1
        assert DigitalMaturity.L2_FMS.value == 2
        assert DigitalMaturity.L3_ANALYTICS.value == 3
        assert DigitalMaturity.L4_AUTONOMOUS.value == 4


class TestKPIMetadataConstruction:
    def test_minimal_valid_construction(self) -> None:
        meta = KPIMetadata(**_valid_kwargs())
        assert meta.code == "PROD.TPH"
        assert meta.status is KPIStatus.PROPOSED
        assert meta.version == "1.0.0"
        assert meta.deprecated_successor is None

    def test_benchmark_bands_is_frozen_into_a_read_only_mapping(self) -> None:
        meta = KPIMetadata(**_valid_kwargs(benchmark_bands={"good": ">0.9"}))
        assert meta.benchmark_bands["good"] == ">0.9"
        with pytest.raises(TypeError):
            meta.benchmark_bands["bad"] = "x"  # type: ignore[index]

    def test_default_method_applicability_is_open_pit_and_underground(self) -> None:
        meta = KPIMetadata(**_valid_kwargs())
        assert meta.method_applicability == ("open_pit", "underground")

    def test_code_is_a_required_positional_field(self) -> None:
        with pytest.raises(TypeError):
            KPIMetadata(name="X")  # type: ignore[call-arg]


class TestKPIMetadataValidate:
    def test_valid_metadata_passes(self) -> None:
        KPIMetadata(**_valid_kwargs())  # must not raise

    def test_malformed_code_raises(self) -> None:
        with pytest.raises(KPIValidationError):
            KPIMetadata(**_valid_kwargs(code="not-a-code"))

    def test_unrecognized_namespace_raises(self) -> None:
        with pytest.raises(KPIValidationError):
            KPIMetadata(**_valid_kwargs(code="NOTREAL.Thing"))

    @pytest.mark.parametrize(
        "field_name",
        [
            "official_name",
            "business_purpose",
            "operational_question",
            "business_meaning",
            "formula",
            "unit",
        ],
    )
    def test_blank_documentation_field_raises(self, field_name: str) -> None:
        with pytest.raises(KPIValidationError, match=field_name):
            KPIMetadata(**_valid_kwargs(**{field_name: "   "}))

    def test_empty_dimensions_raises(self) -> None:
        with pytest.raises(KPIValidationError, match="dimensions"):
            KPIMetadata(**_valid_kwargs(dimensions=()))

    def test_empty_required_events_raises(self) -> None:
        with pytest.raises(KPIValidationError, match="required_events"):
            KPIMetadata(**_valid_kwargs(required_events=()))

    def test_base_metadata_empty_name_still_enforced(self) -> None:
        """``KPIMetadata.validate()`` calls ``super().validate()`` first,
        so a blank ``name`` is rejected by ``BaseMetadata`` itself, as a
        plain ``core.ValidationError`` -- not the ``KPIValidationError``
        subclass raised by the KPI-specific checks further down."""
        with pytest.raises(ValidationError):
            KPIMetadata(**_valid_kwargs(name=""))


class TestKPIMetadataReplace:
    def test_replace_reruns_normalize_and_validate(self) -> None:
        meta = KPIMetadata(**_valid_kwargs())
        replaced = meta.replace(code="PROD.TPH.Ore")
        assert replaced.code == "PROD.TPH.Ore"
        assert replaced.formula == meta.formula

    def test_replace_with_invalid_code_raises(self) -> None:
        meta = KPIMetadata(**_valid_kwargs())
        with pytest.raises(KPIValidationError):
            meta.replace(code="not-a-code")
