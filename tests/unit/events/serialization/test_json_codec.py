"""Tests for mineproductivity.events.serialization.json_codec."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.core import SerializationError
from mineproductivity.events.canonical import (
    ConsumptionEvent,
    DelayEvent,
    MaintenanceEvent,
    ProductionEvent,
    ResourceType,
    SafetyEvent,
    SafetyEventType,
    SafetySeverity,
)
from mineproductivity.events.envelope import EventMetadata
from mineproductivity.events.serialization.json_codec import JSONEventCodec
from mineproductivity.ontology import DelayCategory

NOW = datetime(2026, 6, 25, 6, 0, tzinfo=timezone.utc)


class TestRoundTrip:
    def test_cycle_event_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        envelope = cycle_envelope_factory()
        restored = codec.deserialize(codec.serialize(envelope))
        assert restored == envelope

    def test_cycle_event_with_populated_optional_fields_round_trips(  # type: ignore[no-untyped-def]
        self, cycle_envelope_factory
    ) -> None:
        from mineproductivity.events.canonical import CycleEvent

        codec = JSONEventCodec()
        payload = CycleEvent(
            equipment_id="HT-214",
            shift_id="s",
            queue_min=1.5,
            spot_min=0.5,
            load_min=2.5,
            haul_min=8.0,
            dump_min=1.0,
            return_min=6.0,
            payload_t=220.0,
            route_id="B7N_CR1",
            operator_id="OP-001",
            material_type="Ore",
        )
        envelope = cycle_envelope_factory(payload=payload)
        restored = codec.deserialize(codec.serialize(envelope))
        assert restored == envelope
        assert restored.payload.route_id == "B7N_CR1"
        assert restored.payload.operator_id == "OP-001"

    def test_delay_event_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        payload = DelayEvent(
            equipment_id="CR-01",
            shift_id="s",
            delay_category=DelayCategory.STANDBY,
            delay_reason="no truck",
            duration_min=25.0,
        )
        envelope = cycle_envelope_factory(payload=payload)
        restored = codec.deserialize(codec.serialize(envelope))
        assert restored == envelope
        assert restored.payload.delay_category is DelayCategory.STANDBY

    def test_maintenance_event_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        payload = MaintenanceEvent(
            equipment_id="T-101",
            shift_id="s",
            failure_start_utc=NOW,
            return_to_service_utc=NOW + timedelta(hours=2),
            total_downtime_h=2.0,
            is_planned=True,
            failure_mode_code="TYR-003",
        )
        envelope = cycle_envelope_factory(payload=payload)
        restored = codec.deserialize(codec.serialize(envelope))
        assert restored == envelope
        assert restored.payload.failure_start_utc == NOW

    def test_production_event_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        payload = ProductionEvent(
            equipment_id="PIT-N",
            shift_id="s",
            pit_code="PIT-N",
            material_type="Waste",
            tonnes_moved=100.0,
            planned_tonnes=120.0,
            operating_h=10.0,
        )
        envelope = cycle_envelope_factory(payload=payload)
        restored = codec.deserialize(codec.serialize(envelope))
        assert restored == envelope

    def test_consumption_event_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        payload = ConsumptionEvent(
            equipment_id="T-101",
            shift_id="s",
            resource_type=ResourceType.POWER,
            quantity=500.0,
            unit="kWh",
        )
        envelope = cycle_envelope_factory(payload=payload)
        restored = codec.deserialize(codec.serialize(envelope))
        assert restored == envelope
        assert restored.payload.resource_type is ResourceType.POWER

    def test_safety_event_round_trips(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        payload = SafetyEvent(
            equipment_id="HT-1",
            shift_id="s",
            safety_event_type=SafetyEventType.FATIGUE,
            severity=SafetySeverity.HIGH,
        )
        envelope = cycle_envelope_factory(payload=payload)
        restored = codec.deserialize(codec.serialize(envelope))
        assert restored == envelope
        assert restored.payload.zone_id is None

    def test_metadata_with_tags_and_attributes_round_trips(self, cycle_event_factory) -> None:  # type: ignore[no-untyped-def]
        from mineproductivity.events.envelope import EventEnvelope
        from mineproductivity.events.identifier import EventID
        from mineproductivity.events.versioning import EventVersion

        codec = JSONEventCodec()
        envelope = EventEnvelope(
            event_id=EventID.generate(),
            version=EventVersion(),
            payload=cycle_event_factory(),
            event_time_utc=NOW,
            processing_time_utc=NOW,
            ingestion_time_utc=NOW,
            metadata=EventMetadata(
                name="tagged",
                tags=["a", "b"],  # type: ignore[arg-type]  # BaseMetadata._normalize() accepts any iterable
                attributes={"site": "bingham-west"},
                confidence=0.8,
            ),
        )
        restored = codec.deserialize(codec.serialize(envelope))
        assert restored.metadata.tags == frozenset({"a", "b"})
        assert restored.metadata.attributes == {"site": "bingham-west"}
        assert restored.metadata.confidence == 0.8


class TestSerializeShape:
    def test_serialized_payload_carries_event_type_code(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        data = codec.serialize(cycle_envelope_factory())
        assert data["payload"]["event_type_code"] == "CYCLE"

    def test_serialized_timestamps_are_iso_strings(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        data = codec.serialize(cycle_envelope_factory())
        assert isinstance(data["event_time_utc"], str)

    def test_serialized_result_is_json_dumpable(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        import json

        codec = JSONEventCodec()
        data = codec.serialize(cycle_envelope_factory())
        json.dumps(data)  # should not raise


class TestDeserializeErrors:
    def test_unknown_event_type_code_raises(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        codec = JSONEventCodec()
        data = codec.serialize(cycle_envelope_factory())
        data["payload"]["event_type_code"] = "NOT_A_REAL_TYPE"
        with pytest.raises(SerializationError):
            codec.deserialize(data)

    def test_missing_key_raises_serialization_error(self) -> None:
        codec = JSONEventCodec()
        with pytest.raises(SerializationError):
            codec.deserialize({"payload": {"event_type_code": "CYCLE"}})
