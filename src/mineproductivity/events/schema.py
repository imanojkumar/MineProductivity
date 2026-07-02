"""``EventSchema``: the machine-readable shape of one event type."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.events.exceptions import EventValidationError
from mineproductivity.events.versioning import EventVersion

__all__ = ["EventSchema"]

_JSON_SCHEMA_TYPES: Mapping[str, str] = {
    "str": "string",
    "float": "number",
    "int": "integer",
    "bool": "boolean",
    "datetime": "string",
}


@dataclasses.dataclass(frozen=True, slots=True)
class EventSchema(BaseValueObject):
    """The machine-readable shape of one event type -- used for
    validation, documentation generation, and JSON Schema export (parity
    with the ontology's ``to_schema()`` pattern).

    Examples
    --------
    >>> schema = EventSchema(
    ...     event_type_code="CYCLE",
    ...     version=EventVersion(),
    ...     required_fields=("payload_t",),
    ...     field_types={"payload_t": "float"},
    ...     invariants=("payload_t >= 0",),
    ... )
    >>> schema.to_json_schema()["required"]
    ['payload_t']
    """

    event_type_code: str
    version: EventVersion
    required_fields: tuple[str, ...]
    field_types: Mapping[str, str]
    invariants: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)

    def validate(self) -> None:
        if not self.event_type_code or not self.event_type_code.isupper():
            raise EventValidationError(
                "EventSchema.event_type_code must be a non-empty uppercase code"
            )
        missing = [f for f in self.required_fields if f not in self.field_types]
        if missing:
            raise EventValidationError(
                f"EventSchema.required_fields not typed in field_types: {missing}"
            )

    def to_json_schema(self) -> Mapping[str, Any]:
        """Export this schema as a (draft-2020-12-flavored) JSON Schema document."""
        properties = {
            name: {"type": _JSON_SCHEMA_TYPES.get(type_name, "string")}
            for name, type_name in self.field_types.items()
        }
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": self.event_type_code,
            "type": "object",
            "properties": properties,
            "required": list(self.required_fields),
        }
