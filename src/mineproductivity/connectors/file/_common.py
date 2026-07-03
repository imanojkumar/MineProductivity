"""Shared row-normalization and time-parsing logic for file-based
reference connectors (:class:`~mineproductivity.connectors.file.csv_connector.CSVConnector`,
:class:`~mineproductivity.connectors.file.excel_connector.ExcelConnector`)
-- both read the identical row shape, so the translation logic is
written once here rather than duplicated per file format.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from mineproductivity.events import CycleEvent, DelayEvent
from mineproductivity.ontology import DelayCategory

from mineproductivity.connectors.exceptions import MappingError
from mineproductivity.connectors.normalization import FieldMapper, Normalizer

__all__ = ["FileRowNormalizer", "parse_source_datetime"]

_CYCLE_FLOAT_FIELDS = (
    "queue_min",
    "spot_min",
    "load_min",
    "haul_min",
    "dump_min",
    "return_min",
    "payload_t",
)


class FileRowNormalizer(Normalizer):
    """Normalizes a raw, string-keyed row (as produced by
    :class:`csv.DictReader` or an ``openpyxl`` sheet scan) into a
    canonical :class:`CycleEvent`/:class:`DelayEvent`.

    The reference file connectors' own CSV/Excel schema already encodes
    :class:`~mineproductivity.ontology.DelayCategory` values by name
    directly (``EQUIPMENT``, ``OPERATIONAL``, ...) -- no vendor
    reason-code translation happens here; that is what
    :class:`~mineproductivity.connectors.normalization.ReasonCodeMap` and
    the ``oem/`` connector shapes are for.
    """

    def __init__(self, *, field_mapper: FieldMapper | None = None) -> None:
        self._field_mapper = field_mapper

    def _apply_mapper(self, raw: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._field_mapper.apply(raw) if self._field_mapper is not None else raw

    def normalize_cycle(self, raw: Mapping[str, Any]) -> CycleEvent:
        row = self._apply_mapper(raw)
        try:
            equipment_id = str(row["equipment_id"])
            shift_id = str(row["shift_id"])
            floats = {field: float(row[field]) for field in _CYCLE_FLOAT_FIELDS}
        except KeyError as exc:
            raise MappingError(f"cycle row missing required field {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise MappingError(f"cycle row has a non-numeric value: {exc}") from exc

        route_id = row.get("route_id") or None
        operator_id = row.get("operator_id") or None
        material_type = row.get("material_type") or "unspecified"

        try:
            return CycleEvent(
                equipment_id=equipment_id,
                shift_id=shift_id,
                material_type=str(material_type),
                route_id=str(route_id) if route_id is not None else None,
                operator_id=str(operator_id) if operator_id is not None else None,
                **floats,
            )
        except Exception as exc:
            raise MappingError(f"cycle row failed event validation: {exc}") from exc

    def normalize_delay(self, raw: Mapping[str, Any]) -> DelayEvent:
        row = self._apply_mapper(raw)
        try:
            equipment_id = str(row["equipment_id"])
            shift_id = str(row["shift_id"])
            duration_min = float(row["duration_min"])
            delay_reason = str(row["delay_reason"])
            category_name = str(row["delay_category"])
        except KeyError as exc:
            raise MappingError(f"delay row missing required field {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise MappingError(f"delay row has a non-numeric value: {exc}") from exc

        try:
            delay_category = DelayCategory[category_name.strip().upper()]
        except KeyError as exc:
            raise MappingError(
                f"delay row has an unrecognized delay_category {category_name!r}"
            ) from exc

        try:
            return DelayEvent(
                equipment_id=equipment_id,
                shift_id=shift_id,
                delay_category=delay_category,
                delay_reason=delay_reason,
                duration_min=duration_min,
            )
        except Exception as exc:
            raise MappingError(f"delay row failed event validation: {exc}") from exc


def parse_source_datetime(raw: str, *, source_timezone: str) -> datetime:
    """Parse an ISO-8601 datetime string. A naive string is interpreted
    as local time in ``source_timezone`` and converted to the equivalent
    aware UTC datetime; an already-aware string is converted to UTC
    directly (design spec §30 Category F: local, non-UTC timestamps must
    be correctly normalized)."""
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise MappingError(f"unparseable event_time {raw!r}: {exc}") from exc
    if parsed.tzinfo is not None:
        return parsed.astimezone(ZoneInfo("UTC"))
    localized = parsed.replace(tzinfo=ZoneInfo(source_timezone))
    return localized.astimezone(ZoneInfo("UTC"))
