"""``JSONEventCodec``: converts an :class:`EventEnvelope` to and from a plain, JSON-safe mapping."""

from __future__ import annotations

import dataclasses
import types
import typing
from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Any

from mineproductivity.core import BaseSerializer, SerializationError

from mineproductivity.events.canonical import canonical_event_types
from mineproductivity.events.envelope import EventEnvelope, EventMetadata
from mineproductivity.events.identifier import EventID
from mineproductivity.events.versioning import EventVersion

__all__ = ["JSONEventCodec"]


def _value_to_json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, frozenset):
        return sorted(value)
    if isinstance(value, Mapping):
        return {key: _value_to_json_safe(item) for key, item in value.items()}
    return value


def _fields_to_json_safe(obj: Any) -> dict[str, Any]:
    return {f.name: _value_to_json_safe(getattr(obj, f.name)) for f in dataclasses.fields(obj)}


def _convert_value(field_type: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = typing.get_origin(field_type)
    if origin in (types.UnionType, typing.Union):
        non_none = [arg for arg in typing.get_args(field_type) if arg is not type(None)]
        field_type = non_none[0] if non_none else field_type
    if isinstance(field_type, type) and issubclass(field_type, Enum):
        return field_type(value)
    if field_type is datetime:
        return datetime.fromisoformat(value)
    return value


def _reconstruct_dataclass(cls: type, data: Mapping[str, Any]) -> Any:
    hints = typing.get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for f in dataclasses.fields(cls):
        if f.name not in data:
            continue
        kwargs[f.name] = _convert_value(hints.get(f.name), data[f.name])
    return cls(**kwargs)


class JSONEventCodec(BaseSerializer[EventEnvelope[Any]]):
    """Converts an :class:`~mineproductivity.events.envelope.EventEnvelope`
    to and from a plain, JSON-safe :class:`Mapping`.

    Handles every canonical event type's ``Enum`` and ``datetime`` fields
    correctly (round-trips them, rather than leaving raw Python objects
    that ``json.dumps`` would reject).

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> from mineproductivity.events.canonical import CycleEvent
    >>> now = datetime(2026, 6, 25, 6, tzinfo=timezone.utc)
    >>> envelope = EventEnvelope(
    ...     event_id=EventID.generate(), version=EventVersion(),
    ...     payload=CycleEvent(
    ...         equipment_id="HT-214", shift_id="A-2026-06-25",
    ...         queue_min=1.5, spot_min=0.5, load_min=2.5,
    ...         haul_min=8.0, dump_min=1.0, return_min=6.0, payload_t=220.0,
    ...     ),
    ...     event_time_utc=now, processing_time_utc=now, ingestion_time_utc=now,
    ... )
    >>> codec = JSONEventCodec()
    >>> data = codec.serialize(envelope)
    >>> restored = codec.deserialize(data)
    >>> restored.payload.payload_t
    220.0
    """

    def serialize(self, obj: EventEnvelope[Any]) -> dict[str, Any]:
        payload_dict = _fields_to_json_safe(obj.payload)
        payload_dict["event_type_code"] = obj.payload.event_type_code
        return {
            "event_id": obj.event_id.value,
            "version": obj.version.version,
            "payload": payload_dict,
            "event_time_utc": obj.event_time_utc.isoformat(),
            "processing_time_utc": obj.processing_time_utc.isoformat(),
            "ingestion_time_utc": obj.ingestion_time_utc.isoformat(),
            "metadata": _fields_to_json_safe(obj.metadata),
        }

    def deserialize(self, data: Mapping[str, Any]) -> EventEnvelope[Any]:
        try:
            payload_data = dict(data["payload"])
            event_type_code = payload_data.pop("event_type_code")
            event_cls = canonical_event_types().get(event_type_code)
            if event_cls is None:
                raise SerializationError(f"unknown event_type_code {event_type_code!r}")
            payload = _reconstruct_dataclass(event_cls, payload_data)
            metadata = _reconstruct_dataclass(EventMetadata, dict(data["metadata"]))
            return EventEnvelope(
                event_id=EventID(value=data["event_id"]),
                version=EventVersion(version=data["version"]),
                payload=payload,
                event_time_utc=datetime.fromisoformat(data["event_time_utc"]),
                processing_time_utc=datetime.fromisoformat(data["processing_time_utc"]),
                ingestion_time_utc=datetime.fromisoformat(data["ingestion_time_utc"]),
                metadata=metadata,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SerializationError(
                f"could not deserialize EventEnvelope from {data!r}: {exc}"
            ) from exc
